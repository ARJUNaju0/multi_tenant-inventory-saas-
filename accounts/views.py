from datetime import timedelta
from django.contrib.auth import get_user_model

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

from .audit import log_action
from .serializers import (CompanyRegistrationSerializer,CustomTokenObtainPairSerializer, UserCreateSerializer,UserSerializer,UserProfileSerializer,InvitationSerializer,InvitationAcceptSerializer, AuditLogSerializer)
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from rest_framework.views import APIView
from .models import AuditLog, Invitation ,Role
from .permissions import IsAdminRole, IsTenantUser , IsAdminRole    

from django.core.mail import send_mail
from django.db import transaction
from django.conf import settings
from django.utils import timezone


from django.db import transaction

from notifications.models import Notification
from notifications.services import create_notification





User = get_user_model()


class CompanyRegistrationView(generics.CreateAPIView):
    """
    Creates a new company and its first Admin user.
    """

    serializer_class = CompanyRegistrationSerializer

    permission_classes = [AllowAny]


class UserCreateView(generics.CreateAPIView):
    """
    Creates a new user for the authenticated admin's company.
    """

    serializer_class = UserCreateSerializer
    permission_classes = [IsAuthenticated, IsTenantUser, IsAdminRole]

    def get_queryset(self):
        return User.objects.filter(
            company=self.request.user.company
        )

    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.company
        )


class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    Returns and updates the currently authenticated user's information.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Authenticates a user using email and password.

    Returns access and refresh JWT tokens.
    """

    serializer_class = CustomTokenObtainPairSerializer


class CurrentUserView(generics.RetrieveAPIView):
    """
    Returns the currently authenticated user's profile.
    """

    serializer_class = UserProfileSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    def get_object(self):
        return self.request.user


class UserManagementViewSet(ModelViewSet):
    """
    Admin-only user management.

    IMPORTANT:
    Every query is restricted to the authenticated
    user's company.
    """

    permission_classes = [IsAuthenticated,IsAdminRole,]
    
    def get_queryset(self):
        return User.objects.filter(
            company=self.request.user.company
        ).order_by("email")

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer

        return UserSerializer

    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.company
        )


class LogoutView(generics.GenericAPIView):
    """
    Blacklist the supplied refresh token.

    POST /api/v1/accounts/logout/
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):

        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {
                    "detail": "Refresh token is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

        except Exception:
            return Response(
                {
                    "detail": "Invalid or expired refresh token."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Logged out successfully."
            },
            status=status.HTTP_205_RESET_CONTENT,
        )
    


# ============================================================
# INVITATION CREATE + LIST
# ============================================================

class InvitationCreateView(APIView):
    """
    Company administrator can:

    GET:
        View invitations belonging to their company.

    POST:
        Invite a MANAGER or STAFF user.

    GET
        /api/v1/accounts/invitations/

    POST
        /api/v1/accounts/invitations/
    """

    permission_classes = [
        IsAuthenticated,
        IsTenantUser,
        IsAdminRole,
    ]

    # --------------------------------------------------------
    # GET INVITATIONS
    # --------------------------------------------------------

    def get(self, request):

        invitations = (
            Invitation.objects
            .filter(company=request.user.company)
            .select_related("invited_by", "company")
            .order_by("-created_at")
        )

        serializer = InvitationSerializer(
            invitations,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    # --------------------------------------------------------
    # CREATE INVITATION
    # --------------------------------------------------------

    def post(self, request):

        # ----------------------------------------------------
        # Get and normalize input
        # ----------------------------------------------------

        email = request.data.get("email")
        role = request.data.get("role")

        if not email:
            return Response(
                {
                    "email": "Email is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = email.strip().lower()

        if not role:
            return Response(
                {
                    "role": "Role is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        role = role.upper()

        # ----------------------------------------------------
        # Validate role
        # ----------------------------------------------------

        if role not in [
            Role.MANAGER,
            Role.STAFF,
        ]:
            return Response(
                {
                    "role": "Only Manager or Staff roles can be invited."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Prevent existing account from being invited
        # ----------------------------------------------------

        if User.objects.filter(
            email__iexact=email
        ).exists():

            return Response(
                {
                    "email": "An account with this email already exists."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Prevent duplicate active invitation
        # ----------------------------------------------------

        existing_invitation = (
            Invitation.objects
            .filter(
                company=request.user.company,
                email__iexact=email,
                accepted_at__isnull=True,
                expires_at__gt=timezone.now(),
            )
            .first()
        )

        if existing_invitation:

            return Response(
                {
                    "email": "A pending invitation already exists for this email."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Create invitation
        # ----------------------------------------------------

        invitation = Invitation.objects.create(
            company=request.user.company,
            email=email,
            role=role,
            invited_by=request.user,
            expires_at=timezone.now() + timedelta(
                minutes=10
            ),
        )

        # ----------------------------------------------------
        # Build frontend invitation URL
        # ----------------------------------------------------

        frontend_url = getattr(
            settings,
            "FRONTEND_URL",
            "http://localhost:3000",
        ).rstrip("/")

        invitation_link = (
            f"{frontend_url}/invitations/accept/"
            f"{invitation.token}/"
        )

        # ----------------------------------------------------
        # Send email
        # ----------------------------------------------------

        send_mail(
            subject=(
                f"Invitation to join "
                f"{request.user.company.name}"
            ),
            message=(
                f"Hello,\n\n"
                f"You have been invited to join "
                f"{request.user.company.name} "
                f"as a {invitation.role}.\n\n"
                f"Please use the following link to "
                f"accept the invitation:\n\n"
                f"{invitation_link}\n\n"
                f"This invitation expires in 10 minutes.\n\n"
                f"If you did not expect this invitation, "
                f"you can safely ignore this email.\n\n"
                f"Regards,\n"
                f"{request.user.company.name}"
            ),
            from_email=getattr(
                settings,
                "DEFAULT_FROM_EMAIL",
                "noreply@stockmanagement.local",
            ),
            recipient_list=[
                invitation.email
            ],
            fail_silently=False,
        )

        # ----------------------------------------------------
        # Audit log
        # ----------------------------------------------------

        log_action(
            company=request.user.company,
            user=request.user,
            action="INVITATION_CREATED",
            entity="Invitation",
            object_id=invitation.id,
            changes={
                "email": invitation.email,
                "role": invitation.role,
            },
)

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return Response(
            {
                "message": "Invitation sent successfully.",
                "email": invitation.email,
                "role": invitation.role,
                "expires_at": invitation.expires_at,
                "invitation_link": invitation_link,
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# INVITATION ACCEPTANCE
# ============================================================

class InvitationAcceptView(APIView):
    """
    Public invitation acceptance endpoint.

    GET:
        Validate invitation and return basic information.

    POST:
        Create the invited user and mark invitation as accepted.

    GET
        /api/v1/accounts/invitations/accept/<token>/

    POST
        /api/v1/accounts/invitations/accept/<token>/
    """

    permission_classes = [
        AllowAny,
    ]

    # --------------------------------------------------------
    # GET INVITATION
    # --------------------------------------------------------

    def get_invitation(self, token, lock=False):

        queryset = (
            Invitation.objects
            .select_related("company")
        )

        if lock:
            queryset = queryset.select_for_update()

        try:
            return queryset.get(
                token=token
            )

        except Invitation.DoesNotExist:
            return None

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    def get(self, request, token):

        invitation = self.get_invitation(
            token
        )

        if not invitation:
            return Response(
                {
                    "detail": "Invalid invitation."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if invitation.accepted_at:
            return Response(
                {
                    "detail": "This invitation has already been accepted."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invitation.expires_at <= timezone.now():
            return Response(
                {
                    "detail": "This invitation has expired."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "email": invitation.email,
                "company_name": invitation.company.name,
                "role": invitation.role,
                "expires_at": invitation.expires_at,
            },
            status=status.HTTP_200_OK,
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    @transaction.atomic
    def post(self, request, token):

        # Lock the invitation row.
        #
        # This prevents two simultaneous requests from
        # accepting the same invitation.
        invitation = self.get_invitation(
            token,
            lock=True,
        )

        if not invitation:
            return Response(
                {
                    "detail": "Invalid invitation."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ----------------------------------------------------
        # Check accepted
        # ----------------------------------------------------

        if invitation.accepted_at:

            return Response(
                {
                    "detail": "This invitation has already been accepted."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Check expiration
        # ----------------------------------------------------

        if invitation.expires_at <= timezone.now():

            return Response(
                {
                    "detail": "This invitation has expired."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Check email
        # ----------------------------------------------------

        if User.objects.filter(
            email__iexact=invitation.email
        ).exists():

            return Response(
                {
                    "detail": "An account with this email already exists."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Validate acceptance form
        # ----------------------------------------------------

        serializer = InvitationAcceptSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        # ----------------------------------------------------
        # Create user
        # ----------------------------------------------------

        user = User(
            email=invitation.email,
            first_name=serializer.validated_data[
                "first_name"
            ],
            last_name=serializer.validated_data.get(
                "last_name",
                "",
            ),
            company=invitation.company,
            role=invitation.role,
            is_active=True,
        )

        user.set_password(
            serializer.validated_data["password"]
        )

        user.save()

        # ----------------------------------------------------
        # Mark invitation as accepted
        # ----------------------------------------------------

        invitation.accepted_at = timezone.now()

        invitation.save(
            update_fields=[
                "accepted_at"
            ]
        )

        # ----------------------------------------------------
        # Audit log
        # ----------------------------------------------------

        log_action(
            company=invitation.company,
            user=user,
            action="INVITATION_ACCEPTED",
            entity="Invitation",
            object_id=invitation.id,
            changes={
                "email": user.email,
                "role": user.role,
            },
        )


    
# ----------------------------------------------------
# Notify the admin who sent the invitation
# ----------------------------------------------------

        admin = invitation.invited_by

        if admin and admin.is_active:
            transaction.on_commit(
                lambda: create_notification(
                    company=invitation.company,
                    recipient=admin,
                    actor=user,
                    title="Invitation accepted",
                    message=(
                        f"{user.email} accepted your invitation "
                        f"and joined {invitation.company.name}."
                    ),
                    notification_type=(
                        Notification.Type.INVITATION_ACCEPTED
                    ),
                    priority=Notification.Priority.NORMAL,
                    target_url="/users",
                ),
                robust=True,
            )



            # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return Response(
            {
                "message": "Invitation accepted successfully.",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "company_name": invitation.company.name,
                },
            },
            status=status.HTTP_201_CREATED,
        )


        
    # Call this after the invitation has been successfully accepted.
    def notify_invitation_accepted(invitation, new_user):
        admin = invitation.invited_by

        if not admin or not admin.is_active:
            return

        transaction.on_commit(
            lambda: create_notification(
                company=invitation.company,
                recipient=admin,
                actor=new_user,
                title="Invitation accepted",
                message=(
                    f"{new_user.email} accepted your invitation "
                    "and joined your company."
                ),
                notification_type=(
                    Notification.Type.INVITATION_ACCEPTED
                ),
                priority=Notification.Priority.NORMAL,
                target_url="/users",
            )
        )






# ============================================================
# ACTIVITY / AUDIT LOG
# ============================================================

class AuditLogListView(generics.ListAPIView):
    """
    Company administrators can view company activity.

    GET /api/v1/accounts/activity/
    """

    serializer_class = AuditLogSerializer

    permission_classes = [
        IsAuthenticated,
        IsTenantUser,
        IsAdminRole,
    ]

    def get_queryset(self):

        return (
            AuditLog.objects
            .filter(
                company=self.request.user.company
            )
            .select_related("user")
            .order_by(
                "-created_at",
                "-id",
            )
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update the currently authenticated user's profile.

    GET   /api/v1/accounts/profile/
    PATCH /api/v1/accounts/profile/
    PUT   /api/v1/accounts/profile/
    """

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    

class ActivityLogView(generics.ListAPIView):
    """
    Company administrators can view company activity.

    GET /api/v1/accounts/activity/
    """

    serializer_class = AuditLogSerializer

    permission_classes = [
        IsAuthenticated,
        IsTenantUser,
        IsAdminRole,
    ]

    def get_queryset(self):

        return (
            AuditLog.objects
            .filter(
                company=self.request.user.company
            )
            .select_related("user")
            .order_by(
                "-created_at",
                "-id",
            )
        )
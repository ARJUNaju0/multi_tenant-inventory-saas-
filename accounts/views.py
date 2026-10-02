from datetime import timedelta
from django.contrib.auth import get_user_model

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import (CompanyRegistrationSerializer,CustomTokenObtainPairSerializer, UserCreateSerializer,UserSerializer,UserProfileSerializer)
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from rest_framework.views import APIView
from .models import Invitation
from .permissions import IsAdminRole, IsTenantUser , IsAdminRole    




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
    Logs out the currently authenticated user by blacklisting their refresh token.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class InvitationCreateView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsTenantUser,
    ]

    def post(self, request):

        if request.user.role != "ADMIN":
            return Response(
                {"detail": "Only administrators can invite users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        email = request.data.get("email")
        role = request.data.get("role")

        if not email:
            return Response(
                {"email": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if role not in ["MANAGER", "STAFF"]:
            return Response(
                {"role": "Invalid role."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invitation = Invitation.objects.create(
            company=request.user.company,
            email=email,
            role=role,
            invited_by=request.user,
            expires_at=timezone.now() + timedelta(days=7),
        )

        return Response(
            {
                "message": "Invitation created successfully.",
                "token": str(invitation.token),
                "email": invitation.email,
                "role": invitation.role,
            },
            status=status.HTTP_201_CREATED,
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
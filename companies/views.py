from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdmin
from .serializers import CompanySerializer
from accounts.models import User, Invitation
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsTenantUser
from accounts.models import Role



class MyCompanyView(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [
                permissions.IsAuthenticated(),
            ]

        return [
            permissions.IsAuthenticated(),
            IsAdmin(),
        ]

    def get(self, request):
        company = request.user.company

        serializer = CompanySerializer(company)

        return Response(serializer.data)

    def patch(self, request):
        company = request.user.company

        serializer = CompanySerializer(
            company,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

class DashboardView(APIView):
    """
    Company dashboard.

    Returns dashboard information for the authenticated
    tenant user.
    """

    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        company = request.user.company

        # All active users belonging to the current company.
        users = User.objects.filter(
            company=company,
            is_active=True,
        )

        # Current company's invitations.
        invitations = Invitation.objects.filter(
            company=company,
        ).order_by("-created_at")

        return Response(
            {
                # --------------------------------------------------
                # Company
                # --------------------------------------------------
                "company": {
                    "id": str(company.id),
                    "name": company.name,
                    "created_at": company.created_at,
                },

                # --------------------------------------------------
                # Current authenticated user
                # --------------------------------------------------
                "user": {
                    "id": str(request.user.id),
                    "name": (
                        request.user.get_full_name()
                        or request.user.email
                    ),
                    "email": request.user.email,
                    "role": request.user.role,
                },

                # --------------------------------------------------
                # User statistics
                # --------------------------------------------------
                "users": {
                    "total": users.count(),
                    "managers": users.filter(
                        role=Role.MANAGER
                    ).count(),
                    "staff": users.filter(
                        role=Role.STAFF
                    ).count(),
                },

                # --------------------------------------------------
                # Invitations
                # --------------------------------------------------
                "invitations": [
                    {
                        "id": str(invitation.id),
                        "email": invitation.email,
                        "role": invitation.role,
                        "invited_by_name": (
                            invitation.invited_by.get_full_name()
                            if invitation.invited_by
                            else None
                        ),
                        "created_at": invitation.created_at,
                        "expires_at": invitation.expires_at,
                        "accepted_at": invitation.accepted_at,
                    }
                    for invitation in invitations
                ],

                # --------------------------------------------------
                # Inventory
                # --------------------------------------------------
                # Inventory app is not implemented yet.
                # These values can be replaced later.
                "inventory": {
                    "total_products": 0,
                    "total_warehouses": 0,
                    "low_stock_count": 0,
                    "stock_value": 0,
                    "recent_movements": 0,
                },

                # --------------------------------------------------
                # Recent activity
                # --------------------------------------------------
                # Can be connected to AuditLog later.
                "recent_activity": [],
            }
        )
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Role


class IsTenantUser(BasePermission):
    """
    Default permission for tenant APIs.

    Allows access only to users who are:
    - authenticated
    - active
    - attached to a company
    """

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.company_id
        )


def role_permission(*roles):
    """
    Create a permission class that allows only specific roles.
    """

    class RolePermission(IsTenantUser):
        def has_permission(self, request, view):
            return (
                super().has_permission(request, view)
                and request.user.role in roles
            )

    RolePermission.__name__ = "Is" + "Or".join(
        role.title() for role in roles
    )

    return RolePermission


# Admin only
IsAdmin = role_permission(Role.ADMIN)

# Admin or Manager
IsManagerOrAdmin = role_permission(
    Role.ADMIN,
    Role.MANAGER,
)


class ReadAnyWriteManager(IsTenantUser):
    """
    All tenant users can read.

    Admin and Manager can:
    - create
    - update
    - partially update
    - delete

    Staff can only read.
    """

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        if request.method in SAFE_METHODS:
            return True

        return request.user.role in (
            Role.ADMIN,
            Role.MANAGER,
        )


class IsAdminRole(IsTenantUser):
    """
    Allows access only to company administrators.
    """

    message = "Only company administrators can perform this action."

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.role == Role.ADMIN
        )
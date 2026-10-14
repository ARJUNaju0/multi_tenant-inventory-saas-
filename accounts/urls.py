from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (ActivityLogView, CompanyRegistrationView, InvitationCreateView, LogoutView,UserCreateView,UserDetailView,CustomTokenObtainPairView,CurrentUserView,UserManagementViewSet,UserProfileView,InvitationAcceptView)


# Admin user management routes
router = DefaultRouter()
router.register(r"users",UserManagementViewSet,basename="user-management",)


urlpatterns = [
    # Company + first admin registration
    path("company/register/",CompanyRegistrationView.as_view(),name="company-register",),

    # User registration
    path("register/",UserCreateView.as_view(),name="user-register",),

    # JWT authentication
    path("login/",CustomTokenObtainPairView.as_view(),name="login",),

    path("token/refresh/",TokenRefreshView.as_view(),name="token-refresh",),

    # Current authenticated user
    path("me/",CurrentUserView.as_view(),name="user-detail",),

    # Logout
    path("logout/",LogoutView.as_view(),name="logout",),

    # Admin user management
    path("",include(router.urls),),

    path("profile/",UserProfileView.as_view(),name="user-profile",),

    path("users/<uuid:pk>/",UserDetailView.as_view(),name="user-detail",),

    path("invitations/",InvitationCreateView.as_view(),name="invitation-create",),

    path("invitations/accept/<str:token>/",InvitationAcceptView.as_view(),name="invitation-accept",),

    path("activity/",ActivityLogView.as_view(),name="activity-log-list",)

]
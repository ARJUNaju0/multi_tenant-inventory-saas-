from django.urls import path

from .views import DashboardView, MyCompanyView,DashboardView

urlpatterns = [
    path("", MyCompanyView.as_view(), name="my-company"),
    path("dashboard/",DashboardView.as_view(),name="dashboard",),

]
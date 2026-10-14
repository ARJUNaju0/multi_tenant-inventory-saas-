
from django.urls import path, include


from .views import (
    NotificationListView,
    UnreadNotificationCountView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
)

app_name = "notifications"

urlpatterns = [
    path("",NotificationListView.as_view(),name="notification-list",),

    path("unread-count/",UnreadNotificationCountView.as_view(),name="notification-unread-count",),

    path("mark-all-read/",MarkAllNotificationsReadView.as_view(),name="notification-mark-all-read",),

    path("<int:notification_id>/read/",MarkNotificationReadView.as_view(),name="notification-mark-read",),
]

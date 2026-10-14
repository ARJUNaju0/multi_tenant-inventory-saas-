
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    """
    Return notifications for the authenticated user only.
    Supports ?unread=true to filter unread notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if not user.company_id:
            return Notification.objects.none()

        queryset = Notification.objects.filter(
            company_id=user.company_id,
            recipient_id=user.pk,
        ).select_related("recipient", "actor")

        unread = self.request.query_params.get("unread", "").lower()

        if unread == "true":
            queryset = queryset.filter(is_read=False)

        return queryset.order_by("-created_at")


class UnreadNotificationCountView(APIView):
    """Return the unread notification count for the current user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.company_id:
            return Response({"unread_count": 0})

        unread_count = Notification.objects.filter(
            company_id=request.user.company_id,
            recipient_id=request.user.pk,
            is_read=False,
        ).count()

        return Response({"unread_count": unread_count})


class MarkNotificationReadView(APIView):
    """Mark one of the current user's notifications as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        if not request.user.company_id:
            return Response(
                {"detail": "You are not associated with a company."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            notification = Notification.objects.get(
                id=notification_id,
                company_id=request.user.company_id,
                recipient_id=request.user.pk,
            )
        except Notification.DoesNotExist:
            return Response(
                {"detail": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])

        return Response(
            {
                "message": "Notification marked as read.",
                "id": notification.pk,
                "is_read": notification.is_read,
                "read_at": notification.read_at,
            },
            status=status.HTTP_200_OK,
        )


class MarkAllNotificationsReadView(APIView):
    """Mark all unread notifications for the current user as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.company_id:
            return Response({"updated_count": 0})

        now = timezone.now()

        updated_count = Notification.objects.filter(
            company_id=request.user.company_id,
            recipient_id=request.user.pk,
            is_read=False,
        ).update(
            is_read=True,
            read_at=now,
        )

        return Response(
            {
                "message": "All notifications marked as read.",
                "updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )

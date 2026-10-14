
from django.conf import settings
from django.db import models
from django.db.models import Q


class Notification(models.Model):
    class Type(models.TextChoices):
        LOW_STOCK = "LOW_STOCK", "Low Stock"
        STOCK_IN = "STOCK_IN", "Stock Received"
        STOCK_OUT = "STOCK_OUT", "Stock Issued"
        INVITATION_ACCEPTED = (
            "INVITATION_ACCEPTED",
            "Invitation Accepted",
        )
        USER_CREATED = "USER_CREATED", "User Created"
        SYSTEM = "SYSTEM", "System"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "High"

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    # User who should receive this notification.
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    # User who triggered the event, if applicable.
    # Example: the employee who accepted an invitation.
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_notifications",
    )

    title = models.CharField(max_length=200)
    message = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=Type.choices,
        default=Type.SYSTEM,
    )

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )

    # Internal frontend page to open when clicked.
    target_url = models.CharField(max_length=300, blank=True)

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["recipient", "is_read", "-created_at"],
                name="notif_recipient_read_idx",
            ),
            models.Index(
                fields=["company", "-created_at"],
                name="notif_company_created_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(is_read=True) | Q(read_at__isnull=True),
                name="notif_unread_no_read_at",
            ),
        ]

    def __str__(self):
        return f"{self.title} - {self.recipient}"

    def mark_as_read(self):
        from django.utils import timezone

        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

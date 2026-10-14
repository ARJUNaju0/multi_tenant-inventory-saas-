
from .models import Notification


def create_notification(
    *,
    company,
    recipient,
    title,
    message,
    notification_type=Notification.Type.SYSTEM,
    priority=Notification.Priority.NORMAL,
    target_url="",
    actor=None,
):
    """
    Create a notification for a user in the specified company.

    Call this from trusted backend business logic, not directly
    with unvalidated recipient/company values from the frontend.
    """

    if not recipient or recipient.company_id != company.pk:
        raise ValueError(
            "The recipient must belong to the specified company."
        )

    if actor is not None and actor.company_id != company.pk:
        raise ValueError(
            "The actor must belong to the specified company."
        )

    return Notification.objects.create(
        company=company,
        recipient=recipient,
        actor=actor,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        target_url=target_url,
    )

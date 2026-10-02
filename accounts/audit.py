from decimal import Decimal

from .models import AuditLog


def _plain(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def log_action(*, company, user, action, entity, object_id, changes=None):
    return AuditLog.objects.create(
        company=company,
        user=user,
        action=action,
        entity=entity,
        object_id=str(object_id),
        changes=_plain(changes or {}),
    )

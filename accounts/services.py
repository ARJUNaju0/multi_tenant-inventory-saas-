from django.contrib.auth import get_user_model
from django.db import transaction

from accounts.models import Role
from companies.models import Company


User = get_user_model()


@transaction.atomic
def register_new_tenant(
    company_name,
    admin_email,
    admin_password,
):
    """
    Create a new company and its first Admin user
    inside a single database transaction.

    If either company creation or user creation fails,
    the entire transaction is rolled back.
    """

    company = Company.objects.create(
        name=company_name,
    )

    admin_user = User.objects.create_user(
        email=admin_email,
        password=admin_password,
        company=company,
        role=Role.ADMIN,
        is_active=True,
    )

    return company, admin_user
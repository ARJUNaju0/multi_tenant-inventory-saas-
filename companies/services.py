from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Company

User = get_user_model()

@transaction.atomic
def register_new_tenant(company_name, admin_email, admin_password, allow_negative_stock=False):
    """
    Creates a new company and its initial Admin user in a single transaction.
    """
    # 1. Create the Company (ID is auto-generated as UUID)
    company = Company.objects.create(name=company_name,allow_negative_stock=allow_negative_stock)

    # 2. Create the Admin User and link them to the new Company
    admin_user = User.objects.create_user(
        email=admin_email,
        password=admin_password,
        company=company,
        role='Admin',
        is_active=True,
        # If your custom user model requires a username, set it to the email
        username=admin_email 
    )

    return company, admin_user
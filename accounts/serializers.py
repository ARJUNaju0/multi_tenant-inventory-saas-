from django.utils import timezone

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .services import register_new_tenant
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Company, Invitation, Role, AuditLog


User = get_user_model()

class CompanyRegistrationSerializer(serializers.Serializer):
    """
    Serializer used when a new company and its
    first Admin user are created.
    """

    company_name = serializers.CharField(
        max_length=200,
        min_length=2,
        trim_whitespace=True,
    )

    admin_email = serializers.EmailField()

    admin_password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
    )


    def validate_company_name(self, value):
        """
        Prevent duplicate company names.
        """

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Company name is required."
            )

        if Company.objects.filter(
            name__iexact=value
        ).exists():
            raise serializers.ValidationError(
                "A company with this name already exists."
            )

        return value

    def validate_admin_email(self, value):
        """
        Check whether the email is already registered.
        """

        value = value.strip().lower()

        if User.objects.filter(
            email__iexact=value
        ).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return value

    def validate_admin_password(self, value):
        """
        Apply Django's configured password validators.
        """

        validate_password(value)

        return value

    def create(self, validated_data):
        """
        Create the Company and first Admin user.
        """

        company, admin_user = register_new_tenant(
            company_name=validated_data["company_name"],
            admin_email=validated_data["admin_email"],
            admin_password=validated_data["admin_password"],
        
        )

        return {
            "company_id": company.id,
            "company_name": company.name,
            "admin_user_id": admin_user.id,
            "admin_email": admin_user.email,
            "role": admin_user.role,
        
        }

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer used when a user logs in.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["user_id"] = str(user.id)
        token["company_id"] = str(user.company_id)
        token["role"] = user.role

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data["user"] = UserSerializer(self.user).data

        return data


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer used by a company ADMIN to create a user.

    The new user is always assigned to the same company
    as the authenticated admin creating the user.
    """

    company_name = serializers.CharField(
        source="company.name",
        read_only=True,
    )

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "password",
            "role",
            "company_name",
        ]
        read_only_fields = [
            "id",
            "company_name",
        ]

    def validate_email(self, value):
        """
        Prevent duplicate email accounts.
        """

        value = value.strip().lower()

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return value

    def validate_role(self, value):
        """
        Prevent creating another ADMIN through the normal
        user-management endpoint.

        ADMIN user creation should remain controlled separately.
        """

        if value not in [
            Role.MANAGER,
            Role.STAFF,
        ]:
            raise serializers.ValidationError(
                "Users can only be created with Manager or Staff roles."
            )

        return value

    def create(self, validated_data):
        """
        Create the user inside the authenticated admin's company.
        """

        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                "Authentication is required."
            )

        admin_user = request.user

        if admin_user.role != User.Role.ADMIN:
            raise serializers.ValidationError(
                "Only company administrators can create users."
            )

        if not admin_user.company_id:
            raise serializers.ValidationError(
                "Your account is not associated with a company."
            )

        password = validated_data.pop("password")

        user = User(
            **validated_data,
            company=admin_user.company,
        )

        user.set_password(password)
        user.save()

        return user

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer used to return user information.
    """

    company_name = serializers.CharField(source="company.name",read_only=True,)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "role",
            "company",
            "company_name",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "email",
            "company",
            "company_name",
            "is_active",
        ]



class UserProfileSerializer(serializers.ModelSerializer):
    company_id = serializers.UUIDField(source="company.id",read_only=True,)
    company_name = serializers.CharField(source="company.name",read_only=True,)

    class Meta:
        model = User

        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "company_id",
            "company_name",
            "is_active",
            "date_joined",
        ]

        read_only_fields = [
            "id",
            "email",
            "role",
            "company_id",
            "company_name",
            "is_active",
            "date_joined",
        ]

class InvitationSerializer(serializers.ModelSerializer):

    invited_by_name = serializers.CharField(source="invited_by.get_full_name",read_only=True,)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = [
            "id",
            "email",
            "role",
            "invited_by_name",
            "created_at",
            "expires_at",
            "accepted_at",
            "status",
        ]
        read_only_fields = [
            "id",
            "invited_by_name",
            "created_at",
            "expires_at",
            "accepted_at",
            "status",
        ]

    def get_status(self, obj):
        if obj.accepted_at is not None:
            return "Accepted"

        if obj.expires_at <= timezone.now():
            return "Expired"

        return "Pending"



class InvitationAcceptSerializer(serializers.Serializer):
    first_name = serializers.CharField(
        max_length=150,
        min_length=1,
    )

    last_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
    )

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
    )

    password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
    )

    def validate_first_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "First name is required."
            )

        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })

        validate_password(attrs["password"])

        return attrs


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source="user.get_full_name",
        read_only=True,
    )

    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user_name",
            "user_email",
            "action",
            "entity",
            "object_id",
            "changes",
            "created_at",
        ]

        read_only_fields = fields
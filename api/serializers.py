"""
Serializers for API endpoints
Converts model instances to/from JSON
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from catalog.models import Publication, PublicationType, Subject, Author, Item
from circulation.models import Loan, Hold, Notification
from accounts.models import User

User = get_user_model()


# ============================================================================
# User & Authentication Serializers
# ============================================================================

class UserSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "user_type",
            "date_joined",
            "is_active",
            "borrower_limit",
            "is_blocked",
        ]
        read_only_fields = ["id", "date_joined", "username"]


class UserDetailSerializer(UserSerializer):
    """Detailed user serializer with additional info"""
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            "profile_picture",
            "bio",
            "phone_number",
            "address",
            "city",
            "state",
            "postal_code",
            "country",
        ]


class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
        ]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


# ============================================================================
# Catalog Serializers
# ============================================================================

class PublicationTypeSerializer(serializers.ModelSerializer):
    """Publication type serializer"""
    
    class Meta:
        model = PublicationType
        fields = ["id", "name", "description"]


class AuthorSerializer(serializers.ModelSerializer):
    """Author serializer"""
    
    class Meta:
        model = Author
        fields = ["id", "first_name", "last_name", "biography"]


class SubjectSerializer(serializers.ModelSerializer):
    """Subject/Category serializer"""
    
    class Meta:
        model = Subject
        fields = ["id", "name", "description"]


class ItemSerializer(serializers.ModelSerializer):
    """Item/Copy serializer"""
    
    class Meta:
        model = Item
        fields = [
            "id",
            "publication",
            "item_id",
            "isbn",
            "status",
            "location",
            "barcode",
            "date_added",
        ]
        read_only_fields = ["id", "date_added"]


class PublicationListSerializer(serializers.ModelSerializer):
    """Publication list serializer (minimal info)"""
    
    publication_type = PublicationTypeSerializer(read_only=True)
    authors_count = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    available_items = serializers.SerializerMethodField()

    class Meta:
        model = Publication
        fields = [
            "id",
            "title",
            "isbn",
            "publication_type",
            "authors_count",
            "items_count",
            "available_items",
            "cover_image",
            "date_added",
        ]

    def get_authors_count(self, obj):
        return obj.authors.count()

    def get_items_count(self, obj):
        return obj.items.count()

    def get_available_items(self, obj):
        return obj.items.filter(status="available").count()


class PublicationDetailSerializer(serializers.ModelSerializer):
    """Detailed publication serializer"""
    
    publication_type = PublicationTypeSerializer(read_only=True)
    authors = AuthorSerializer(many=True, read_only=True)
    subjects = SubjectSerializer(many=True, read_only=True)
    items = ItemSerializer(many=True, read_only=True)
    available_items_count = serializers.SerializerMethodField()

    class Meta:
        model = Publication
        fields = [
            "id",
            "title",
            "subtitle",
            "isbn",
            "publication_type",
            "authors",
            "subjects",
            "publisher",
            "publication_date",
            "edition",
            "pages",
            "language",
            "abstract",
            "cover_image",
            "call_number",
            "items",
            "available_items_count",
            "date_added",
            "date_modified",
        ]
        read_only_fields = ["id", "date_added", "date_modified"]

    def get_available_items_count(self, obj):
        return obj.items.filter(status="available").count()


class PublicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating publications"""
    
    authors = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(), many=True
    )
    subjects = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), many=True
    )

    class Meta:
        model = Publication
        fields = [
            "title",
            "subtitle",
            "isbn",
            "publication_type",
            "authors",
            "subjects",
            "publisher",
            "publication_date",
            "edition",
            "pages",
            "language",
            "abstract",
            "cover_image",
            "call_number",
        ]


# ============================================================================
# Circulation Serializers
# ============================================================================

class LoanSerializer(serializers.ModelSerializer):
    """Loan/Checkout record serializer"""
    
    item_details = ItemSerializer(source="item", read_only=True)
    publication_title = serializers.CharField(
        source="item.publication.title", read_only=True
    )
    borrower_name = serializers.CharField(
        source="borrower.get_full_name", read_only=True
    )
    is_overdue = serializers.SerializerMethodField()
    days_until_due = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            "id",
            "item",
            "item_details",
            "publication_title",
            "borrower",
            "borrower_name",
            "checkout_date",
            "due_date",
            "return_date",
            "renewal_count",
            "is_overdue",
            "days_until_due",
        ]
        read_only_fields = ["id", "checkout_date", "return_date"]

    def get_is_overdue(self, obj):
        from django.utils import timezone
        return obj.is_overdue()

    def get_days_until_due(self, obj):
        from django.utils import timezone
        if obj.return_date:
            return 0
        today = timezone.now().date()
        delta = obj.due_date - today
        return max(0, delta.days)


class HoldSerializer(serializers.ModelSerializer):
    """Hold/Reserve record serializer"""
    
    publication_title = serializers.CharField(
        source="publication.title", read_only=True
    )
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    queue_position = serializers.SerializerMethodField()

    class Meta:
        model = Hold
        fields = [
            "id",
            "publication",
            "publication_title",
            "user",
            "user_name",
            "hold_date",
            "queue_position",
            "status",
            "ready_date",
            "pickup_deadline",
        ]
        read_only_fields = ["id", "hold_date", "queue_position"]

    def get_queue_position(self, obj):
        return obj.get_queue_position()


class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    
    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "notification_type",
            "title",
            "message",
            "related_loan",
            "related_hold",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class BorrowerStatsSerializer(serializers.Serializer):
    """Borrower statistics serializer"""
    
    total_loans = serializers.IntegerField()
    active_loans = serializers.IntegerField()
    overdue_loans = serializers.IntegerField()
    total_holds = serializers.IntegerField()
    pending_holds = serializers.IntegerField()
    is_blocked = serializers.BooleanField()
    borrowing_limit = serializers.IntegerField()
    loans_available = serializers.IntegerField()

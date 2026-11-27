"""
API Viewsets for REST endpoints
Handles CRUD operations for all models
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated as DRFIsAuthenticated,
    AllowAny,
)
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model, authenticate
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from catalog.models import Publication, PublicationType, Subject, Author, Item
from circulation.models import Loan, Hold, Notification
from accounts.security import TwoFactorAuthManager

from .permissions import IsAdmin, IsAdminOrStaff, IsOwnerOrAdmin, IsStaffOrAdmin
from .permissions import IsAuthenticatedAndAgreed
from .serializers import (
    UserSerializer,
    UserDetailSerializer,
    UserRegisterSerializer,
    PublicationTypeSerializer,
    AuthorSerializer,
    SubjectSerializer,
    ItemSerializer,
    PublicationListSerializer,
    PublicationDetailSerializer,
    PublicationCreateSerializer,
    LoanSerializer,
    HoldSerializer,
    NotificationSerializer,
    BorrowerStatsSerializer,
)
from .permissions import (
    IsBorrower,
    IsNotBlocked,
)
from elibrary.caching import (
    CacheManager,
    QueryOptimizer,
    invalidate_cache,
)

User = get_user_model()


# ============================================================================
# Authentication & User Viewsets
# ============================================================================

class ObtainAuthTokenView(APIView):
    """
    Obtain authentication token.
    POST /api/v1/auth/token/ - Get token
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'detail': 'Credentials not provided'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                {'detail': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if user.two_factor_enabled:
            totp_code = request.data.get("totp_code", "")
            if not totp_code or not TwoFactorAuthManager.verify_totp(user, totp_code):
                return Response(
                    {"detail": "A valid authenticator code is required."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


class AcceptUserAgreementView(APIView):
    """Record agreement acceptance for an authenticated API user."""

    permission_classes = [DRFIsAuthenticated]

    def post(self, request):
        request.user.agreed_to_terms = True
        request.user.agreed_at = timezone.now()
        request.user.save(update_fields=["agreed_to_terms", "agreed_at"])
        return Response({"accepted": True, "agreed_at": request.user.agreed_at})


class UserRegistrationViewSet(viewsets.ViewSet):
    """Administrator-only borrower/student account creation endpoint."""
    
    permission_classes = [IsAdmin]

    def create(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "User registered successfully",
                    "user_id": user.id,
                    "username": user.username,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    User management viewset
    - GET /api/v1/users/ - List all users (admin only)
    - GET /api/v1/users/{id}/ - Get user details
    - PUT /api/v1/users/{id}/ - Update user
    - DELETE /api/v1/users/{id}/ - Delete user (admin only)
    - GET /api/v1/users/me/ - Get current user
    - GET /api/v1/users/{id}/loans/ - Get user's loans
    - GET /api/v1/users/{id}/holds/ - Get user's holds
    """
    
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticatedAndAgreed]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["user_type", "is_active", "is_blocked"]
    search_fields = ["username", "email", "first_name", "last_name"]

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [IsAdmin]
        elif self.action == "stats":
            permission_classes = [IsStaffOrAdmin]
        elif self.action in ["destroy", "list"]:
            permission_classes = [IsAdmin]
        elif self.action == "me":
            permission_classes = [IsAuthenticatedAndAgreed]
        else:
            permission_classes = [IsOwnerOrAdmin]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self.request.user, "user_type", "") == "admin_staff":
            return queryset.filter(is_superuser=False)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return UserSerializer
        return UserDetailSerializer

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Get current logged-in user"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def loans(self, request, pk=None):
        """Get all loans for a specific user"""
        user = self.get_object()
        loans = Loan.objects.filter(borrower=user)
        serializer = LoanSerializer(loans, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def holds(self, request, pk=None):
        """Get all holds for a specific user"""
        user = self.get_object()
        holds = Hold.objects.filter(user=user)
        serializer = HoldSerializer(holds, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[IsStaffOrAdmin])
    def stats(self, request, pk=None):
        """Get borrower statistics"""
        user = self.get_object()
        active_loans = Loan.objects.filter(
            borrower=user, return_date__isnull=True
        ).count()
        overdue_loans = Loan.objects.filter(
            borrower=user,
            return_date__isnull=True,
            due_date__lt=timezone.now().date(),
        ).count()
        holds = Hold.objects.filter(borrower=user)
        pending_holds = holds.filter(status__in=["waiting", "ready"]).count()

        data = {
            "total_loans": Loan.objects.filter(borrower=user).count(),
            "active_loans": active_loans,
            "overdue_loans": overdue_loans,
            "total_holds": holds.count(),
            "pending_holds": pending_holds,
            "is_blocked": user.is_blocked,
            "borrowing_limit": user.max_items_allowed,
            "loans_available": max(0, user.max_items_allowed - active_loans),
        }
        serializer = BorrowerStatsSerializer(data)
        return Response(serializer.data)


# ============================================================================
# Catalog Viewsets
# ============================================================================

class PublicationTypeViewSet(viewsets.ModelViewSet):
    """Publication type management"""
    
    queryset = PublicationType.objects.all()
    serializer_class = PublicationTypeSerializer
    permission_classes = [IsAuthenticatedAndAgreed]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_permissions(self):
        if self.action in ["create", "update", "destroy"]:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAuthenticatedAndAgreed]
        return [permission() for permission in permission_classes]


class AuthorViewSet(viewsets.ModelViewSet):
    """Author management"""
    
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticatedAndAgreed]
    filter_backends = [filters.SearchFilter]
    search_fields = ["first_name", "last_name"]

    def get_permissions(self):
        if self.action in ["create", "update", "destroy"]:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAuthenticatedAndAgreed]
        return [permission() for permission in permission_classes]


class SubjectViewSet(viewsets.ModelViewSet):
    """Subject/Category management"""
    
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticatedAndAgreed]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_permissions(self):
        if self.action in ["create", "update", "destroy"]:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAuthenticatedAndAgreed]
        return [permission() for permission in permission_classes]


class ItemViewSet(viewsets.ModelViewSet):
    """Item/Copy management with query optimization"""
    
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticatedAndAgreed]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["publication", "status", "location"]
    search_fields = ["barcode", "publication__isbn"]

    def get_queryset(self):
        """Optimize queryset with select_related and prefetch_related."""
        qs = super().get_queryset()
        return QueryOptimizer.optimize_item_queryset(qs)

    def get_permissions(self):
        if self.action in ["create", "update", "destroy"]:
            permission_classes = [IsStaffOrAdmin]
        else:
            permission_classes = [IsAuthenticatedAndAgreed]
        return [permission() for permission in permission_classes]
    
    @invalidate_cache(prefix=CacheManager.PREFIXES['ITEM'])
    def create(self, request, *args, **kwargs):
        """Create item and invalidate cache."""
        return super().create(request, *args, **kwargs)
    
    @invalidate_cache(prefix=CacheManager.PREFIXES['ITEM'])
    def update(self, request, *args, **kwargs):
        """Update item and invalidate cache."""
        return super().update(request, *args, **kwargs)
    
    @invalidate_cache(prefix=CacheManager.PREFIXES['ITEM'])
    def destroy(self, request, *args, **kwargs):
        """Delete item and invalidate cache."""
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def available(self, request):
        """Get all available items"""
        items = Item.objects.filter(status="available")
        items = QueryOptimizer.optimize_item_queryset(items)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)


class PublicationViewSet(viewsets.ModelViewSet):
    """
    Publication management with query optimization
    - GET /api/v1/publications/ - List all publications
    - POST /api/v1/publications/ - Create publication (admin only)
    - GET /api/v1/publications/{id}/ - Get publication details
    - PUT /api/v1/publications/{id}/ - Update publication (admin only)
    - DELETE /api/v1/publications/{id}/ - Delete publication (admin only)
    - GET /api/v1/publications/{id}/availability/ - Check availability
    """
    
    queryset = Publication.objects.all()
    permission_classes = [IsAuthenticatedAndAgreed]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["publication_type", "language"]
    search_fields = [
        "title",
        "subtitle",
        "isbn",
        "authors__first_name",
        "authors__last_name",
        "subjects__name",
    ]
    ordering_fields = ["title", "date_added", "publication_date"]
    ordering = ["-date_added"]

    def get_queryset(self):
        """Optimize queryset with select_related and prefetch_related."""
        qs = super().get_queryset()
        return QueryOptimizer.optimize_publication_queryset(qs)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PublicationDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return PublicationCreateSerializer
        else:
            return PublicationListSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "destroy", "partial_update"]:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAuthenticatedAndAgreed]
        return [permission() for permission in permission_classes]
    
    @invalidate_cache(prefix=CacheManager.PREFIXES['PUBLICATION'])
    def create(self, request, *args, **kwargs):
        """Create publication and invalidate cache."""
        return super().create(request, *args, **kwargs)
    
    @invalidate_cache(prefix=CacheManager.PREFIXES['PUBLICATION'])
    def update(self, request, *args, **kwargs):
        """Update publication and invalidate cache."""
        return super().update(request, *args, **kwargs)
    
    @invalidate_cache(prefix=CacheManager.PREFIXES['PUBLICATION'])
    def destroy(self, request, *args, **kwargs):
        """Delete publication and invalidate cache."""
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["get"])
    def availability(self, request, pk=None):
        """Check availability of a publication"""
        publication = self.get_object()
        items = publication.items.all()
        available = items.filter(status="available").count()
        total = items.count()

        return Response(
            {
                "publication_id": publication.id,
                "title": publication.title,
                "total_copies": total,
                "available_copies": available,
                "on_loan": items.filter(status="on_loan").count(),
                "in_transit": items.filter(status="in_transit").count(),
                "items": ItemSerializer(items, many=True).data,
            }
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticatedAndAgreed, IsBorrower, IsNotBlocked])
    def borrow(self, request, pk=None):
        """Place a hold/request to borrow this publication"""
        publication = self.get_object()
        if not request.user.can_borrow():
            return Response(
                {"error": "Only eligible borrower accounts may place holds."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # A checked-out copy or active hold should not create a second request.
        existing_loan = Loan.objects.filter(
            borrower=request.user,
            item__publication=publication,
            return_date__isnull=True,
        ).exists()
        if existing_loan:
            return Response(
                {"error": "You already have a copy of this publication checked out"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        existing_hold = Hold.objects.filter(
            publication=publication,
            borrower=request.user,
            status__in=["waiting", "ready"],
        ).first()
        if existing_hold:
            return Response(HoldSerializer(existing_hold).data, status=status.HTTP_200_OK)

        serializer = HoldSerializer(data={**request.data, "publication": publication.pk})
        serializer.is_valid(raise_exception=True)
        hold = serializer.save(borrower=request.user)
        hold.update_queue_position()
        return Response(
            HoldSerializer(hold).data,
            status=status.HTTP_201_CREATED,
        )


# ============================================================================
# Circulation Viewsets
# ============================================================================

class LoanViewSet(viewsets.ModelViewSet):
    """
    Loan management with query optimization
    - GET /api/v1/loans/ - List loans
    - GET /api/v1/loans/my-loans/ - Get current user's loans
    - GET /api/v1/loans/{id}/renew/ - Renew a loan
    """
    
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticatedAndAgreed]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["borrower", "status"]
    ordering = ["-checkout_date"]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Loan.objects.none()
        
        if user.is_library_staff:
            qs = Loan.objects.all()
        else:
            # Borrowers can only see their own loans
            qs = Loan.objects.filter(borrower=user)
        
        # Apply query optimization
        return QueryOptimizer.optimize_loan_queryset(qs)

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsStaffOrAdmin]
        else:
            permission_classes = [IsAuthenticatedAndAgreed]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        from rest_framework.exceptions import PermissionDenied, ValidationError

        borrower = serializer.validated_data["borrower"]
        item = serializer.validated_data["item"]
        if not borrower.can_borrow():
            raise PermissionDenied("Only eligible borrower accounts may check out items.")

        with transaction.atomic():
            locked_item = Item.objects.select_for_update().get(pk=item.pk)
            if locked_item.status != "available":
                raise ValidationError({"item": "This item is no longer available for checkout."})
            if not borrower.can_borrow():
                raise PermissionDenied("The borrower is no longer eligible to check out items.")
            serializer.save(item=locked_item, checkout_staff=self.request.user)
    
    @invalidate_cache(prefix=CacheManager.PREFIXES['LOAN'])
    def create(self, request, *args, **kwargs):
        """Create loan and invalidate cache."""
        return super().create(request, *args, **kwargs)
    
    @invalidate_cache(prefix=CacheManager.PREFIXES['LOAN'])
    def destroy(self, request, *args, **kwargs):
        """Delete loan and invalidate cache."""
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def my_loans(self, request):
        """Get current user's loans"""
        loans = Loan.objects.filter(borrower=request.user)
        loans = QueryOptimizer.optimize_loan_queryset(loans)
        serializer = self.get_serializer(loans, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Get active (not yet returned) loans"""
        loans = Loan.objects.filter(return_date__isnull=True)
        if request.user.user_type == "borrower":
            loans = loans.filter(borrower=request.user)
        loans = QueryOptimizer.optimize_loan_queryset(loans)
        serializer = self.get_serializer(loans, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        """Get overdue loans"""
        loans = Loan.objects.filter(
            return_date__isnull=True, due_date__lt=timezone.now().date()
        )
        if request.user.user_type == "borrower":
            loans = loans.filter(borrower=request.user)
        serializer = self.get_serializer(loans, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticatedAndAgreed])
    def renew(self, request, pk=None):
        """Renew a loan"""
        loan = self.get_object()
        if request.user.user_type == "borrower":
            if loan.borrower != request.user:
                return Response(
                    {"error": "You can only renew your own loans"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not request.user.can_borrow():
                return Response(
                    {"error": "Only eligible borrower accounts may renew loans."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        if not loan.can_renew():
            return Response(
                {"error": "This loan is not eligible for renewal."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        loan.renew()

        return Response(
            {
                "message": "Loan renewed successfully",
                "new_due_date": loan.due_date,
                "renewal_count": loan.renewal_count,
            }
        )


class HoldViewSet(viewsets.ModelViewSet):
    """
    Hold/Reserve management
    - GET /api/v1/holds/ - List holds
    - POST /api/v1/holds/ - Create hold
    - GET /api/v1/holds/my-holds/ - Get current user's holds
    """
    
    serializer_class = HoldSerializer
    permission_classes = [IsAuthenticatedAndAgreed]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["publication", "borrower", "status"]
    ordering = ["-hold_date"]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Hold.objects.none()
        if user.is_library_staff:
            return Hold.objects.all()
        # Borrowers can only see their own holds
        return Hold.objects.filter(borrower=user)

    def get_permissions(self):
        if self.action in ["create"]:
            permission_classes = [IsAuthenticatedAndAgreed, IsNotBlocked]
        elif self.action in ["update", "partial_update", "destroy", "set_ready", "complete"]:
            permission_classes = [IsStaffOrAdmin]
        else:
            permission_classes = [IsAuthenticatedAndAgreed]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        borrower = self.request.user
        if not borrower.can_borrow():
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only eligible borrower accounts may place holds.")
        publication = serializer.validated_data["publication"]
        if Hold.objects.filter(
            publication=publication,
            borrower=borrower,
            status__in=["waiting", "ready"],
        ).exists():
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"publication": "You already have an active hold on this publication."})
        hold = serializer.save(borrower=borrower)
        hold.update_queue_position()

    @action(detail=False, methods=["get"])
    def my_holds(self, request):
        """Get current user's holds"""
        holds = Hold.objects.filter(borrower=request.user)
        serializer = self.get_serializer(holds, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsStaffOrAdmin])
    def set_ready(self, request, pk=None):
        """Mark a hold as ready for pickup"""
        hold = self.get_object()
        if hold.status != "waiting":
            return Response({"error": "Only waiting holds can be marked ready."}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            item = Item.objects.select_for_update().filter(
                publication=hold.publication,
                status="available",
            ).first()
            if item is None:
                return Response({"error": "No available item can be reserved."}, status=status.HTTP_400_BAD_REQUEST)
            item.status = "on_hold_shelf"
            item.save(update_fields=["status"])
            hold.reserved_item = item
            hold.status = "ready"
            hold.ready_date = timezone.now()
            hold.expiry_date = timezone.now() + timezone.timedelta(
                days=getattr(settings, "HOLD_PICKUP_DAYS", 7)
            )
            hold.save(update_fields=["reserved_item", "status", "ready_date", "expiry_date"])
        Notification.objects.create(
            borrower=hold.borrower,
            notification_type="hold_ready",
            title=f"Hold Ready for Pickup: {hold.publication.title}",
            message=f'Your hold for "{hold.publication.title}" is ready for pickup.',
            hold=hold,
            action_url="/accounts/my-account/",
        )
        return Response({"message": "Hold marked as ready"})

    @action(detail=True, methods=["post"], permission_classes=[IsStaffOrAdmin])
    def complete(self, request, pk=None):
        """Complete a hold (picked up)"""
        hold = self.get_object()
        if hold.status != "ready" or not hold.reserved_item_id:
            return Response({"error": "This hold has no reserved item ready for pickup."}, status=status.HTTP_400_BAD_REQUEST)
        if not hold.borrower.can_borrow():
            return Response(
                {"error": "The borrower is no longer eligible to borrow."},
                status=status.HTTP_403_FORBIDDEN,
            )
        with transaction.atomic():
            item = Item.objects.select_for_update().get(
                pk=hold.reserved_item_id,
                publication=hold.publication,
                status="on_hold_shelf",
            )
            loan = Loan.objects.create(
                item=item,
                borrower=hold.borrower,
                checkout_staff=request.user,
                status="active",
            )
            hold.status = "fulfilled"
            hold.save(update_fields=["status"])
        Notification.objects.create(
            borrower=hold.borrower,
            notification_type="checkout",
            title=f"Item Checked Out: {hold.publication.title}",
            message=f'You have checked out "{hold.publication.title}". Due date: {loan.due_date}.',
            loan=loan,
            hold=hold,
            action_url="/accounts/my-account/",
        )
        return Response({"message": "Hold completed"})


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Notification management
    - GET /api/v1/notifications/ - List notifications
    - GET /api/v1/notifications/my-notifications/ - Get current user's notifications
    """
    
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticatedAndAgreed]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["notification_type", "is_read"]
    ordering = ["-created_date"]

    def get_queryset(self):
        # Users can only see their own notifications
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        return Notification.objects.filter(borrower=self.request.user)

    @action(detail=False, methods=["get"])
    def unread(self, request):
        """Get unread notifications"""
        notifications = Notification.objects.filter(
            borrower=request.user, is_read=False
        )
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"message": "Notification marked as read"})

    @action(detail=False, methods=["post"])
    def mark_all_as_read(self, request):
        """Mark all notifications as read"""
        Notification.objects.filter(borrower=request.user, is_read=False).update(
            is_read=True
        )
        return Response({"message": "All notifications marked as read"})

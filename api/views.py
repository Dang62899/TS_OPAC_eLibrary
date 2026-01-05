"""
API Viewsets for REST endpoints
Handles CRUD operations for all models
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAdminUser,
)
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.db.models import Q, Count

from catalog.models import Publication, PublicationType, Subject, Author, Item
from circulation.models import Loan, Hold, Notification
from accounts.models import User as CustomUser

from .permissions import IsAdmin, IsAdminOrStaff, IsOwnerOrAdmin, IsStaffOrAdmin
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
    IsOwnerOrAdmin,
    IsStaffOrAdmin,
    IsAdmin,
    IsBorrower,
    IsBorrowerOrStaff,
    IsNotBlocked,
)
from elibrary.caching import (
    CacheManager,
    QueryOptimizer,
    StatsCacheManager,
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
        
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


class UserRegistrationViewSet(viewsets.ViewSet):
    """User registration endpoint"""
    
    permission_classes = [AllowAny]

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
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["user_type", "is_active", "is_blocked"]
    search_fields = ["username", "email", "first_name", "last_name"]

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [IsAdminOrStaff]
        elif self.action in ["destroy", "list"]:
            permission_classes = [IsAdmin]
        elif self.action == "me":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsOwnerOrAdmin]
        return [permission() for permission in permission_classes]

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
        holds = Hold.objects.filter(user=user)
        pending_holds = holds.filter(status__in=["pending", "ready"]).count()

        data = {
            "total_loans": Loan.objects.filter(borrower=user).count(),
            "active_loans": active_loans,
            "overdue_loans": overdue_loans,
            "total_holds": holds.count(),
            "pending_holds": pending_holds,
            "is_blocked": user.is_blocked,
            "borrowing_limit": user.borrower_limit,
            "loans_available": max(0, user.borrower_limit - active_loans),
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
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_permissions(self):
        if self.action in ["create", "update", "destroy"]:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class AuthorViewSet(viewsets.ModelViewSet):
    """Author management"""
    
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["first_name", "last_name"]

    def get_permissions(self):
        if self.action in ["create", "update", "destroy"]:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class SubjectViewSet(viewsets.ModelViewSet):
    """Subject/Category management"""
    
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_permissions(self):
        if self.action in ["create", "update", "destroy"]:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class ItemViewSet(viewsets.ModelViewSet):
    """Item/Copy management with query optimization"""
    
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["publication", "status", "location"]
    search_fields = ["item_id", "isbn", "barcode"]

    def get_queryset(self):
        """Optimize queryset with select_related and prefetch_related."""
        qs = super().get_queryset()
        return QueryOptimizer.optimize_item_queryset(qs)

    def get_permissions(self):
        if self.action in ["create", "update", "destroy"]:
            permission_classes = [IsStaffOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
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
            permission_classes = [IsAuthenticated]
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

    @action(detail=True, methods=["post"], permission_classes=[IsBorrowerOrStaff, IsNotBlocked])
    def borrow(self, request, pk=None):
        """Place a hold/request to borrow this publication"""
        publication = self.get_object()
        # Check if already borrowed
        existing_loan = Loan.objects.filter(
            borrower=request.user, publication=publication, return_date__isnull=True
        ).exists()
        if existing_loan:
            return Response(
                {"error": "You already have a copy of this publication checked out"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Create hold request
        hold, created = Hold.objects.get_or_create(
            publication=publication, user=request.user
        )
        serializer = HoldSerializer(hold)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
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
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["borrower", "status"]
    ordering = ["-checkout_date"]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Loan.objects.none()
        
        if user.user_type == "admin" or user.user_type == "staff":
            qs = Loan.objects.all()
        else:
            # Borrowers can only see their own loans
            qs = Loan.objects.filter(borrower=user)
        
        # Apply query optimization
        return QueryOptimizer.optimize_loan_queryset(qs)

    def get_permissions(self):
        if self.action in ["create", "destroy"]:
            permission_classes = [IsStaffOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
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

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def renew(self, request, pk=None):
        """Renew a loan"""
        loan = self.get_object()
        
        # Check permission
        if request.user.user_type == "borrower" and loan.borrower != request.user:
            return Response(
                {"error": "You can only renew your own loans"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        # Attempt renewal
        if loan.renewal_count >= 3:
            return Response(
                {"error": "Maximum renewals reached"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Extend due date
        from datetime import timedelta
        loan.due_date += timedelta(days=14)
        loan.renewal_count += 1
        loan.save()

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
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["publication", "borrower", "status"]
    ordering = ["-hold_date"]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Hold.objects.none()
        if user.user_type == "admin" or user.user_type == "staff":
            return Hold.objects.all()
        # Borrowers can only see their own holds
        return Hold.objects.filter(borrower=user)

    def get_permissions(self):
        if self.action in ["destroy"]:
            permission_classes = [IsStaffOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

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
        hold.status = "ready"
        hold.ready_date = timezone.now()
        hold.save()
        return Response({"message": "Hold marked as ready"})

    @action(detail=True, methods=["post"], permission_classes=[IsStaffOrAdmin])
    def complete(self, request, pk=None):
        """Complete a hold (picked up)"""
        hold = self.get_object()
        hold.status = "completed"
        hold.save()
        return Response({"message": "Hold completed"})


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Notification management
    - GET /api/v1/notifications/ - List notifications
    - GET /api/v1/notifications/my-notifications/ - Get current user's notifications
    """
    
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["notification_type", "is_read"]
    ordering = ["-created_at"]

    def get_queryset(self):
        # Users can only see their own notifications
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def unread(self, request):
        """Get unread notifications"""
        notifications = Notification.objects.filter(
            user=request.user, is_read=False
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
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True
        )
        return Response({"message": "All notifications marked as read"})

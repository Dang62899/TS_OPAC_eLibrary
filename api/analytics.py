# Analytics Views and API for TS OPAC eLibrary

from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Sum, Q, F, Case, When, IntegerField, Avg
from django.views import View
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.shortcuts import render
from datetime import timedelta, datetime
from catalog.models import Publication, Item
from circulation.models import Loan, Reservation, ActivityLog
import json

# ============================================================================
# SERIALIZERS
# ============================================================================

class ActivityLogSerializer(serializers.Serializer):
    """Serializer for activity log entries"""
    id = serializers.IntegerField()
    user = serializers.CharField(source='user.username')
    action = serializers.CharField()
    timestamp = serializers.DateTimeField()
    description = serializers.CharField()
    
    class Meta:
        fields = ['id', 'user', 'action', 'timestamp', 'description']


class LibraryMetricsSerializer(serializers.Serializer):
    """Serializer for library-wide metrics"""
    total_publications = serializers.IntegerField()
    total_items = serializers.IntegerField()
    available_items = serializers.IntegerField()
    checked_out_items = serializers.IntegerField()
    reserved_items = serializers.IntegerField()
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_checkouts = serializers.IntegerField()
    avg_checkout_duration = serializers.FloatField()


class CirculationTrendSerializer(serializers.Serializer):
    """Serializer for circulation trends"""
    date = serializers.DateField()
    checkouts = serializers.IntegerField()
    returns = serializers.IntegerField()
    reservations = serializers.IntegerField()
    active_loans = serializers.IntegerField()


class PopularItemSerializer(serializers.Serializer):
    """Serializer for popular items"""
    id = serializers.IntegerField()
    title = serializers.CharField()
    checkout_count = serializers.IntegerField()
    current_availability = serializers.IntegerField()
    average_rating = serializers.FloatField()


class SearchStatisticSerializer(serializers.Serializer):
    """Serializer for search statistics"""
    query = serializers.CharField()
    count = serializers.IntegerField()
    unique_users = serializers.IntegerField()
    timestamp = serializers.DateTimeField()


# ============================================================================
# VIEWSETS
# ============================================================================

class LibraryMetricsViewSet(viewsets.ViewSet):
    """
    API endpoint for library-wide metrics and statistics
    
    Endpoints:
    - GET /api/analytics/metrics/ - Overall library metrics
    - GET /api/analytics/metrics/today/ - Today's statistics
    - GET /api/analytics/metrics/monthly/ - Monthly trends
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get overall library metrics"""
        from django.contrib.auth.models import User
        from circulation.models import Loan
        
        try:
            total_publications = Publication.objects.count()
            total_items = Item.objects.count()
            available_items = Item.objects.filter(status='available').count()
            checked_out_items = Item.objects.filter(status='checked_out').count()
            reserved_items = Item.objects.filter(status='reserved').count()
            total_users = User.objects.filter(is_active=True).count()
            
            # Active users (logged in last 30 days)
            active_users = User.objects.filter(
                last_login__gte=timezone.now() - timedelta(days=30)
            ).count()
            
            # Total checkouts
            total_checkouts = Loan.objects.count()
            
            # Average checkout duration
            avg_duration = Loan.objects.filter(
                return_date__isnull=False
            ).aggregate(
                avg_days=(Avg(F('return_date') - F('checkout_date')))
            )['avg_days']
            
            avg_checkout_duration = avg_duration.days if avg_duration else 0
            
            metrics = {
                'total_publications': total_publications,
                'total_items': total_items,
                'available_items': available_items,
                'checked_out_items': checked_out_items,
                'reserved_items': reserved_items,
                'total_users': total_users,
                'active_users': active_users,
                'total_checkouts': total_checkouts,
                'avg_checkout_duration': avg_checkout_duration,
                'timestamp': timezone.now()
            }
            
            serializer = LibraryMetricsSerializer(metrics)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's statistics"""
        today = timezone.now().date()
        
        today_checkouts = Loan.objects.filter(
            checkout_date__date=today
        ).count()
        
        today_returns = Loan.objects.filter(
            return_date__date=today
        ).count()
        
        today_reservations = Reservation.objects.filter(
            request_date__date=today
        ).count()
        
        return Response({
            'date': today,
            'checkouts': today_checkouts,
            'returns': today_returns,
            'reservations': today_reservations
        })
    
    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Get monthly trends for last 12 months"""
        trends = []
        
        for i in range(12):
            month = timezone.now().date().replace(day=1) - timedelta(days=i*30)
            
            checkouts = Loan.objects.filter(
                checkout_date__year=month.year,
                checkout_date__month=month.month
            ).count()
            
            returns = Loan.objects.filter(
                return_date__year=month.year,
                return_date__month=month.month
            ).count()
            
            trends.append({
                'month': month,
                'checkouts': checkouts,
                'returns': returns
            })
        
        return Response(trends)


class CirculationAnalyticsViewSet(viewsets.ViewSet):
    """
    Circulation analytics and trends
    
    Endpoints:
    - GET /api/analytics/circulation/ - Overall circulation stats
    - GET /api/analytics/circulation/trends/ - Circulation trends
    - GET /api/analytics/circulation/popular/ - Popular items
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get circulation statistics"""
        from circulation.models import Loan
        
        total_loans = Loan.objects.count()
        active_loans = Loan.objects.filter(return_date__isnull=True).count()
        completed_loans = Loan.objects.filter(return_date__isnull=False).count()
        overdue_loans = Loan.objects.filter(
            return_date__isnull=True,
            due_date__lt=timezone.now()
        ).count()
        
        return Response({
            'total_loans': total_loans,
            'active_loans': active_loans,
            'completed_loans': completed_loans,
            'overdue_loans': overdue_loans
        })
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get circulation trends"""
        from circulation.models import Loan
        
        # Get trends for last 30 days
        trends = []
        for i in range(30):
            date = timezone.now().date() - timedelta(days=i)
            
            checkouts = Loan.objects.filter(
                checkout_date__date=date
            ).count()
            
            returns = Loan.objects.filter(
                return_date__date=date
            ).count()
            
            active = Loan.objects.filter(
                checkout_date__date__lte=date,
                return_date__isnull=True
            ).count()
            
            trends.append({
                'date': date,
                'checkouts': checkouts,
                'returns': returns,
                'active_loans': active
            })
        
        return Response(trends)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most popular items (by checkouts)"""
        from circulation.models import Loan
        
        popular_items = Publication.objects.annotate(
            checkout_count=Count('item__loans')
        ).order_by('-checkout_count')[:20]
        
        data = []
        for pub in popular_items:
            available = pub.item_set.filter(status='available').count()
            data.append({
                'id': pub.id,
                'title': pub.title,
                'checkout_count': pub.checkout_count or 0,
                'available_copies': available,
                'total_copies': pub.item_set.count()
            })
        
        return Response(data)


class SearchAnalyticsViewSet(viewsets.ViewSet):
    """
    Search analytics and statistics
    
    Endpoints:
    - GET /api/analytics/search/ - Search statistics
    - GET /api/analytics/search/popular/ - Popular search terms
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get search statistics"""
        try:
            searches = ActivityLog.objects.filter(
                action='search'
            ).values('description').annotate(
                count=Count('id'),
                unique_users=Count('user', distinct=True)
            ).order_by('-count')[:20]
            
            return Response(list(searches))
        except:
            return Response([])
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular search queries"""
        searches = ActivityLog.objects.filter(
            action='search'
        ).values('description').annotate(
            count=Count('id')
        ).order_by('-count')[:50]
        
        return Response(list(searches))


# ============================================================================
# VIEWS (Django views, not API viewsets)
# ============================================================================

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('catalog.view_analytics', raise_exception=True), name='dispatch')
class AnalyticsDashboardView(View):
    """Main analytics dashboard"""
    
    def get(self, request):
        from circulation.models import Loan
        from django.contrib.auth.models import User
        
        # Calculate metrics
        total_pubs = Publication.objects.count()
        total_items = Item.objects.count()
        available = Item.objects.filter(status='available').count()
        total_users = User.objects.filter(is_active=True).count()
        total_loans = Loan.objects.count()
        
        # Recent activity
        recent_activity = ActivityLog.objects.all().order_by('-timestamp')[:10]
        
        # Circulation stats for chart
        circulation_data = []
        for i in range(30):
            date = timezone.now().date() - timedelta(days=i)
            checkouts = Loan.objects.filter(checkout_date__date=date).count()
            circulation_data.append({'date': str(date), 'count': checkouts})
        
        circulation_data.reverse()
        
        context = {
            'total_publications': total_pubs,
            'total_items': total_items,
            'available_items': available,
            'total_users': total_users,
            'total_loans': total_loans,
            'recent_activity': recent_activity,
            'circulation_data': json.dumps(circulation_data)
        }
        
        return render(request, 'analytics/dashboard.html', context)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('catalog.view_analytics', raise_exception=True), name='dispatch')
class PopularItemsView(View):
    """View for popular items"""
    
    def get(self, request):
        popular = Publication.objects.annotate(
            checkout_count=Count('item__loans')
        ).order_by('-checkout_count')[:20]
        
        context = {'popular_items': popular}
        return render(request, 'analytics/popular_items.html', context)

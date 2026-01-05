"""
API endpoints for analytics and monitoring dashboards.
Provides real-time metrics, performance data, and system health information.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from elibrary.metrics import MetricsCollector, PerformanceMonitor
from elibrary.analytics import DashboardProvider, TrendAnalyzer, AlertingSystem

import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def metrics_summary_view(request):
    """
    GET /api/v1/analytics/metrics-summary/
    Get comprehensive metrics summary for the last hour.
    """
    try:
        collector = MetricsCollector()
        
        return Response({
            'status': 'success',
            'data': {
                'requests': collector.get_request_metrics(minutes=60),
                'cache': collector.get_cache_metrics(minutes=60),
                'errors': collector.get_error_metrics(minutes=60),
            },
            'timestamp': collector._append_to_metrics_queue.__self__.metrics_cache_key or None,
        })
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def performance_dashboard_view(request):
    """
    GET /api/v1/analytics/performance/
    Get comprehensive performance dashboard.
    """
    try:
        dashboard = DashboardProvider.get_full_dashboard()
        
        return Response({
            'status': 'success',
            'data': dashboard,
        })
    except Exception as e:
        logger.error(f"Error getting performance dashboard: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def sla_status_view(request):
    """
    GET /api/v1/analytics/sla-status/
    Get SLA compliance status for all endpoints.
    """
    try:
        minutes = int(request.query_params.get('minutes', 60))
        sla_metrics = PerformanceMonitor.get_sla_metrics(minutes=minutes)
        
        return Response({
            'status': 'success',
            'data': sla_metrics,
            'period_minutes': minutes,
        })
    except Exception as e:
        logger.error(f"Error getting SLA status: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def request_trends_view(request):
    """
    GET /api/v1/analytics/trends/requests/
    Get request rate trends over time.
    """
    try:
        hours = int(request.query_params.get('hours', 24))
        trends = TrendAnalyzer.get_request_trends(hours=hours)
        
        return Response({
            'status': 'success',
            'data': trends,
            'period_hours': hours,
        })
    except Exception as e:
        logger.error(f"Error getting request trends: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def error_trends_view(request):
    """
    GET /api/v1/analytics/trends/errors/
    Get error rate trends over time.
    """
    try:
        hours = int(request.query_params.get('hours', 24))
        trends = TrendAnalyzer.get_error_trends(hours=hours)
        
        return Response({
            'status': 'success',
            'data': trends,
            'period_hours': hours,
        })
    except Exception as e:
        logger.error(f"Error getting error trends: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def alerts_view(request):
    """
    GET /api/v1/analytics/alerts/
    Get active system alerts and anomalies.
    """
    try:
        alerts = AlertingSystem.get_active_alerts()
        
        return Response({
            'status': 'success',
            'alerts': alerts,
            'alert_count': len(alerts),
        })
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_activity_view(request):
    """
    GET /api/v1/analytics/user-activity/
    Get current user's activity metrics.
    """
    try:
        from circulation.models import Loan, Hold, Notification
        
        user = request.user
        
        return Response({
            'status': 'success',
            'user_id': user.id,
            'user_type': user.user_type,
            'active_loans': Loan.objects.filter(
                borrower=user,
                status='active'
            ).count(),
            'active_holds': Hold.objects.filter(
                borrower=user,
                status='waiting'
            ).count(),
            'unread_notifications': Notification.objects.filter(
                user=user,
                is_read=False
            ).count(),
        })
    except Exception as e:
        logger.error(f"Error getting user activity: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def library_analytics_view(request):
    """
    GET /api/v1/analytics/library/
    Get comprehensive library analytics.
    """
    try:
        return Response({
            'status': 'success',
            'data': DashboardProvider.get_library_overview(),
        })
    except Exception as e:
        logger.error(f"Error getting library analytics: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def circulation_analytics_view(request):
    """
    GET /api/v1/analytics/circulation/
    Get circulation and loan analytics.
    """
    try:
        return Response({
            'status': 'success',
            'data': DashboardProvider.get_circulation_dashboard(),
        })
    except Exception as e:
        logger.error(f"Error getting circulation analytics: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def users_analytics_view(request):
    """
    GET /api/v1/analytics/users/
    Get user analytics and demographics.
    """
    try:
        return Response({
            'status': 'success',
            'data': DashboardProvider.get_users_dashboard(),
        })
    except Exception as e:
        logger.error(f"Error getting users analytics: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def system_health_view(request):
    """
    GET /api/v1/analytics/system-health/
    Get overall system health and status.
    """
    try:
        health = DashboardProvider.get_system_health()
        alerts = AlertingSystem.get_active_alerts()
        
        return Response({
            'status': 'success',
            'health': health,
            'active_alerts': len(alerts),
            'alerts': alerts[:5],  # Show top 5 alerts
        })
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

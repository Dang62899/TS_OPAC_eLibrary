"""
Analytics dashboard data provider.
Aggregates metrics and provides formatted data for dashboard visualization.
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.core.cache import cache

from circulation.models import Loan, Hold, Notification
from catalog.models import Publication, Item
from accounts.models import User
from elibrary.metrics import MetricsCollector, PerformanceMonitor

logger = logging.getLogger(__name__)


class DashboardProvider:
    """Provide comprehensive dashboard data for monitoring and analytics."""
    
    CACHE_TTL = 300  # 5 minutes
    
    @classmethod
    def get_full_dashboard(cls):
        """Get complete dashboard data."""
        cache_key = 'dashboard:full'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        dashboard_data = {
            'timestamp': timezone.now().isoformat(),
            'library': cls.get_library_overview(),
            'performance': cls.get_performance_dashboard(),
            'users': cls.get_users_dashboard(),
            'circulation': cls.get_circulation_dashboard(),
            'health': cls.get_system_health(),
        }
        
        cache.set(cache_key, dashboard_data, cls.CACHE_TTL)
        return dashboard_data
    
    @classmethod
    def get_library_overview(cls):
        """Get library statistics overview."""
        try:
            return {
                'total_publications': Publication.objects.count(),
                'total_items': Item.objects.count(),
                'available_items': Item.objects.filter(status='available').count(),
                'unavailable_items': Item.objects.exclude(status='available').count(),
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(is_active=True).count(),
                'blocked_users': User.objects.filter(is_blocked=True).count(),
            }
        except Exception as e:
            logger.error(f"Error getting library overview: {e}")
            return {}
    
    @classmethod
    def get_performance_dashboard(cls):
        """Get performance metrics dashboard."""
        try:
            collector = MetricsCollector()
            request_metrics = collector.get_request_metrics(minutes=60)
            cache_metrics = collector.get_cache_metrics(minutes=60)
            error_metrics = collector.get_error_metrics(minutes=60)
            sla_metrics = PerformanceMonitor.get_sla_metrics(minutes=60)
            
            return {
                'request_metrics': {
                    'total_requests': request_metrics.get('total_requests', 0),
                    'avg_response_time_ms': request_metrics.get('avg_response_time_ms', 0),
                    'requests_by_method': request_metrics.get('requests_by_method', {}),
                    'requests_by_status': request_metrics.get('requests_by_status', {}),
                    'slowest_endpoints': cls._format_endpoint_stats(
                        request_metrics.get('slowest_endpoints', [])
                    ),
                },
                'cache_metrics': {
                    'total_operations': cache_metrics.get('total_operations', 0),
                    'hit_rate': round(cache_metrics.get('hit_rate', 0), 2),
                    'hits': cache_metrics.get('hits', 0),
                    'misses': cache_metrics.get('misses', 0),
                    'avg_hit_duration_ms': round(cache_metrics.get('avg_hit_duration_ms', 0), 2),
                },
                'error_metrics': {
                    'total_errors': error_metrics.get('total_errors', 0),
                    'error_rate': round(error_metrics.get('error_rate', 0), 2),
                    'errors_by_type': error_metrics.get('errors_by_type', {}),
                },
                'sla_status': sla_metrics.get('overall_health', 'unknown'),
            }
        except Exception as e:
            logger.error(f"Error getting performance dashboard: {e}")
            return {}
    
    @classmethod
    def get_users_dashboard(cls):
        """Get user analytics dashboard."""
        try:
            now = timezone.now()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            return {
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(is_active=True).count(),
                'new_users_week': User.objects.filter(date_joined__gte=week_ago).count(),
                'new_users_month': User.objects.filter(date_joined__gte=month_ago).count(),
                'users_by_type': dict(
                    User.objects.values('user_type').annotate(count=Count('id')).values_list('user_type', 'count')
                ),
                'blocked_users': User.objects.filter(is_blocked=True).count(),
                'admin_users': User.objects.filter(user_type='admin').count(),
                'staff_users': User.objects.filter(user_type='staff').count(),
                'borrower_users': User.objects.filter(user_type='borrower').count(),
            }
        except Exception as e:
            logger.error(f"Error getting users dashboard: {e}")
            return {}
    
    @classmethod
    def get_circulation_dashboard(cls):
        """Get circulation analytics dashboard."""
        try:
            now = timezone.now()
            
            active_loans = Loan.objects.filter(status='active')
            overdue_loans = active_loans.filter(due_date__lt=now)
            returned_loans = Loan.objects.filter(status='returned')
            
            return {
                'active_loans': active_loans.count(),
                'overdue_loans': overdue_loans.count(),
                'total_returned': returned_loans.count(),
                'avg_checkout_duration_days': cls._calculate_avg_loan_duration(),
                'holds_waiting': Hold.objects.filter(status='waiting').count(),
                'holds_fulfilled': Hold.objects.filter(status='fulfilled').count(),
                'notifications_pending': Notification.objects.filter(is_read=False).count(),
                'notifications_read': Notification.objects.filter(is_read=True).count(),
                'recent_activity_24h': Loan.objects.filter(
                    checkout_date__gte=now - timedelta(days=1)
                ).count(),
            }
        except Exception as e:
            logger.error(f"Error getting circulation dashboard: {e}")
            return {}
    
    @classmethod
    def get_system_health(cls):
        """Get overall system health status."""
        try:
            from elibrary.metrics import MetricsCollector
            
            collector = MetricsCollector()
            request_metrics = collector.get_request_metrics(minutes=60)
            error_metrics = collector.get_error_metrics(minutes=60)
            
            # Calculate health score (0-100)
            error_rate = error_metrics.get('error_rate', 0)
            
            if error_rate < 1:
                health_score = 95
                status = 'excellent'
            elif error_rate < 5:
                health_score = 85
                status = 'good'
            elif error_rate < 10:
                health_score = 70
                status = 'acceptable'
            else:
                health_score = 50
                status = 'poor'
            
            return {
                'status': status,
                'health_score': health_score,
                'error_rate': round(error_rate, 2),
                'avg_response_time_ms': round(request_metrics.get('avg_response_time_ms', 0), 2),
                'total_requests_hour': request_metrics.get('total_requests', 0),
                'timestamp': timezone.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {'status': 'unknown', 'health_score': 0}
    
    @staticmethod
    def _format_endpoint_stats(endpoint_list):
        """Format endpoint statistics for display."""
        return [
            {
                'path': path,
                'avg_ms': round(stats['avg_ms'], 2),
                'count': stats['count'],
            }
            for path, stats in endpoint_list
        ]
    
    @staticmethod
    def _calculate_avg_loan_duration():
        """Calculate average loan duration in days."""
        try:
            returned_loans = Loan.objects.filter(
                status='returned',
                return_date__isnull=False
            )
            
            if not returned_loans.exists():
                return 0
            
            total_days = 0
            count = 0
            
            for loan in returned_loans[:100]:  # Sample for performance
                duration = (loan.return_date - loan.checkout_date).days
                total_days += duration
                count += 1
            
            return round(total_days / count, 1) if count > 0 else 0
        except Exception:
            return 0


class TrendAnalyzer:
    """Analyze trends in metrics over time."""
    
    @staticmethod
    def get_request_trends(hours=24):
        """Get request rate trends over time."""
        collector = MetricsCollector()
        metrics = cache.get('metrics:queue:requests', [])
        
        if not metrics:
            return []
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        recent = [
            m for m in metrics
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        # Bucket requests by hour
        hourly_buckets = {}
        for metric in recent:
            ts = datetime.fromisoformat(metric['timestamp'])
            hour_key = ts.strftime('%Y-%m-%d %H:00')
            
            if hour_key not in hourly_buckets:
                hourly_buckets[hour_key] = {'count': 0, 'total_time': 0}
            
            hourly_buckets[hour_key]['count'] += 1
            hourly_buckets[hour_key]['total_time'] += metric['response_time_ms']
        
        # Format for display
        trends = []
        for hour, data in sorted(hourly_buckets.items()):
            trends.append({
                'timestamp': hour,
                'request_count': data['count'],
                'avg_response_time': round(data['total_time'] / data['count'], 2),
            })
        
        return trends
    
    @staticmethod
    def get_error_trends(hours=24):
        """Get error rate trends over time."""
        metrics = cache.get('metrics:queue:errors', [])
        
        if not metrics:
            return []
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        recent = [
            m for m in metrics
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        # Bucket errors by hour
        hourly_buckets = {}
        for metric in recent:
            ts = datetime.fromisoformat(metric['timestamp'])
            hour_key = ts.strftime('%Y-%m-%d %H:00')
            
            if hour_key not in hourly_buckets:
                hourly_buckets[hour_key] = 0
            
            hourly_buckets[hour_key] += 1
        
        # Format for display
        trends = []
        for hour, count in sorted(hourly_buckets.items()):
            trends.append({
                'timestamp': hour,
                'error_count': count,
            })
        
        return trends


class AlertingSystem:
    """Alert system for anomalies and SLA violations."""
    
    @staticmethod
    def check_sla_violations():
        """Check for SLA violations."""
        monitor = PerformanceMonitor()
        sla_metrics = monitor.get_sla_metrics(minutes=60)
        
        violations = []
        for path, sla in sla_metrics.get('sla_status', {}).items():
            if sla['status'] == 'poor':
                violations.append({
                    'endpoint': path,
                    'avg_ms': sla['avg_ms'],
                    'threshold_ms': 1000,
                    'status': 'poor',
                })
        
        return violations
    
    @staticmethod
    def check_error_rate_spike():
        """Check for error rate spikes."""
        collector = MetricsCollector()
        error_metrics = collector.get_error_metrics(minutes=5)
        
        error_rate = error_metrics.get('error_rate', 0)
        
        if error_rate > 10:  # More than 10% errors
            return {
                'alert': 'error_spike',
                'error_rate': error_rate,
                'threshold': 10,
                'severity': 'high' if error_rate > 20 else 'medium',
            }
        
        return None
    
    @staticmethod
    def check_cache_misses():
        """Check for unusual cache miss rates."""
        collector = MetricsCollector()
        cache_metrics = collector.get_cache_metrics(minutes=60)
        
        hit_rate = cache_metrics.get('hit_rate', 0)
        
        if hit_rate < 50:  # Less than 50% hit rate
            return {
                'alert': 'low_cache_hit_rate',
                'hit_rate': hit_rate,
                'threshold': 50,
                'severity': 'medium',
            }
        
        return None
    
    @staticmethod
    def get_active_alerts():
        """Get all active alerts."""
        alerts = []
        
        sla_violations = AlertingSystem.check_sla_violations()
        if sla_violations:
            alerts.extend(sla_violations)
        
        error_spike = AlertingSystem.check_error_rate_spike()
        if error_spike:
            alerts.append(error_spike)
        
        cache_alert = AlertingSystem.check_cache_misses()
        if cache_alert:
            alerts.append(cache_alert)
        
        return alerts

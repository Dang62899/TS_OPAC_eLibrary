"""
Metrics collection and aggregation system for monitoring and analytics.
Tracks API performance, error rates, cache effectiveness, and system health.
"""

import time
import logging
from datetime import datetime, timedelta
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Central metrics collection with in-memory aggregation and caching."""
    
    def __init__(self):
        self.metrics_cache_key = 'metrics:aggregated'
        self.retention_minutes = 60
    
    def record_request(self, method, path, status_code, response_time_ms, user_id=None):
        """Record API request metrics."""
        metric = {
            'timestamp': timezone.now().isoformat(),
            'method': method,
            'path': path,
            'status_code': status_code,
            'response_time_ms': response_time_ms,
            'user_id': user_id,
        }
        
        # Store in cache with 60-minute retention
        self._append_to_metrics_queue('requests', metric)
        logger.debug(f"Recorded request: {method} {path} {status_code} ({response_time_ms}ms)")
    
    def record_cache_hit(self, key, hit=True, duration_ms=0):
        """Record cache hit/miss."""
        metric = {
            'timestamp': timezone.now().isoformat(),
            'key': key,
            'hit': hit,
            'duration_ms': duration_ms,
        }
        self._append_to_metrics_queue('cache_ops', metric)
    
    def record_database_query(self, query_type, table, duration_ms, row_count=0):
        """Record database query metrics."""
        metric = {
            'timestamp': timezone.now().isoformat(),
            'query_type': query_type,
            'table': table,
            'duration_ms': duration_ms,
            'row_count': row_count,
        }
        self._append_to_metrics_queue('queries', metric)
    
    def record_error(self, error_type, path, status_code, user_id=None):
        """Record error occurrence."""
        metric = {
            'timestamp': timezone.now().isoformat(),
            'error_type': error_type,
            'path': path,
            'status_code': status_code,
            'user_id': user_id,
        }
        self._append_to_metrics_queue('errors', metric)
        logger.warning(f"Error recorded: {error_type} at {path} ({status_code})")
    
    def _append_to_metrics_queue(self, queue_name, metric):
        """Append metric to in-memory queue."""
        queue_key = f'metrics:queue:{queue_name}'
        queue = cache.get(queue_key, [])
        queue.append(metric)
        
        # Keep only last 1000 items to prevent memory bloat
        if len(queue) > 1000:
            queue = queue[-1000:]
        
        cache.set(queue_key, queue, self.retention_minutes * 60)
    
    def get_request_metrics(self, minutes=60):
        """Get request metrics for specified period."""
        metrics = cache.get('metrics:queue:requests', [])
        
        if not metrics:
            return self._empty_request_metrics()
        
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        recent = [
            m for m in metrics
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        return self._aggregate_request_metrics(recent)
    
    def get_cache_metrics(self, minutes=60):
        """Get cache effectiveness metrics."""
        metrics = cache.get('metrics:queue:cache_ops', [])
        
        if not metrics:
            return {
                'total_operations': 0,
                'hit_rate': 0.0,
                'avg_hit_duration_ms': 0.0,
                'avg_miss_duration_ms': 0.0,
            }
        
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        recent = [
            m for m in metrics
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        hits = [m for m in recent if m.get('hit')]
        misses = [m for m in recent if not m.get('hit')]
        
        return {
            'total_operations': len(recent),
            'hits': len(hits),
            'misses': len(misses),
            'hit_rate': len(hits) / len(recent) * 100 if recent else 0,
            'avg_hit_duration_ms': sum(m['duration_ms'] for m in hits) / len(hits) if hits else 0,
            'avg_miss_duration_ms': sum(m['duration_ms'] for m in misses) / len(misses) if misses else 0,
        }
    
    def get_error_metrics(self, minutes=60):
        """Get error rate and distribution."""
        metrics = cache.get('metrics:queue:errors', [])
        
        if not metrics:
            return {
                'total_errors': 0,
                'errors_by_type': {},
                'errors_by_path': {},
                'error_rate': 0.0,
            }
        
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        recent = [
            m for m in metrics
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        by_type = defaultdict(int)
        by_path = defaultdict(int)
        
        for error in recent:
            by_type[error['error_type']] += 1
            by_path[error['path']] += 1
        
        # Get request count to calculate error rate
        request_metrics = self.get_request_metrics(minutes)
        error_rate = (len(recent) / request_metrics.get('total_requests', 1)) * 100
        
        return {
            'total_errors': len(recent),
            'errors_by_type': dict(by_type),
            'errors_by_path': dict(by_path),
            'error_rate': error_rate,
        }
    
    def _empty_request_metrics(self):
        """Return empty request metrics structure."""
        return {
            'total_requests': 0,
            'requests_by_method': {},
            'requests_by_path': {},
            'requests_by_status': {},
            'avg_response_time_ms': 0,
            'slowest_endpoints': [],
            'fastest_endpoints': [],
        }
    
    def _aggregate_request_metrics(self, metrics):
        """Aggregate request metrics."""
        by_method = defaultdict(int)
        by_path = defaultdict(list)
        by_status = defaultdict(int)
        
        for metric in metrics:
            by_method[metric['method']] += 1
            by_path[metric['path']].append(metric['response_time_ms'])
            by_status[metric['status_code']] += 1
        
        # Calculate per-endpoint stats
        endpoint_stats = {}
        for path, times in by_path.items():
            endpoint_stats[path] = {
                'count': len(times),
                'avg_ms': sum(times) / len(times),
                'min_ms': min(times),
                'max_ms': max(times),
            }
        
        # Get slowest and fastest
        sorted_endpoints = sorted(
            endpoint_stats.items(),
            key=lambda x: x[1]['avg_ms'],
            reverse=True
        )
        
        return {
            'total_requests': len(metrics),
            'requests_by_method': dict(by_method),
            'requests_by_path': {path: len(times) for path, times in by_path.items()},
            'requests_by_status': dict(by_status),
            'avg_response_time_ms': sum(m['response_time_ms'] for m in metrics) / len(metrics),
            'slowest_endpoints': sorted_endpoints[:5],
            'fastest_endpoints': sorted_endpoints[-5:],
            'endpoint_stats': endpoint_stats,
        }
    
    def clear_metrics(self):
        """Clear all collected metrics (for testing)."""
        cache.delete('metrics:queue:requests')
        cache.delete('metrics:queue:cache_ops')
        cache.delete('metrics:queue:queries')
        cache.delete('metrics:queue:errors')
        logger.info("All metrics cleared")


class PerformanceMonitor:
    """Monitor and aggregate performance metrics across the system."""
    
    @staticmethod
    def get_performance_summary(minutes=60):
        """Get comprehensive performance summary."""
        collector = MetricsCollector()
        
        return {
            'timestamp': timezone.now().isoformat(),
            'period_minutes': minutes,
            'requests': collector.get_request_metrics(minutes),
            'cache': collector.get_cache_metrics(minutes),
            'errors': collector.get_error_metrics(minutes),
        }
    
    @staticmethod
    def get_sla_metrics(minutes=60):
        """Calculate SLA compliance metrics."""
        collector = MetricsCollector()
        request_metrics = collector.get_request_metrics(minutes)
        
        endpoint_stats = request_metrics.get('endpoint_stats', {})
        
        # Define SLA thresholds (in ms)
        sla_thresholds = {
            'excellent': 200,  # <200ms
            'good': 500,       # <500ms
            'acceptable': 1000, # <1000ms
        }
        
        endpoint_sla = {}
        for path, stats in endpoint_stats.items():
            avg_time = stats['avg_ms']
            if avg_time < sla_thresholds['excellent']:
                status = 'excellent'
            elif avg_time < sla_thresholds['good']:
                status = 'good'
            elif avg_time < sla_thresholds['acceptable']:
                status = 'acceptable'
            else:
                status = 'poor'
            
            endpoint_sla[path] = {
                'avg_ms': avg_time,
                'status': status,
                'count': stats['count'],
            }
        
        return {
            'sla_status': endpoint_sla,
            'overall_health': PerformanceMonitor._calculate_overall_health(endpoint_sla),
        }
    
    @staticmethod
    def _calculate_overall_health(endpoint_sla):
        """Calculate overall system health based on SLA."""
        if not endpoint_sla:
            return 'unknown'
        
        statuses = [sla['status'] for sla in endpoint_sla.values()]
        
        excellent_count = statuses.count('excellent')
        good_count = statuses.count('good')
        acceptable_count = statuses.count('acceptable')
        poor_count = statuses.count('poor')
        
        total = len(statuses)
        excellent_pct = (excellent_count + good_count) / total * 100
        
        if excellent_pct >= 90:
            return 'excellent'
        elif excellent_pct >= 75:
            return 'good'
        elif excellent_pct >= 60:
            return 'acceptable'
        else:
            return 'poor'


class RequestLogger:
    """Log request/response details for analytics."""
    
    @staticmethod
    def log_request(request, response, duration_ms):
        """Log request with context."""
        collector = MetricsCollector()
        
        collector.record_request(
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            response_time_ms=duration_ms,
            user_id=request.user.id if request.user.is_authenticated else None,
        )
        
        # Log errors
        if response.status_code >= 400:
            collector.record_error(
                error_type=f'HTTP{response.status_code}',
                path=request.path,
                status_code=response.status_code,
                user_id=request.user.id if request.user.is_authenticated else None,
            )


class MetricsMiddleware:
    """Middleware to automatically collect request metrics."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration_ms = (time.time() - start_time) * 1000
        RequestLogger.log_request(request, response, duration_ms)
        
        return response

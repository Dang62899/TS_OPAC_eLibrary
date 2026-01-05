"""
Caching strategies and utilities for performance optimization.
Implements Redis-based caching with fallback to Django's in-memory cache.
"""

import hashlib
import json
import logging
from functools import wraps
from django.core.cache import cache
from django.conf import settings
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


class CacheManager:
    """Central cache management with TTL control and utilities."""
    
    # Cache TTL configurations (in seconds)
    TTL = {
        'SHORT': 300,        # 5 minutes - for frequently changing data
        'MEDIUM': 1800,      # 30 minutes - for moderately stable data
        'LONG': 3600,        # 1 hour - for stable data
        'VERY_LONG': 86400,  # 1 day - for reference data
    }
    
    # Cache key prefixes for organized namespacing
    PREFIXES = {
        'USER': 'user:',
        'PUBLICATION': 'pub:',
        'ITEM': 'item:',
        'LOAN': 'loan:',
        'HOLD': 'hold:',
        'CIRCULATION': 'circ:',
        'STATS': 'stats:',
        'SEARCH': 'search:',
        'HEALTH': 'health:',
    }
    
    @staticmethod
    def get_cache_key(prefix, identifier, version=None):
        """Generate a consistent cache key."""
        key = f"{prefix}{identifier}"
        if version:
            key = f"{key}:v{version}"
        return key
    
    @staticmethod
    def invalidate_pattern(prefix):
        """Invalidate all keys matching a prefix (requires Redis)."""
        try:
            # This works with Redis backend
            from django.core.cache import cache as django_cache
            if hasattr(django_cache, 'delete_pattern'):
                django_cache.delete_pattern(f"{prefix}*")
                logger.info(f"Invalidated cache pattern: {prefix}*")
        except Exception as e:
            logger.warning(f"Could not invalidate cache pattern {prefix}: {e}")
    
    @staticmethod
    def clear_all():
        """Clear entire cache (use sparingly)."""
        cache.clear()
        logger.warning("Cache cleared completely")


def cache_result(ttl=CacheManager.TTL['MEDIUM'], prefix=None, key_fn=None):
    """
    Decorator to cache function results with automatic key generation.
    
    Args:
        ttl: Time to live in seconds
        prefix: Cache key prefix
        key_fn: Optional custom key function(args, kwargs) -> str
    
    Usage:
        @cache_result(ttl=CacheManager.TTL['LONG'], prefix='user_list')
        def get_active_users():
            return User.objects.filter(is_active=True)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_fn:
                cache_key = key_fn(*args, **kwargs)
            else:
                # Default: function name + args hash
                key_str = f"{func.__name__}_{str(args)}_{str(kwargs)}"
                key_hash = hashlib.md5(key_str.encode()).hexdigest()[:8]
                cache_key = f"{prefix or func.__name__}:{key_hash}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return result
            
            # Cache miss - execute function
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss - cached: {cache_key}")
            return result
        
        return wrapper
    return decorator


def invalidate_cache(prefix=None, keys=None):
    """
    Decorator to invalidate cache after a function executes.
    Used for mutations (create, update, delete operations).
    
    Args:
        prefix: Cache key prefix to invalidate
        keys: List of specific cache keys to invalidate
    
    Usage:
        @invalidate_cache(prefix='user_list:')
        def create_user(self, request):
            # Create user
            return response
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute function
            result = func(*args, **kwargs)
            
            # Invalidate cache
            if prefix:
                CacheManager.invalidate_pattern(prefix)
            if keys:
                for key in keys:
                    cache.delete(key)
            
            return result
        
        return wrapper
    return decorator


class QueryOptimizer:
    """Utilities for optimizing database queries."""
    
    @staticmethod
    def optimize_publication_queryset(qs):
        """
        Apply select_related and prefetch_related optimizations
        to Publication querysets to reduce database hits.
        """
        if not isinstance(qs, QuerySet):
            return qs
        
        return qs.select_related(
            'publication_type',  # One-to-one or foreign key
        ).prefetch_related(
            'authors',           # Many-to-many
            'subjects',          # Many-to-many
            'items',             # Reverse foreign key
        )
    
    @staticmethod
    def optimize_item_queryset(qs):
        """Optimize Item querysets."""
        if not isinstance(qs, QuerySet):
            return qs
        
        return qs.select_related(
            'publication',
            'location',
        ).prefetch_related(
            'loans',
            'holds',
        )
    
    @staticmethod
    def optimize_loan_queryset(qs):
        """Optimize Loan querysets."""
        if not isinstance(qs, QuerySet):
            return qs
        
        return qs.select_related(
            'borrower',
            'item',
            'item__publication',
        ).prefetch_related(
            'notifications',
        )
    
    @staticmethod
    def optimize_hold_queryset(qs):
        """Optimize Hold querysets."""
        if not isinstance(qs, QuerySet):
            return qs
        
        return qs.select_related(
            'borrower',
            'publication',
        )
    
    @staticmethod
    def optimize_user_queryset(qs):
        """Optimize User querysets."""
        if not isinstance(qs, QuerySet):
            return qs
        
        return qs.prefetch_related(
            'loans',
            'holds',
            'notifications',
        )


class StatsCacheManager:
    """Specialized cache management for statistics and analytics."""
    
    @staticmethod
    def get_library_stats(cache_minutes=60):
        """
        Get cached library statistics.
        Includes total items, loans, users, etc.
        """
        cache_key = CacheManager.get_cache_key(
            CacheManager.PREFIXES['STATS'],
            'library_overview'
        )
        
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        from catalog.models import Item, Publication
        from circulation.models import Loan, Hold
        from accounts.models import User
        
        stats = {
            'total_publications': Publication.objects.count(),
            'total_items': Item.objects.count(),
            'available_items': Item.objects.filter(status='available').count(),
            'total_users': User.objects.count(),
            'active_loans': Loan.objects.filter(status='active').count(),
            'active_holds': Hold.objects.filter(status='waiting').count(),
            'overdue_loans': Loan.objects.filter(
                status='active',
                due_date__lt=__import__('django.utils.timezone', fromlist=['now']).now()
            ).count(),
        }
        
        cache.set(cache_key, stats, cache_minutes * 60)
        return stats
    
    @staticmethod
    def invalidate_library_stats():
        """Invalidate library statistics cache."""
        cache_key = CacheManager.get_cache_key(
            CacheManager.PREFIXES['STATS'],
            'library_overview'
        )
        cache.delete(cache_key)


class SearchCacheManager:
    """Specialized cache management for search results."""
    
    @staticmethod
    def get_search_cache_key(query, filters=None, page=1):
        """Generate cache key for search results."""
        key_str = f"search:{query}:{str(filters)}:{page}"
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return CacheManager.get_cache_key(
            CacheManager.PREFIXES['SEARCH'],
            key_hash
        )
    
    @staticmethod
    def cache_search_results(query, results, filters=None, page=1, ttl=CacheManager.TTL['MEDIUM']):
        """Cache search results."""
        cache_key = SearchCacheManager.get_search_cache_key(query, filters, page)
        cache.set(cache_key, results, ttl)
        return cache_key
    
    @staticmethod
    def get_cached_search_results(query, filters=None, page=1):
        """Get cached search results if available."""
        cache_key = SearchCacheManager.get_search_cache_key(query, filters, page)
        return cache.get(cache_key)
    
    @staticmethod
    def invalidate_search_cache():
        """Invalidate all search cache."""
        CacheManager.invalidate_pattern(CacheManager.PREFIXES['SEARCH'])


class PermissionCacheManager:
    """Cache management for permission checks."""
    
    @staticmethod
    def cache_user_permissions(user_id, permissions, ttl=CacheManager.TTL['LONG']):
        """Cache user permissions."""
        cache_key = CacheManager.get_cache_key(
            CacheManager.PREFIXES['USER'],
            f'{user_id}:permissions'
        )
        cache.set(cache_key, permissions, ttl)
    
    @staticmethod
    def get_cached_permissions(user_id):
        """Get cached user permissions."""
        cache_key = CacheManager.get_cache_key(
            CacheManager.PREFIXES['USER'],
            f'{user_id}:permissions'
        )
        return cache.get(cache_key)
    
    @staticmethod
    def invalidate_user_cache(user_id):
        """Invalidate all cache for a specific user."""
        cache.delete(
            CacheManager.get_cache_key(
                CacheManager.PREFIXES['USER'],
                f'{user_id}:permissions'
            )
        )


# Cache warmup utilities for production
def warmup_cache():
    """
    Pre-populate cache with frequently accessed data.
    Call this on application startup or periodically.
    """
    try:
        logger.info("Warming up cache...")
        
        # Pre-cache library statistics
        StatsCacheManager.get_library_stats()
        
        # Pre-cache reference data (publication types, subjects, etc.)
        from catalog.models import PublicationType, Subject
        
        # Cache publication types (rarely change)
        types_key = CacheManager.get_cache_key(
            CacheManager.PREFIXES['PUBLICATION'],
            'types:all'
        )
        cache.set(
            types_key,
            list(PublicationType.objects.all()),
            CacheManager.TTL['VERY_LONG']
        )
        
        # Cache subjects
        subjects_key = CacheManager.get_cache_key(
            CacheManager.PREFIXES['PUBLICATION'],
            'subjects:all'
        )
        cache.set(
            subjects_key,
            list(Subject.objects.all()),
            CacheManager.TTL['VERY_LONG']
        )
        
        logger.info("Cache warmup completed")
    except Exception as e:
        logger.error(f"Cache warmup failed: {e}")

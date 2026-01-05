# Phase 4 Performance Optimization Documentation

## Overview

Phase 4 includes comprehensive performance optimization strategies focusing on:
1. **Query Optimization** - Reduce database hits and N+1 problems
2. **Caching Strategies** - Redis-based caching with intelligent invalidation
3. **Database Indexing** - Strategic indices for frequently used queries
4. **Pagination Optimization** - Efficient handling of large datasets

## 1. Query Optimization

### Problem: N+1 Query Problems

When fetching related data, the ORM can generate many queries:

```python
# ❌ BAD - Generates N+1 queries (1 for publications + N for authors)
publications = Publication.objects.all()
for pub in publications:
    authors = pub.authors.all()  # Database hit for each publication!
```

### Solution: select_related and prefetch_related

```python
# ✅ GOOD - Optimized with prefetch_related (2 queries total)
from elibrary.caching import QueryOptimizer

publications = QueryOptimizer.optimize_publication_queryset(
    Publication.objects.all()
)
# Now fetches publications and all related authors/subjects in just 2 queries
```

### Available Query Optimizers

| Optimizer | Optimizes | Related Fields |
|-----------|-----------|---|
| `optimize_publication_queryset()` | Publications | publication_type, authors, subjects, items |
| `optimize_item_queryset()` | Items | publication, location, loans, holds |
| `optimize_loan_queryset()` | Loans | borrower, item, notifications |
| `optimize_hold_queryset()` | Holds | borrower, publication |
| `optimize_user_queryset()` | Users | loans, holds, notifications |

### Implementation in ViewSets

```python
class PublicationViewSet(viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    
    def get_queryset(self):
        qs = super().get_queryset()
        # Apply optimization automatically
        return QueryOptimizer.optimize_publication_queryset(qs)
```

## 2. Caching Strategy

### Cache Levels and TTL

```python
from elibrary.caching import CacheManager

# Cache TTL configurations
CacheManager.TTL = {
    'SHORT': 300,        # 5 minutes - frequently changing data
    'MEDIUM': 1800,      # 30 minutes - moderately stable data
    'LONG': 3600,        # 1 hour - stable reference data
    'VERY_LONG': 86400,  # 1 day - rarely changing data
}
```

### Cache Key Organization

```python
# Cache keys are organized by prefix for easy invalidation
PREFIXES = {
    'USER': 'user:',
    'PUBLICATION': 'pub:',
    'ITEM': 'item:',
    'LOAN': 'loan:',
    'HOLD': 'hold:',
    'CIRCULATION': 'circ:',
    'STATS': 'stats:',
    'SEARCH': 'search:',
}

# Example: Get a publication cache key
key = CacheManager.get_cache_key(
    CacheManager.PREFIXES['PUBLICATION'],
    'pub_123'
)
# Result: 'pub:pub_123'
```

### Cache Result Decorator

Automatically cache function results:

```python
from elibrary.caching import cache_result, CacheManager

@cache_result(ttl=CacheManager.TTL['LONG'], prefix='user_list')
def get_active_users():
    return User.objects.filter(is_active=True).count()

# First call: Database query executed, result cached
result = get_active_users()  # Hits database

# Second call: Result returned from cache
result = get_active_users()  # Returns from cache
```

### Invalidate Cache Decorator

Automatically invalidate cache after mutations:

```python
from elibrary.caching import invalidate_cache, CacheManager

@invalidate_cache(prefix=CacheManager.PREFIXES['PUBLICATION'])
def create(self, request, *args, **kwargs):
    # After creating a publication, all pub:* cache keys are invalidated
    return super().create(request, *args, **kwargs)
```

### Statistics Cache Management

Pre-calculate and cache library statistics:

```python
from elibrary.caching import StatsCacheManager

# Get cached statistics (or calculate if not cached)
stats = StatsCacheManager.get_library_stats(cache_minutes=60)

# Returns:
# {
#     'total_publications': 1250,
#     'total_items': 3500,
#     'available_items': 2100,
#     'total_users': 450,
#     'active_loans': 320,
#     'active_holds': 45,
#     'overdue_loans': 12,
# }

# Invalidate when data changes
StatsCacheManager.invalidate_library_stats()
```

### Search Results Caching

Cache expensive search queries:

```python
from elibrary.caching import SearchCacheManager

# Check if search results are cached
results = SearchCacheManager.get_cached_search_results(
    query='Python',
    filters={'publication_type': 'Book'},
    page=1
)

if not results:
    # Not cached - execute search
    results = search_publications('Python', filters)
    # Cache the results
    SearchCacheManager.cache_search_results(
        query='Python',
        results=results,
        filters={'publication_type': 'Book'},
        page=1,
        ttl=CacheManager.TTL['MEDIUM']
    )
```

## 3. Database Indexing

### Creating Indices

Recommended indices for production performance:

```sql
-- High Priority Indices (50-80% query improvement)
CREATE INDEX idx_loan_status_due_date ON circulation_loan(status, due_date);
CREATE INDEX idx_item_publication_status ON catalog_item(publication_id, status);
CREATE INDEX idx_loan_borrower_status ON circulation_loan(borrower_id, status);

-- Medium Priority Indices (30-40% improvement)
CREATE INDEX idx_user_active_type ON accounts_user(is_active, user_type);
CREATE INDEX idx_publication_search ON catalog_publication(title, isbn);
CREATE INDEX idx_item_location ON catalog_item(location_id);

-- Additional Indices
CREATE INDEX idx_hold_publication_status ON circulation_hold(publication_id, status);
CREATE INDEX idx_notification_user ON circulation_notification(user_id, is_read);
```

### Automated Index Creation

Use the management command to create all recommended indices:

```bash
# Analyze database and show recommendations
python manage.py optimize_database --analyze

# Create all recommended indices
python manage.py optimize_database --create-indices

# Run all optimizations
python manage.py optimize_database --all
```

### Index Analysis

The `DatabaseIndexAnalyzer` provides:

```python
from elibrary.database_optimization import DatabaseIndexAnalyzer

analyzer = DatabaseIndexAnalyzer()

# Get recommendations
recommendations = analyzer.analyze_slow_queries()
# Returns list of:
# {
#     'table': 'circulation_loan',
#     'columns': ['status', 'due_date'],
#     'reason': 'Frequently filtered by status and sorted by due date',
#     'priority': 'HIGH',
# }

# Get SQL for creating indices
sql_statements = analyzer.get_index_creation_sql()
```

## 4. Pagination Optimization

### Standard Pagination

For datasets up to thousands of records:

```python
from elibrary.database_optimization import PaginationOptimizer

# Get page 3 with 20 items per page
qs = Publication.objects.all().order_by('-date_added')
paginated, max_page = PaginationOptimizer.optimize_pagination_query(
    qs,
    page=3,
    page_size=20
)

# Returns: (paginated_queryset, total_pages)
# Max pages calculated to avoid expensive .count()
```

### Keyset (Cursor) Pagination

For very large datasets, use cursor-based pagination:

```python
# More efficient than offset for large datasets
results, has_next, next_cursor = PaginationOptimizer.keyset_pagination(
    qs=Publication.objects.all(),
    cursor=None,  # None on first page
    limit=20,
    order_by='id'
)

# On next request:
# results, has_next, next_cursor = PaginationOptimizer.keyset_pagination(
#     qs=Publication.objects.all(),
#     cursor=next_cursor,  # Use cursor from previous page
#     limit=20
# )
```

## 5. Bulk Operations

### Bulk Create with Batching

For importing large amounts of data:

```python
from elibrary.database_optimization import BatchOperationOptimizer

items_to_create = [Item(...) for _ in range(10000)]

# Create in batches to avoid memory issues
created = BatchOperationOptimizer.bulk_create_with_batching(
    Item,
    items_to_create,
    batch_size=1000
)
# Creates 10,000 items in 10 batches
```

### Bulk Update with Batching

```python
items_to_update = Item.objects.filter(status='damaged')

# Update status to 'unavailable' in batches
updated = BatchOperationOptimizer.bulk_update_with_batching(
    Item,
    items_to_update,
    fields=['status'],
    batch_size=1000
)
```

## 6. Cache Warmup

Pre-populate cache on application startup:

```python
# In your application startup (e.g., celery task or signal)
from elibrary.caching import warmup_cache

# Call on server startup
warmup_cache()

# Pre-caches:
# - Library statistics
# - Publication types
# - All subjects
# - Reference data
```

## 7. Performance Monitoring

### Query Performance Monitor

Debug query execution (development only):

```python
from elibrary.database_optimization import QueryPerformanceMonitor

# Get total queries executed
query_count = QueryPerformanceMonitor.get_query_count()

# Get slow queries (taking >100ms)
slow = QueryPerformanceMonitor.get_slow_queries(threshold_ms=100)

# Log statistics
QueryPerformanceMonitor.log_query_stats()
# Output: "Database: 42 queries in 0.543s"
```

### Connection Pool Optimization

```python
from elibrary.database_optimization import ConnectionPoolOptimizer

# Get recommendations for your database
recommendations = ConnectionPoolOptimizer.get_pool_recommendations()

# Already configured in settings.py:
# CONN_MAX_AGE = 600  # Persistent connections
# CONN_HEALTH_CHECKS = True  # Auto-detect stale connections
```

## Implementation Checklist

- [x] Query Optimization (select_related/prefetch_related)
- [x] Cache Strategy (TTL levels, key prefixes)
- [x] Cache Decorators (@cache_result, @invalidate_cache)
- [x] Statistics Caching
- [x] Search Result Caching
- [x] Database Index Recommendations
- [x] Automated Index Creation
- [x] Bulk Operation Utilities
- [x] Pagination Optimization
- [x] Cache Warmup
- [x] Performance Monitoring
- [ ] Production Testing & Monitoring
- [ ] Metrics Collection & Analytics (Phase 4 - Advanced Monitoring)

## Performance Impact Estimates

| Optimization | Impact | Priority |
|---|---|---|
| Query Optimization (select_related) | 40-60% reduction in queries | **HIGH** |
| Database Indices (composite) | 50-80% faster queries | **HIGH** |
| Cache Layer (publications, users) | 70-90% reduced DB hits | **HIGH** |
| Pagination Optimization | 30-50% faster large queries | **MEDIUM** |
| Bulk Operations | 80-90% faster imports | **MEDIUM** |

## Next Steps

1. **Apply Database Indices** (production)
   ```bash
   python manage.py optimize_database --create-indices
   ```

2. **Monitor Performance** (Phase 4 - Advanced Monitoring)
   - Query timing
   - Cache hit rates
   - Database load
   - API response times

3. **Fine-tune Based on Metrics**
   - Adjust cache TTLs based on data change frequency
   - Add additional indices based on slow query logs
   - Optimize specific endpoints based on usage patterns

## Configuration

All optimization tools are configured in:
- [elibrary/caching.py](elibrary/caching.py) - Caching strategies
- [elibrary/database_optimization.py](elibrary/database_optimization.py) - Database optimization
- [catalog/management/commands/optimize_database.py](catalog/management/commands/optimize_database.py) - Management command

## References

- [Django QuerySet API](https://docs.djangoproject.com/en/stable/ref/models/querysets/)
- [Django select_related and prefetch_related](https://docs.djangoproject.com/en/stable/ref/models/querysets/#select-related)
- [Django Cache Framework](https://docs.djangoproject.com/en/stable/topics/cache/)
- [Database Index Strategy](https://en.wikipedia.org/wiki/Database_index)

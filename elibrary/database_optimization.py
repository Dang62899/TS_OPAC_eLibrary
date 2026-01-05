"""
Database optimization utilities and index management.
Includes query analysis, index recommendations, and performance monitoring.
"""

import logging
from django.db import connection, models
from django.db.models import Count, Q
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class DatabaseIndexAnalyzer:
    """Analyze and recommend database indices for performance."""
    
    @staticmethod
    def analyze_slow_queries():
        """
        Analyze potentially slow queries based on common patterns.
        Returns recommendations for indices.
        """
        recommendations = []
        
        # Recommendation: Index on (status, due_date) for loan queries
        recommendations.append({
            'table': 'circulation_loan',
            'columns': ['status', 'due_date'],
            'reason': 'Frequently filtered by status and sorted by due_date',
            'priority': 'HIGH',
        })
        
        # Recommendation: Index on (publication_id, status) for items
        recommendations.append({
            'table': 'catalog_item',
            'columns': ['publication_id', 'status'],
            'reason': 'Common filter: items by publication status',
            'priority': 'HIGH',
        })
        
        # Recommendation: Index on (borrower_id, status) for user activity
        recommendations.append({
            'table': 'circulation_loan',
            'columns': ['borrower_id', 'status'],
            'reason': 'User dashboard: get active/returned loans',
            'priority': 'HIGH',
        })
        
        # Recommendation: Index on (is_active, user_type) for user filtering
        recommendations.append({
            'table': 'accounts_user',
            'columns': ['is_active', 'user_type'],
            'reason': 'Admin dashboard: filter active users by role',
            'priority': 'MEDIUM',
        })
        
        # Recommendation: Index on search fields
        recommendations.append({
            'table': 'catalog_publication',
            'columns': ['title', 'isbn'],
            'reason': 'Full-text search on title and ISBN',
            'priority': 'MEDIUM',
        })
        
        # Recommendation: Foreign key indices
        recommendations.append({
            'table': 'catalog_item',
            'columns': ['location_id'],
            'reason': 'Foreign key filtering',
            'priority': 'MEDIUM',
        })
        
        return recommendations
    
    @staticmethod
    def get_index_creation_sql():
        """Generate SQL for recommended indices."""
        sql_statements = [
            # High priority indices
            'CREATE INDEX IF NOT EXISTS idx_loan_status_due_date ON circulation_loan(status, due_date);',
            'CREATE INDEX IF NOT EXISTS idx_item_publication_status ON catalog_item(publication_id, status);',
            'CREATE INDEX IF NOT EXISTS idx_loan_borrower_status ON circulation_loan(borrower_id, status);',
            
            # Medium priority indices
            'CREATE INDEX IF NOT EXISTS idx_user_active_type ON accounts_user(is_active, user_type);',
            'CREATE INDEX IF NOT EXISTS idx_publication_search ON catalog_publication(title, isbn);',
            'CREATE INDEX IF NOT EXISTS idx_item_location ON catalog_item(location_id);',
            
            # Additional useful indices
            'CREATE INDEX IF NOT EXISTS idx_hold_publication_status ON circulation_hold(publication_id, status);',
            'CREATE INDEX IF NOT EXISTS idx_loan_item ON circulation_loan(item_id);',
            'CREATE INDEX IF NOT EXISTS idx_notification_user ON circulation_notification(user_id, is_read);',
        ]
        return sql_statements


class QueryPerformanceMonitor:
    """Monitor query performance and identify bottlenecks."""
    
    @staticmethod
    def get_query_count():
        """Get current database query count (development only)."""
        if hasattr(connection, 'queries'):
            return len(connection.queries)
        return None
    
    @staticmethod
    def get_slow_queries(threshold_ms=100):
        """Get queries taking longer than threshold (development only)."""
        if not hasattr(connection, 'queries'):
            return []
        
        slow = [
            q for q in connection.queries
            if float(q.get('time', 0)) > (threshold_ms / 1000)
        ]
        return slow
    
    @staticmethod
    def log_query_stats():
        """Log database query statistics for debugging."""
        if hasattr(connection, 'queries'):
            query_count = len(connection.queries)
            total_time = sum(float(q.get('time', 0)) for q in connection.queries)
            logger.info(f"Database: {query_count} queries in {total_time:.3f}s")


class BatchOperationOptimizer:
    """Optimize bulk operations with batch processing."""
    
    BATCH_SIZE = 1000
    
    @staticmethod
    def bulk_create_with_batching(model, objects, batch_size=None):
        """
        Create multiple objects efficiently using batching.
        Prevents memory issues with large bulk operations.
        """
        batch_size = batch_size or BatchOperationOptimizer.BATCH_SIZE
        created_count = 0
        
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            model.objects.bulk_create(batch, ignore_conflicts=True)
            created_count += len(batch)
            logger.info(f"Bulk created {created_count} {model.__name__} objects")
        
        return created_count
    
    @staticmethod
    def bulk_update_with_batching(model, objects, fields, batch_size=None):
        """
        Update multiple objects efficiently using batching.
        """
        batch_size = batch_size or BatchOperationOptimizer.BATCH_SIZE
        updated_count = 0
        
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            model.objects.bulk_update(batch, fields, batch_size=batch_size)
            updated_count += len(batch)
            logger.info(f"Bulk updated {updated_count} {model.__name__} objects")
        
        return updated_count


class PaginationOptimizer:
    """Optimize pagination queries for large datasets."""
    
    @staticmethod
    def optimize_pagination_query(qs, page, page_size=20):
        """
        Optimize pagination with efficient offset calculation.
        For large page numbers, use keyset pagination instead.
        """
        total_count = qs.count()
        max_page = (total_count + page_size - 1) // page_size
        
        if page > max_page:
            return qs.none(), max_page
        
        offset = (page - 1) * page_size
        paginated = qs[offset:offset + page_size]
        
        return paginated, max_page
    
    @staticmethod
    def keyset_pagination(qs, cursor=None, limit=20, order_by='id'):
        """
        Implement keyset (cursor-based) pagination for better performance
        with large datasets. More efficient than offset-based pagination.
        """
        if cursor:
            # Assume cursor is the ordering field value
            qs = qs.filter(**{f'{order_by}__gt': cursor})
        
        results = list(qs.order_by(order_by)[:limit + 1])
        has_next = len(results) > limit
        
        if has_next:
            results = results[:limit]
            next_cursor = getattr(results[-1], order_by)
        else:
            next_cursor = None
        
        return results, has_next, next_cursor


# Management command for creating indices
class Command(BaseCommand):
    """Django management command: python manage.py create_database_indices"""
    
    help = 'Create recommended database indices for performance optimization'
    
    def handle(self, *args, **options):
        analyzer = DatabaseIndexAnalyzer()
        recommendations = analyzer.analyze_slow_queries()
        sql_statements = analyzer.get_index_creation_sql()
        
        self.stdout.write(self.style.SUCCESS('Database Index Recommendations:'))
        self.stdout.write('-' * 80)
        
        for rec in recommendations:
            self.stdout.write(f"\nTable: {rec['table']}")
            self.stdout.write(f"Columns: {', '.join(rec['columns'])}")
            self.stdout.write(f"Reason: {rec['reason']}")
            self.stdout.write(f"Priority: {rec['priority']}")
        
        self.stdout.write(self.style.SUCCESS('\n\nSQL Statements to Execute:'))
        self.stdout.write('-' * 80)
        for sql in sql_statements:
            self.stdout.write(f"\n{sql}")
        
        # Option to create indices automatically
        if options.get('create'):
            from django.db import connection
            with connection.cursor() as cursor:
                for sql in sql_statements:
                    try:
                        cursor.execute(sql)
                        self.stdout.write(self.style.SUCCESS(f"✓ Created: {sql.split('ON')[0]}"))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"⚠ Failed: {sql}\n  Error: {e}"))
            
            self.stdout.write(self.style.SUCCESS('\n✓ Index creation completed'))


class ConnectionPoolOptimizer:
    """Optimize database connection pooling and persistence."""
    
    @staticmethod
    def get_pool_recommendations():
        """Return connection pool optimization recommendations."""
        recommendations = {
            'CONN_MAX_AGE': {
                'recommended': 600,  # 10 minutes
                'rationale': 'Persistent connections reduce overhead',
            },
            'CONN_HEALTH_CHECKS': {
                'recommended': True,
                'rationale': 'Auto-detect stale connections',
            },
            'AUTOCOMMIT': {
                'recommended': True,
                'rationale': 'Better control over transactions',
            },
        }
        return recommendations


# Database statistics utilities
def get_table_statistics():
    """Get statistics about database tables."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                name,
                COUNT(*) as row_count
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        results = cursor.fetchall()
    
    stats = {}
    for table_name, row_count in results:
        stats[table_name] = row_count
    
    return stats

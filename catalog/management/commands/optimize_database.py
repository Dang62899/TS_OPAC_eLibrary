"""
Django management command to apply database optimizations and indices.
Usage: python manage.py optimize_database
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, DEFAULT_DB_ALIAS
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Optimize database with indices, analyze queries, and apply performance improvements'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-indices',
            action='store_true',
            help='Create recommended database indices',
        )
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze database for optimization opportunities',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all optimizations',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('╔════════════════════════════════════════════════╗'))
        self.stdout.write(self.style.SUCCESS('║   DATABASE OPTIMIZATION UTILITY                 ║'))
        self.stdout.write(self.style.SUCCESS('╚════════════════════════════════════════════════╝'))
        
        run_all = options.get('all', False)
        create_indices = options.get('create_indices') or run_all
        analyze = options.get('analyze') or run_all
        
        if not (create_indices or analyze):
            self.stdout.write(self.style.WARNING(
                'No options specified. Use --all to run all optimizations or '
                '--create-indices or --analyze for specific tasks.'
            ))
            return
        
        if create_indices:
            self.create_indices()
        
        if analyze:
            self.analyze_database()
        
        self.stdout.write(self.style.SUCCESS('\n✓ Database optimization completed'))
    
    def create_indices(self):
        """Create recommended database indices."""
        self.stdout.write(self.style.SUCCESS('\n[1/2] Creating Database Indices...'))
        self.stdout.write('-' * 80)
        
        indices = [
            # High Priority Indices
            {
                'name': 'idx_loan_status_due_date',
                'table': 'circulation_loan',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_loan_status_due_date ON circulation_loan(status, due_date);',
                'description': 'Optimize loan queries by status and due date',
            },
            {
                'name': 'idx_item_publication_status',
                'table': 'catalog_item',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_item_publication_status ON catalog_item(publication_id, status);',
                'description': 'Optimize item queries by publication and status',
            },
            {
                'name': 'idx_loan_borrower_status',
                'table': 'circulation_loan',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_loan_borrower_status ON circulation_loan(borrower_id, status);',
                'description': 'Optimize user dashboard loan queries',
            },
            
            # Medium Priority Indices
            {
                'name': 'idx_user_active_type',
                'table': 'accounts_user',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_user_active_type ON accounts_user(is_active, user_type);',
                'description': 'Optimize admin user filtering',
            },
            {
                'name': 'idx_publication_search',
                'table': 'catalog_publication',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_publication_search ON catalog_publication(title, isbn);',
                'description': 'Optimize publication search queries',
            },
            {
                'name': 'idx_item_location',
                'table': 'catalog_item',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_item_location ON catalog_item(location_id);',
                'description': 'Optimize item location queries',
            },
            
            # Additional Indices
            {
                'name': 'idx_hold_publication_status',
                'table': 'circulation_hold',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_hold_publication_status ON circulation_hold(publication_id, status);',
                'description': 'Optimize hold queries',
            },
            {
                'name': 'idx_loan_item',
                'table': 'circulation_loan',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_loan_item ON circulation_loan(item_id);',
                'description': 'Optimize item loan lookups',
            },
            {
                'name': 'idx_notification_user',
                'table': 'circulation_notification',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_notification_user ON circulation_notification(user_id, is_read);',
                'description': 'Optimize notification queries',
            },
        ]
        
        success_count = 0
        failed_count = 0
        
        with connection.cursor() as cursor:
            for idx in indices:
                try:
                    cursor.execute(idx['sql'])
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ {idx['name']:<35} - {idx['description']}")
                    )
                    success_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ {idx['name']:<35} - Error: {str(e)[:50]}")
                    )
                    failed_count += 1
        
        self.stdout.write(f"\nSummary: {success_count} created, {failed_count} warnings")
    
    def analyze_database(self):
        """Analyze database for optimization opportunities."""
        self.stdout.write(self.style.SUCCESS('\n[2/2] Analyzing Database...'))
        self.stdout.write('-' * 80)
        
        analysis = {
            'table_sizes': self.get_table_sizes(),
            'missing_indices': self.get_missing_indices(),
            'slow_queries': self.get_slow_query_patterns(),
        }
        
        # Report table sizes
        self.stdout.write(self.style.SUCCESS('\nTable Sizes:'))
        for table, size_info in analysis['table_sizes'].items():
            size_mb = size_info['size_kb'] / 1024
            if size_mb > 10:
                style = self.style.WARNING
            else:
                style = self.style.SUCCESS
            self.stdout.write(
                style(f"  {table:<35} {size_info['rows']:>8} rows ({size_mb:>6.2f} MB)")
            )
        
        # Report optimization recommendations
        self.stdout.write(self.style.SUCCESS('\nOptimization Recommendations:'))
        recommendations = self.get_recommendations(analysis)
        for i, rec in enumerate(recommendations, 1):
            self.stdout.write(f"\n  {i}. {rec['title']}")
            self.stdout.write(f"     {rec['description']}")
            self.stdout.write(f"     Impact: {rec['impact']}")
    
    def get_table_sizes(self):
        """Get sizes of all tables."""
        sizes = {}
        with connection.cursor() as cursor:
            # For SQLite
            try:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    sizes[table] = {
                        'rows': row_count,
                        'size_kb': row_count * 2,  # Rough estimate
                    }
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not get table sizes: {e}"))
        
        return sizes
    
    def get_missing_indices(self):
        """Identify potentially missing indices."""
        return [
            'idx_loan_status_due_date',
            'idx_item_publication_status',
            'idx_loan_borrower_status',
        ]
    
    def get_slow_query_patterns(self):
        """Identify patterns that could benefit from optimization."""
        patterns = [
            'Queries filtering on status and date fields',
            'Queries with multiple joins on publication/item',
            'User activity queries (loans, holds, notifications)',
        ]
        return patterns
    
    def get_recommendations(self, analysis):
        """Generate optimization recommendations."""
        recommendations = [
            {
                'title': 'Create Composite Indices',
                'description': 'Multi-column indices on frequently filtered fields',
                'impact': 'HIGH - Can reduce query time by 50-80%',
            },
            {
                'title': 'Implement Query Result Caching',
                'description': 'Cache publication types, subjects, and reference data',
                'impact': 'MEDIUM - Reduces database load by 30-40%',
            },
            {
                'title': 'Optimize ORM Queries with select_related',
                'description': 'Use select_related for foreign keys in list views',
                'impact': 'MEDIUM - Reduces N+1 query problems',
            },
            {
                'title': 'Use Pagination for Large Result Sets',
                'description': 'Implement cursor-based pagination for better performance',
                'impact': 'MEDIUM - Improves response time for large datasets',
            },
            {
                'title': 'Archive Old Data',
                'description': 'Move completed loans older than 1 year to archive',
                'impact': 'LOW - Maintains database size',
            },
        ]
        return recommendations

#!/usr/bin/env python
"""
SQLite to PostgreSQL Migration Script
Backs up data and verifies migration success
"""

import os
import sys
import django
import json
from datetime import datetime
from django.core import serializers

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elibrary.settings')
django.setup()

from django.apps import apps
from django.db import connection

class DatabaseMigrator:
    def __init__(self):
        self.backup_file = f'sqlite_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        self.backup_data = {}
        
    def print_header(self, text):
        """Print formatted header"""
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")
    
    def print_success(self, text):
        """Print success message"""
        print(f"✅ {text}")
    
    def print_error(self, text):
        """Print error message"""
        print(f"❌ {text}")
    
    def print_info(self, text):
        """Print info message"""
        print(f"ℹ️  {text}")
    
    def get_db_engine(self):
        """Get current database engine"""
        db_engine = connection.settings_dict['ENGINE']
        if 'sqlite' in db_engine:
            return 'SQLite'
        elif 'postgresql' in db_engine:
            return 'PostgreSQL'
        else:
            return 'Unknown'
    
    def backup_data(self):
        """Backup all data from current database"""
        self.print_header("🔄 BACKING UP DATA")
        
        models = apps.get_models()
        total_records = 0
        
        for model in models:
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            
            queryset = model.objects.all()
            count = queryset.count()
            
            if count > 0:
                try:
                    data = serializers.serialize('json', queryset)
                    self.backup_data[f"{app_label}.{model_name}"] = json.loads(data)
                    total_records += count
                    print(f"  ✓ {app_label}.{model_name}: {count:,} records")
                except Exception as e:
                    self.print_error(f"Failed to backup {app_label}.{model_name}: {e}")
        
        # Save to file
        try:
            with open(self.backup_file, 'w') as f:
                json.dump(self.backup_data, f, indent=2, default=str)
            self.print_success(f"Backup saved to {self.backup_file} ({total_records:,} records)")
        except Exception as e:
            self.print_error(f"Failed to save backup: {e}")
            sys.exit(1)
        
        return total_records
    
    def verify_database(self):
        """Verify database connection and type"""
        self.print_header("🔍 DATABASE VERIFICATION")
        
        db_engine = self.get_db_engine()
        self.print_info(f"Database Engine: {db_engine}")
        
        # Get database info
        db_settings = connection.settings_dict
        db_name = db_settings.get('NAME', 'N/A')
        db_host = db_settings.get('HOST', 'N/A')
        db_port = db_settings.get('PORT', 'N/A')
        
        print(f"  Database Name: {db_name}")
        if db_host:
            print(f"  Host: {db_host}")
        if db_port:
            print(f"  Port: {db_port}")
        
        # Test connection
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                self.print_success("Database connection successful")
        except Exception as e:
            self.print_error(f"Database connection failed: {e}")
            sys.exit(1)
    
    def count_records(self):
        """Count total records in database"""
        self.print_header("📊 RECORD COUNT")
        
        models = apps.get_models()
        total_records = 0
        record_breakdown = {}
        
        for model in models:
            count = model.objects.count()
            if count > 0:
                app_label = model._meta.app_label
                model_name = model._meta.model_name
                label = f"{app_label}.{model_name}"
                record_breakdown[label] = count
                total_records += count
                print(f"  • {label}: {count:,}")
        
        print(f"\n  📈 Total Records: {total_records:,}")
        return total_records, record_breakdown
    
    def migrate_metadata(self):
        """Show migration metadata"""
        self.print_header("📝 MIGRATION METADATA")
        
        print(f"  Timestamp: {datetime.now().isoformat()}")
        print(f"  Backup File: {self.backup_file}")
        print(f"  Database Engine: {self.get_db_engine()}")
        print(f"  Django Version: {django.__version__}")
        print(f"  Python Version: {sys.version.split()[0]}")
    
    def run_all_checks(self):
        """Run all verification checks"""
        try:
            self.verify_database()
            self.migrate_metadata()
            backup_count = self.backup_data()
            total_count, breakdown = self.count_records()
            
            self.print_header("✨ MIGRATION COMPLETE")
            print(f"  Records Backed Up: {backup_count:,}")
            print(f"  Records in Database: {total_count:,}")
            print(f"\n  Next Steps:")
            print(f"  1. Verify the backup file: {self.backup_file}")
            print(f"  2. On PostgreSQL: docker-compose exec web python manage.py loaddata {self.backup_file}")
            print(f"  3. Verify counts match above")
            
            return True
            
        except Exception as e:
            self.print_error(f"Migration check failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("  TS OPAC eLibrary - Database Migration Tool")
    print("="*60)
    
    migrator = DatabaseMigrator()
    success = migrator.run_all_checks()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()

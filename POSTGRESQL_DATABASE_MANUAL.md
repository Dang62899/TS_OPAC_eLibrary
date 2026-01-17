# PostgreSQL Database Manual
## TS_OPAC eLibrary System

**Version:** 1.0  
**Database Engine:** PostgreSQL 14+  
**Date:** January 17, 2026  
**Purpose:** Complete database management and operation guide

---

## Table of Contents
1. [Database Architecture](#database-architecture)
2. [Installation & Setup](#installation--setup)
3. [Database Structure](#database-structure)
4. [User Management](#user-management)
5. [Backup & Recovery](#backup--recovery)
6. [Performance Tuning](#performance-tuning)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Database Architecture

### Schema Overview

```
opac_db
├── accounts (User Management)
│   ├── accounts_user
│   │   ├── id (PK)
│   │   ├── username (UNIQUE)
│   │   ├── email
│   │   ├── password_hash
│   │   ├── first_name
│   │   ├── last_name
│   │   ├── is_active
│   │   └── created_at
│   └── auth_tokens
│
├── catalog (Publication Management)
│   ├── catalog_publication
│   │   ├── id (PK)
│   │   ├── title
│   │   ├── subtitle
│   │   ├── publication_type_id (FK)
│   │   ├── publisher_id (FK)
│   │   ├── isbn
│   │   ├── publication_date
│   │   ├── pages
│   │   ├── abstract
│   │   └── date_added
│   │
│   ├── catalog_publicationtype
│   │   ├── id (PK)
│   │   ├── name (Manual, SOP, Capstone Project, TTP)
│   │   ├── code
│   │   └── description
│   │
│   ├── catalog_item
│   │   ├── id (PK)
│   │   ├── publication_id (FK)
│   │   ├── barcode (UNIQUE)
│   │   ├── location_id (FK)
│   │   ├── status (available, checked_out, in_repair)
│   │   ├── condition
│   │   └── acquisition_date
│   │
│   ├── catalog_author
│   │   ├── id (PK)
│   │   ├── first_name
│   │   ├── last_name
│   │   └── bio
│   │
│   ├── catalog_subject
│   │   ├── id (PK)
│   │   ├── name
│   │   └── description
│   │
│   ├── catalog_publisher
│   │   ├── id (PK)
│   │   ├── name
│   │   └── website
│   │
│   └── catalog_location
│       ├── id (PK)
│       ├── name
│       ├── building
│       └── floor
│
├── circulation (Loan Management)
│   ├── circulation_loan
│   │   ├── id (PK)
│   │   ├── user_id (FK)
│   │   ├── item_id (FK)
│   │   ├── checkout_date
│   │   ├── due_date
│   │   ├── return_date
│   │   └── status
│   │
│   ├── circulation_hold
│   │   ├── id (PK)
│   │   ├── user_id (FK)
│   │   ├── publication_id (FK)
│   │   ├── hold_date
│   │   └── position
│   │
│   ├── circulation_notification
│   │   ├── id (PK)
│   │   ├── user_id (FK)
│   │   ├── type (due_soon, overdue, item_ready)
│   │   ├── sent_date
│   │   └── read_date
│   │
│   └── circulation_checkoutrequest
│       ├── id (PK)
│       ├── user_id (FK)
│       ├── item_id (FK)
│       ├── requested_date
│       └── status
│
└── api (Authentication & Tokens)
    └── authtoken_token
        ├── key (PK)
        ├── user_id (FK)
        └── created
```

### Key Relationships

- **Users** can have multiple **Loans**, **Holds**, and **Notifications**
- **Publications** can have multiple **Items** and **Authors**
- **Items** can have multiple **Loans** and **Checkout Requests**
- **Authors** and **Subjects** are many-to-many with **Publications**

---

## Installation & Setup

### 1. PostgreSQL Installation

#### Ubuntu/Debian

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib postgresql-client

# Verify installation
psql --version
sudo systemctl status postgresql

# Start PostgreSQL service
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

#### macOS

```bash
# Using Homebrew
brew install postgresql

# Start PostgreSQL
brew services start postgresql

# Verify
psql --version
```

#### Windows

```bash
# Download installer from https://www.postgresql.org/download/windows/
# Or use Chocolatey:
choco install postgresql

# Verify
psql --version
```

### 2. Initial Configuration

```bash
# Connect as postgres user
sudo -u postgres psql

# Create new database user
postgres=# CREATE USER opac_user WITH PASSWORD 'strong_password_here';

# Create database
postgres=# CREATE DATABASE opac_db OWNER opac_user;

# Grant privileges
postgres=# GRANT CONNECT ON DATABASE opac_db TO opac_user;
postgres=# GRANT CREATE ON DATABASE opac_db TO opac_user;

# Exit
postgres=# \q
```

### 3. Connect as Application User

```bash
# Test connection
psql -U opac_user -d opac_db -h localhost

# Or with environment variables
export PGHOST=localhost
export PGUSER=opac_user
export PGDATABASE=opac_db
psql

# View connection info
\conninfo
```

### 4. Apply Django Migrations

```bash
cd /path/to/TS_OPAC_eLibrary

# Activate virtual environment
source venv/bin/activate

# Run migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations

# Create superuser
python manage.py createsuperuser
```

---

## Database Structure

### Core Tables Details

#### accounts_user
```sql
CREATE TABLE accounts_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254),
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    password VARCHAR(255) NOT NULL,
    is_staff BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_username ON accounts_user(username);
CREATE INDEX idx_user_email ON accounts_user(email);
```

#### catalog_publication
```sql
CREATE TABLE catalog_publication (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(255),
    publication_type_id INTEGER REFERENCES catalog_publicationtype(id),
    publisher_id INTEGER REFERENCES catalog_publisher(id),
    isbn VARCHAR(20),
    normalized_isbn VARCHAR(20) UNIQUE,
    publication_date DATE,
    edition VARCHAR(50),
    language VARCHAR(50),
    pages INTEGER,
    abstract TEXT,
    summary TEXT,
    cover_image VARCHAR(200),
    call_number VARCHAR(50) UNIQUE,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pub_title ON catalog_publication(title);
CREATE INDEX idx_pub_type ON catalog_publication(publication_type_id);
CREATE INDEX idx_pub_isbn ON catalog_publication(normalized_isbn);
CREATE INDEX idx_pub_call_number ON catalog_publication(call_number);
```

#### catalog_item
```sql
CREATE TABLE catalog_item (
    id SERIAL PRIMARY KEY,
    publication_id INTEGER NOT NULL REFERENCES catalog_publication(id),
    barcode VARCHAR(50) UNIQUE NOT NULL,
    location_id INTEGER REFERENCES catalog_location(id),
    status VARCHAR(20) DEFAULT 'available',
    condition VARCHAR(20) DEFAULT 'good',
    notes TEXT,
    acquisition_date DATE,
    price DECIMAL(10,2),
    times_borrowed INTEGER DEFAULT 0,
    last_borrowed_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_item_barcode ON catalog_item(barcode);
CREATE INDEX idx_item_status ON catalog_item(status);
CREATE INDEX idx_item_publication ON catalog_item(publication_id);
```

### View Creation for Reports

```sql
-- Recently Added Publications
CREATE VIEW v_recent_publications AS
SELECT 
    p.title,
    pt.name as type,
    p.publication_date,
    COUNT(i.id) as item_count
FROM catalog_publication p
LEFT JOIN catalog_publicationtype pt ON p.publication_type_id = pt.id
LEFT JOIN catalog_item i ON p.id = i.publication_id
WHERE p.date_added > CURRENT_DATE - INTERVAL '30 days'
GROUP BY p.id, p.title, pt.name, p.publication_date
ORDER BY p.date_added DESC;

-- Availability Statistics
CREATE VIEW v_availability_stats AS
SELECT 
    status,
    COUNT(*) as item_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM catalog_item), 2) as percentage
FROM catalog_item
GROUP BY status;

-- User Activity
CREATE VIEW v_user_activity AS
SELECT 
    u.username,
    COUNT(l.id) as total_loans,
    MAX(l.checkout_date) as last_checkout,
    COUNT(h.id) as active_holds
FROM accounts_user u
LEFT JOIN circulation_loan l ON u.id = l.user_id
LEFT JOIN circulation_hold h ON u.id = h.user_id
GROUP BY u.id, u.username
ORDER BY total_loans DESC;
```

---

## User Management

### 1. Create Database Users

```bash
sudo -u postgres psql -c "CREATE USER opac_user WITH PASSWORD 'password';"
sudo -u postgres psql -c "CREATE USER opac_readonly WITH PASSWORD 'password';"
sudo -u postgres psql -c "CREATE USER opac_backup WITH PASSWORD 'password';"
```

### 2. Assign Roles and Privileges

```bash
sudo -u postgres psql << EOF
-- Grant schema access
GRANT USAGE ON SCHEMA public TO opac_user;
GRANT CREATE ON SCHEMA public TO opac_user;

-- Grant table privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO opac_user;

-- Read-only user
GRANT CONNECT ON DATABASE opac_db TO opac_readonly;
GRANT USAGE ON SCHEMA public TO opac_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO opac_readonly;

-- Backup user
GRANT CONNECT ON DATABASE opac_db TO opac_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO opac_backup;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO opac_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO opac_readonly;
EOF
```

### 3. Manage User Passwords

```bash
# Change password
sudo -u postgres psql -c "ALTER USER opac_user WITH PASSWORD 'new_password';"

# View users
sudo -u postgres psql -c "\du"

# Drop user (if no active connections)
sudo -u postgres psql -c "DROP USER opac_user;"
```

---

## Backup & Recovery

### 1. Full Database Backup

```bash
# Backup entire database
pg_dump -U opac_user -d opac_db -F c -b -v -f opac_db_backup.dump

# Backup in SQL format (human-readable)
pg_dump -U opac_user -d opac_db -F p > opac_db_backup.sql

# Compressed backup
pg_dump -U opac_user -d opac_db | gzip > opac_db_backup.sql.gz

# With timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump -U opac_user -d opac_db | gzip > opac_db_backup_$TIMESTAMP.sql.gz
```

### 2. Selective Backup

```bash
# Backup specific tables
pg_dump -U opac_user -d opac_db -t catalog_publication -t catalog_item | gzip > tables_backup.sql.gz

# Backup schema only (no data)
pg_dump -U opac_user -d opac_db -s > schema_only.sql

# Backup data only
pg_dump -U opac_user -d opac_db -a -F c > data_only.dump
```

### 3. Restore from Backup

```bash
# Restore from SQL format
psql -U opac_user -d opac_db < opac_db_backup.sql

# Restore from dump format
pg_restore -U opac_user -d opac_db -v opac_db_backup.dump

# Restore from compressed file
gunzip -c opac_db_backup.sql.gz | psql -U opac_user -d opac_db

# Restore specific table
pg_restore -U opac_user -d opac_db -t catalog_publication opac_db_backup.dump
```

### 4. Point-in-Time Recovery

```bash
# Enable WAL archiving in postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backup/wal_archive/%f'
archive_timeout = 300

# Create recovery point
SELECT pg_create_restore_point('before_migration');

# Recovery: restore backup and replay WAL files up to specific point
```

### 5. Backup Strategy Script

```bash
#!/bin/bash
# backup_strategy.sh

BACKUP_DIR="/backups/postgresql"
RETENTION_DAYS=30
COMPRESS=true

# Create backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/opac_db_$TIMESTAMP.sql"

if [ "$COMPRESS" = true ]; then
    pg_dump -U opac_user -d opac_db | gzip > "$BACKUP_FILE.gz"
else
    pg_dump -U opac_user -d opac_db > "$BACKUP_FILE"
fi

# Verify backup
if [ -f "$BACKUP_FILE.gz" ] || [ -f "$BACKUP_FILE" ]; then
    echo "Backup successful: $BACKUP_FILE"
    
    # Upload to remote storage (optional)
    # scp "$BACKUP_FILE.gz" backup_server:/remote/backups/
else
    echo "Backup failed" >&2
    exit 1
fi

# Remove old backups
find "$BACKUP_DIR" -name "opac_db_*.sql*" -mtime +$RETENTION_DAYS -delete

# Log backup
echo "$(date): Backup completed - $BACKUP_FILE" >> "$BACKUP_DIR/backup.log"
```

```bash
# Schedule automatic backups
crontab -e
# Add: 0 2 * * * /scripts/backup_strategy.sh
```

---

## Performance Tuning

### 1. PostgreSQL Configuration Tuning

```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/15/main/postgresql.conf

# System memory: 32GB
shared_buffers = 8GB                    # 25% of RAM
effective_cache_size = 24GB             # 75% of RAM
maintenance_work_mem = 2GB
work_mem = 50MB

# Connection settings
max_connections = 200
max_prepared_transactions = 100

# WAL settings
wal_buffers = 16MB
checkpoint_completion_target = 0.9
wal_keep_size = 1GB

# Query planner
random_page_cost = 1.1                  # For SSD
effective_io_concurrency = 200

# Logging
log_min_duration_statement = 1000       # Log queries > 1 second
log_connections = on
log_disconnections = on
log_statement = 'all'

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 2. Index Optimization

```sql
-- Analyze table for query planning
ANALYZE catalog_publication;

-- Create indexes for common queries
CREATE INDEX idx_item_status_location ON catalog_item(status, location_id);
CREATE INDEX idx_loan_user_date ON circulation_loan(user_id, checkout_date);
CREATE INDEX idx_publication_type_date ON catalog_publication(publication_type_id, date_added);

-- Reindex table (maintenance)
REINDEX TABLE catalog_publication;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### 3. Query Performance Analysis

```sql
-- Enable query analysis
EXPLAIN ANALYZE SELECT * FROM catalog_publication WHERE publication_type_id = 1;

-- Identify missing indexes
SELECT schemaname, tablename, attname, n_distinct
FROM pg_stats
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY abs(n_distinct) DESC;

-- Monitor slow queries
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
```

### 4. Table Maintenance

```sql
-- Vacuum (remove dead rows)
VACUUM catalog_publication;
VACUUM ANALYZE catalog_publication;

-- Full vacuum (locks table, use off-peak)
VACUUM FULL catalog_publication;

-- Cluster table (sort by index)
CLUSTER catalog_publication USING idx_pub_call_number;
```

---

## Monitoring & Maintenance

### 1. Database Size Monitoring

```sql
-- Database size
SELECT pg_size_pretty(pg_database_size('opac_db'));

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index sizes
SELECT 
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_relation_size(indexrelid) DESC;
```

### 2. Connection Monitoring

```sql
-- Active connections
SELECT 
    datname,
    usename,
    application_name,
    state,
    query_start,
    state_change
FROM pg_stat_activity
WHERE datname = 'opac_db'
ORDER BY query_start;

-- Kill idle connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'opac_db'
  AND pid <> pg_backend_pid()
  AND state = 'idle'
  AND query_start < NOW() - INTERVAL '1 hour';
```

### 3. Replication Monitoring (if configured)

```sql
-- Check replication status
SELECT 
    client_addr,
    usename,
    state,
    sync_priority,
    sync_state
FROM pg_stat_replication;
```

### 4. Maintenance Schedule

```
Weekly:
- VACUUM ANALYZE
- Check slow queries
- Monitor disk space

Monthly:
- REINDEX tables
- Analyze query plans
- Review user privileges

Quarterly:
- Test backup restoration
- Review performance metrics
- Update statistics

Annually:
- Major version upgrade testing
- Comprehensive security audit
- Capacity planning
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Connection Issues

```bash
# Test connection
psql -U opac_user -d opac_db -h localhost

# Check PostgreSQL service
sudo systemctl status postgresql

# Check listen address in postgresql.conf
sudo grep "listen_addresses" /etc/postgresql/15/main/postgresql.conf

# Test TCP connection
telnet localhost 5432
```

#### 2. Disk Space Issues

```sql
-- Check disk usage
SELECT pg_size_pretty(pg_database_size('opac_db'));

-- Identify large tables
SELECT * FROM v_table_sizes ORDER BY size DESC;

-- Clean up temporary files
VACUUM FULL ANALYZE;

-- Archive old data
DELETE FROM circulation_loan WHERE return_date < NOW() - INTERVAL '2 years';
```

#### 3. Slow Queries

```sql
-- Find slow queries
SELECT query, calls, mean_time, max_time
FROM pg_stat_statements
WHERE mean_time > 1000  -- > 1 second
ORDER BY mean_time DESC;

-- Explain query
EXPLAIN ANALYZE SELECT * FROM catalog_publication WHERE title LIKE '%test%';

-- Add missing index
CREATE INDEX idx_publication_title ON catalog_publication(title);
```

#### 4. Lock Issues

```sql
-- Check for locks
SELECT * FROM pg_locks WHERE NOT granted;

-- View blocking queries
SELECT * FROM pg_stat_activity WHERE pg_blocking_pids(pg_stat_activity.pid)::text != '{}';

-- Kill blocking process
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = 12345;
```

#### 5. Memory Issues

```bash
# Check memory usage
ps aux | grep postgres

# Monitor in real-time
top -p $(pgrep -d ',' -f 'postgres:')

# Check shared buffer usage
SELECT * FROM pg_stat_database WHERE datname = 'opac_db';
```

---

## Best Practices

1. **Regular Backups**: Daily full backups, weekly compressed backups
2. **Index Maintenance**: Review indexes monthly, remove unused ones
3. **Statistics**: Run ANALYZE weekly for accurate query planning
4. **Monitoring**: Set up alerts for disk space, connection limits, slow queries
5. **Security**: Use strong passwords, limit user privileges, enable SSL
6. **Documentation**: Keep migration scripts and DDL changes documented
7. **Testing**: Test all backup/restore procedures quarterly
8. **Updates**: Apply security patches promptly

---

**Last Updated:** January 17, 2026  
**Backup Location:** `/backups/postgresql/`  
**Log Location:** `/var/log/postgresql/`  
**Config Location:** `/etc/postgresql/15/main/`

For emergency support or issues, refer to TROUBLESHOOTING.md or PostgreSQL documentation at https://www.postgresql.org/docs/

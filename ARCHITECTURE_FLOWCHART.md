# TS_OPAC eLibrary - System Architecture Flowchart
## Complete System Design & Data Flow Documentation

**Date:** January 17, 2026  
**Version:** 1.0

---

## 1. High-Level System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            OPAC eLibrary System                               │
│                                                                               │
│  ┌──────────────────────┐                    ┌──────────────────────┐       │
│  │   User Interfaces    │                    │   Administration      │       │
│  ├──────────────────────┤                    ├──────────────────────┤       │
│  │ • Web Portal         │                    │ • Admin Dashboard    │       │
│  │ • Mobile App         │                    │ • User Management    │       │
│  │ • Public Catalog     │                    │ • Content Management │       │
│  │ • Search & Browse    │                    │ • Reports & Analytics│       │
│  └──────────────────────┘                    └──────────────────────┘       │
│          │                                              │                    │
│          └──────────────────┬──────────────────────────┘                    │
│                             ▼                                               │
│           ┌────────────────────────────────┐                               │
│           │   Nginx Reverse Proxy / LB     │                               │
│           │   (Port 80, 443)               │                               │
│           └────────────┬───────────────────┘                               │
│                        ▼                                                   │
│           ┌────────────────────────────────┐                               │
│           │  Django Web Application        │                               │
│           │  (Gunicorn WSGI Server)        │                               │
│           │  • REST API Endpoints          │                               │
│           │  • Template Rendering          │                               │
│           │  • Business Logic              │                               │
│           └────────────┬───────────────────┘                               │
│                        ▼                                                   │
│        ┌──────────────────────────────────┐                               │
│        │   Application Services           │                               │
│        ├──────────────────────────────────┤                               │
│        │ • Authentication & Authorization │                               │
│        │ • Search Engine (PostgreSQL FTS) │                               │
│        │ • Notification System            │                               │
│        │ • Caching Layer (Redis/Memcache) │                               │
│        └────────────┬─────────────────────┘                               │
│                     ▼                                                     │
│        ┌────────────────────────────────────┐                             │
│        │  Database Layer                    │                             │
│        ├────────────────────────────────────┤                             │
│        │  PostgreSQL (Primary)              │                             │
│        │  • Catalog Data                    │                             │
│        │  • User Accounts                   │                             │
│        │  • Circulation Records             │                             │
│        │  • Transactions & Logs             │                             │
│        └────────────┬─────────────────────┘                               │
│                     ▼                                                     │
│        ┌────────────────────────────────────┐                             │
│        │  Data Storage & Backups            │                             │
│        ├────────────────────────────────────┤                             │
│        │ • Daily Full Backups               │                             │
│        │ • WAL Archive                      │                             │
│        │ • Remote Replication               │                             │
│        │ • Disaster Recovery                │                             │
│        └────────────────────────────────────┘                             │
│                                                                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. User Request Flow

```
┌─────────────────────┐
│   User Request      │
│   (HTTP/HTTPS)      │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────────┐
    │ Nginx (Port 80)  │
    │ • SSL/TLS Termination
    │ • Load Balancing
    │ • Static Files
    │ • Reverse Proxy
    └──────────┬───────┘
               │
               ▼
    ┌──────────────────────┐
    │  Gunicorn Workers    │
    │  (4 Workers)         │
    │  • Request Parsing   │
    │  • Routing           │
    └──────────┬───────────┘
               │
         ┌─────┴──────┬─────────┬─────────┐
         │            │         │         │
         ▼            ▼         ▼         ▼
    [View]        [Auth]   [Search]  [API]
         │            │         │         │
         └─────┬──────┴─────────┴─────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Django ORM          │
    │  • Query Builder     │
    │  • Connection Pool   │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │  PostgreSQL Database │
    │  • SQL Execution     │
    │  • Transaction Log   │
    │  • Index Lookup      │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Response Data       │
    │  (JSON/HTML)         │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Response Encoding   │
    │  • Compression       │
    │  • Caching Headers   │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │  User Browser        │
    │  • Render Page       │
    │  • Cache Response    │
    └──────────────────────┘
```

---

## 3. Deployment Architecture (Raspberry Pi)

```
┌────────────────────────────────────────────────────────────┐
│                  Raspberry Pi Server                        │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                    OS: Raspberry Pi OS               │ │
│  │                    CPU: ARM (4 Cores)                │ │
│  │                    RAM: 4GB                          │ │
│  │                    Storage: 64GB SD Card             │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ Nginx    │    │ Gunicorn │    │ Supervisor
│  │ :80, :443├───►│ :8000    ├───►│ (daemon)  │            │
│  │          │    │          │    │          │            │
│  └──────────┘    └──────────┘    └──────────┘            │
│       │                │                │                 │
│       ├─Static Files   ├─App Logic      └─Auto Restart   │
│       ├─SSL/TLS        └─ORM                             │
│       └─Caching                                          │
│                                                             │
│  ┌───────────────────────────────────────────────────┐   │
│  │  Application (/srv/opac-elibrary)                │   │
│  │  • Django Project                                │   │
│  │  • Python Virtual Environment                    │   │
│  │  • Cache (Redis/Memcache)                       │   │
│  │  • Logging & Monitoring                         │   │
│  └───────────────────────────────────────────────────┘   │
│                         │                                 │
│                         ▼                                 │
│  ┌───────────────────────────────────────────────────┐   │
│  │  Network Configuration                           │   │
│  │  • IP: 192.168.1.100                             │   │
│  │  • Gateway: 192.168.1.1                          │   │
│  │  • DNS: 8.8.8.8, 8.8.4.4                        │   │
│  │  • Ethernet (Gigabit)                            │   │
│  └───────────────────────────────────────────────────┘   │
│                                                             │
└────────────────────────────────────────────────────────────┘
           │
           │ Network
           ▼
┌────────────────────────────────┐
│  PostgreSQL Server             │
│  (192.168.1.50)               │
│  • Database: opac_db          │
│  • User: opac_user            │
│  • Port: 5432                 │
└────────────────────────────────┘
           │
           ▼
┌────────────────────────────────┐
│  Backup & Replication          │
│  • Daily backups               │
│  • WAL Streaming               │
│  • Remote Replication          │
└────────────────────────────────┘
```

---

## 4. Database Schema Relationships

```
                    ┌─────────────────────────┐
                    │   accounts_user         │
                    │  ┌───────────────────┐  │
                    │  │ id (PK)           │  │
                    │  │ username          │  │
                    │  │ email             │  │
                    │  │ password_hash     │  │
                    │  └───────────────────┘  │
                    └──────────┬──────────────┘
                        ▲      │      ▲
                   ┌────┘      │      └────┐
                   │           │           │
              1:N  │           │      1:N   │
                   ▼           │           ▼
        ┌──────────────────┐   │   ┌──────────────────┐
        │circulation_loan  │   │   │circulation_hold  │
        │┌────────────────┐│   │   │┌────────────────┐│
        ││ id             ││   │   ││ id             ││
        ││ user_id (FK)   ││   │   ││ user_id (FK)   ││
        ││ item_id (FK)   ││   │   ││ pub_id (FK)    ││
        │└────────────────┘│   │   │└────────────────┘│
        └────────┬─────────┘   │   └────────┬─────────┘
                 │   1:N       │            │   N:1
                 │             │            │
            1:N  ▼             │            ▼
        ┌──────────────────────┐       ┌──────────────────────┐
        │  catalog_item        │       │  catalog_publication │
        │┌────────────────────┐│       │┌────────────────────┐│
        ││ id                 ││       ││ id                 ││
        ││ publication_id (FK)││──┐   ││ title              ││
        ││ barcode            ││  │   ││ type_id (FK)       ││
        ││ location_id (FK)   ││  │   ││ publisher_id (FK)  ││
        ││ status             ││  │   ││ isbn               ││
        │└────────────────────┘│  │   │└────────────────────┘│
        └──────────────────────┘  │   └──────────────┬───────┘
                                  │                  │
                           N:1    │                  │ M:N
                                  │          ┌───────┴────────┐
                                  │          │                │
                                  ▼          ▼                ▼
                        ┌──────────────────┐  ┌─────────────────────┐
                        │ catalog_location │  │ catalog_publication_│
                        │┌────────────────┐│  │      authors        │
                        ││ id             ││  │┌───────────────────┐│
                        ││ name           ││  ││ publication_id    ││
                        ││ building       ││  ││ author_id         ││
                        ││ floor          ││  │└───────────────────┘│
                        │└────────────────┘│  └─────────────────────┘
                        └──────────────────┘          │
                                                      │ N:1
                                                      ▼
                                                ┌─────────────────┐
                                                │ catalog_author  │
                                                │┌───────────────┐│
                                                ││ id            ││
                                                ││ first_name    ││
                                                ││ last_name     ││
                                                ││ bio           ││
                                                │└───────────────┘│
                                                └─────────────────┘


    ┌──────────────────────────────┐        ┌──────────────────────────┐
    │ catalog_publication_subjects │        │ catalog_publicationtype  │
    │ ┌──────────────────────────┐ │        │ ┌──────────────────────┐ │
    │ │ publication_id   (PK,FK) │ │        │ │ id                  │ │
    │ │ subject_id       (PK,FK) │─┼───────►│ │ name                │ │
    │ └──────────────────────────┘ │        │ │ (Manual, SOP, etc)  │ │
    │          ▲                    │        │ └──────────────────────┘ │
    │          │ N:1                │        └──────────────────────────┘
    │          │                    │
    │     ┌────┴─────────┐          │
    │     │              │          │
    │     └──────────────┴──────────┘
    │
    │ N:M
    │
    ▼
┌──────────────────┐        ┌──────────────────────┐
│ catalog_subject  │        │ catalog_publisher    │
│┌────────────────┐│        │┌──────────────────────┐
││ id             ││        ││ id                   ││
││ name           ││        ││ name                 ││
││ description    ││        ││ website              ││
│└────────────────┘│        │└──────────────────────┘
└──────────────────┘        └──────────────────────┘
```

---

## 5. Circulation Process Flow

```
START
  │
  ▼
┌──────────────────────┐
│  User Browses        │
│  Catalog             │
└──────────┬───────────┘
           │
           ▼
      ┌─────────────┐
      │ Item Found? │
      └─────┬───┬───┘
            │   │
       Yes  │   │ No ─► Back to Browse
            │   │
            ▼   │
      ┌──────────────────┐
      │ Item Available?  │
      └─────┬───┬────────┘
            │   │
       Yes  │   │ No ─► Place Hold / View Details
            │   │
            ▼   │
      ┌──────────────────┐
      │ Add to Checkout  │
      │ Request          │
      └──────────┬───────┘
                 │
                 ▼
      ┌──────────────────┐
      │ Verify User      │
      │ Eligibility      │
      └─────┬───┬────────┘
            │   │
       Pass │   │ Fail ─► Deny Checkout
            │   │
            ▼   │
      ┌──────────────────┐
      │ System Creates   │
      │ Loan Record      │
      │ • checkout_date  │
      │ • due_date       │
      │ • status: active │
      └──────────┬───────┘
                 │
                 ▼
      ┌──────────────────┐
      │ Update Item      │
      │ Status:          │
      │ available ──►    │
      │ checked_out      │
      └──────────┬───────┘
                 │
                 ▼
      ┌──────────────────┐
      │ Send             │
      │ Notification     │
      │ (Email/SMS)      │
      └──────────┬───────┘
                 │
                 ▼
      ┌──────────────────┐
      │ User Receives    │
      │ Item             │
      └──────────┬───────┘
                 │
                 ▼
      ┌──────────────────┐
      │ Due Date         │
      │ Reminder (7 days)│
      └──────────┬───────┘
                 │
    ┌────┬───────┴─────────┐
    │    │                 │
    │    ▼                 ▼
    │  Return         Overdue
    │    │              │
    │    ▼              ▼
    │ ┌──────────────────────────┐
    │ │ Send Renewal/Overdue     │
    │ │ Notification             │
    │ └──────┬───────────────────┘
    │        │
    └────┬───┘
         │
         ▼
    ┌──────────────────┐
    │ Item Returned    │
    └──────────┬───────┘
               │
               ▼
    ┌──────────────────┐
    │ Update Loan      │
    │ status: returned │
    │ return_date: now │
    └──────────┬───────┘
               │
               ▼
    ┌──────────────────┐
    │ Update Item      │
    │ checked_out ──►  │
    │ available        │
    └──────────┬───────┘
               │
               ▼
    ┌──────────────────┐
    │ Check Holds      │
    │ Queue            │
    └─────┬───┬────────┘
          │   │
     Yes  │   │ No
          │   │
          ▼   │
    ┌──────────────────┐
    │ Notify Next      │
    │ User in Queue    │
    └──────────┬───────┘
               │
               ▼
    ┌──────────────────┐
    │ Send Completion  │
    │ Notification     │
    │ (Email Receipt)  │
    └──────────┬───────┘
               │
               ▼
             END
```

---

## 6. Search & Query Flow

```
         User Search Request
               │
               ▼
    ┌──────────────────────┐
    │ Input Validation     │
    │ • Query string       │
    │ • Filters            │
    │ • Pagination         │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Build Query          │
    │ WHERE clause:        │
    │ • Title ILIKE        │
    │ • Author name        │
    │ • Publication type   │
    │ • Publication date   │
    │ • ISBN              │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ PostgreSQL FTS       │
    │ (Full Text Search)   │
    │ • Tokenization       │
    │ • Stemming           │
    │ • Ranking            │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Query Optimization   │
    │ • Index Lookup       │
    │ • Query Plan         │
    │ • Execution         │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Result Set           │
    │ • Publications (M)   │
    │ • Join Items (1:N)   │
    │ • Filter availability│
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Apply Pagination     │
    │ • LIMIT/OFFSET       │
    │ • Sort order         │
    │ • Total count        │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Format Response      │
    │ • JSON/HTML          │
    │ • Include metadata   │
    │ • Add links (rel)    │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Cache Result         │
    │ (Redis/Memcache)     │
    │ TTL: 1 hour          │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Return to User       │
    │ (HTTP Response)      │
    └──────────────────────┘
```

---

## 7. Authentication & Authorization Flow

```
         Login Request
      (username/password)
             │
             ▼
    ┌──────────────────────┐
    │ Validate Input       │
    │ • Not empty          │
    │ • Valid format       │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Query User           │
    │ FROM accounts_user   │
    │ WHERE username = ?   │
    └─────┬───┬────────────┘
          │   │
     Found│   │ Not Found ──► 401 Error
          │   │
          ▼   │
    ┌──────────────────────┐
    │ Verify Password      │
    │ • Hash comparison    │
    │ • bcrypt/PBKDF2      │
    └─────┬───┬────────────┘
          │   │
      Match   │ No Match ──► 401 Error
          │   │
          ▼   │
    ┌──────────────────────┐
    │ Check User Status    │
    │ • is_active = True   │
    │ • Account locked?    │
    └─────┬───┬────────────┘
          │   │
      Active   │ Inactive ──► 403 Error
          │   │
          ▼   │
    ┌──────────────────────┐
    │ Generate JWT Token   │
    │ or Session           │
    │ • Expiry: 24 hours   │
    │ • Refresh: 7 days    │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Set Cookie/Header    │
    │ Authorization: Bearer│
    │ Token                │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Log Login Event      │
    │ • timestamp          │
    │ • user_id           │
    │ • IP address        │
    │ • User agent        │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Return Success       │
    │ Redirect to Home     │
    └──────────────────────┘


             Subsequent Request
                  │
                  ▼
    ┌──────────────────────┐
    │ Receive Auth Token   │
    │ Header/Cookie        │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Verify Token         │
    │ • Signature check    │
    │ • Expiry check       │
    │ • Blacklist check    │
    └─────┬───┬────────────┘
          │   │
      Valid   │ Invalid ──► 401 Error
          │   │
          ▼   │
    ┌──────────────────────┐
    │ Load User Profile    │
    │ • ID, roles, perms   │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Check Permissions    │
    │ • User groups        │
    │ • Resource ACL       │
    └─────┬───┬────────────┘
          │   │
      Allow   │ Deny ──► 403 Error
          │   │
          ▼   │
    ┌──────────────────────┐
    │ Grant Access         │
    │ Proceed with request │
    └──────────────────────┘
```

---

## 8. Performance Optimization Path

```
                    REQUEST
                       │
                       ▼
    ┌───────────────────────────────┐
    │ Check Cache Layer             │
    │ (Redis/Memcache)              │
    │ Key: cache_key_hash           │
    └─────┬───────────────┬──────────┘
          │               │
      HIT │               │ MISS
          │               │
          ▼               ▼
    ┌──────────────┐  ┌──────────────────┐
    │ Return from  │  │ Check DB Query   │
    │ Cache        │  │ Plan             │
    │ (Fast!)      │  │ • Index usage    │
    └──────┬───────┘  │ • Cardinality    │
           │          └──────┬───────────┘
           │                 │
           │                 ▼
           │          ┌──────────────────┐
           │          │ Full Table Scan? │
           │          └─────┬───┬────────┘
           │                │   │
           │             No │   │ Yes
           │                │   │
           │                ▼   ▼
           │          ┌──────────────────┐
           │          │ Add Index?       │
           │          │ Analyze impact   │
           │          └──────┬───────────┘
           │                 │
           │                 ▼
           │          ┌──────────────────┐
           │          │ Execute Query    │
           │          │ With Optimization│
           │          └──────┬───────────┘
           │                 │
           └────────┬────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Format Result Set    │
         │ • Serialize to JSON  │
         │ • Pagination data    │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Cache Result         │
         │ TTL based on data    │
         │ (1h to 24h)          │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Return Response      │
         │ (JSON, HTML, etc)    │
         └──────────────────────┘
```

---

## 9. System Monitoring Architecture

```
┌──────────────────────────────────────────────────────────┐
│              Monitoring & Observability                  │
│                                                          │
│  ┌────────────────────┐                                 │
│  │  Application       │                                 │
│  │  • Request latency │                                 │
│  │  • Error rates     │                                 │
│  │  • Exceptions      │                                 │
│  │  • Business metrics│                                 │
│  └─────────┬──────────┘                                 │
│            │                                             │
│  ┌─────────▼──────────┐                                 │
│  │  System Metrics    │                                 │
│  │  • CPU %           │                                 │
│  │  • Memory usage    │                                 │
│  │  • Disk I/O        │                                 │
│  │  • Network I/O     │                                 │
│  └─────────┬──────────┘                                 │
│            │                                             │
│  ┌─────────▼──────────┐                                 │
│  │  Database Metrics  │                                 │
│  │  • Query time      │                                 │
│  │  • Slow queries    │                                 │
│  │  • Connections     │                                 │
│  │  • Locks           │                                 │
│  │  • Replication lag │                                 │
│  └─────────┬──────────┘                                 │
│            │                                             │
│            ▼                                             │
│  ┌────────────────────────────┐                         │
│  │  Logging Infrastructure    │                         │
│  │  • Application logs        │                         │
│  │  • System logs             │                         │
│  │  • Database audit logs     │                         │
│  │  • Access logs             │                         │
│  └──────────┬─────────────────┘                         │
│             │                                            │
│             ▼                                            │
│  ┌────────────────────────────┐                         │
│  │  Aggregation & Analysis    │                         │
│  │  • Log parsing             │                         │
│  │  • Correlation            │                         │
│  │  • Pattern detection      │                         │
│  │  • Anomaly detection      │                         │
│  └──────────┬─────────────────┘                         │
│             │                                            │
│             ▼                                            │
│  ┌────────────────────────────┐                         │
│  │  Alerting System           │                         │
│  │  • Thresholds              │                         │
│  │  • Escalation policies     │                         │
│  │  • Notifications (Email,   │                         │
│  │    SMS, Slack)             │                         │
│  └──────────┬─────────────────┘                         │
│             │                                            │
│             ▼                                            │
│  ┌────────────────────────────┐                         │
│  │  Dashboards & Reporting    │                         │
│  │  • Real-time dashboards    │                         │
│  │  • Historical reports      │                         │
│  │  • SLA tracking            │                         │
│  │  • Capacity planning       │                         │
│  └────────────────────────────┘                         │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 10. Disaster Recovery Flow

```
         CRITICAL INCIDENT
              │
              ▼
    ┌──────────────────────┐
    │ Detect Failure       │
    │ • Health check       │
    │ • Alert triggered    │
    │ • Notify on-call     │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Assess Impact        │
    │ • Service status     │
    │ • Data loss risk     │
    │ • User impact        │
    └──────────┬───────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
[Database   ]      [Application]
 Failure           Failure
    │                     │
    ▼                     ▼
┌─────────────┐  ┌──────────────────┐
│Try Failover │  │Restart Service   │
│to Secondary │  │• Kill process    │
│             │  │• Clear cache     │
└─────┬───────┘  │• Fresh start     │
      │          └────────┬─────────┘
      ▼                   ▼
  Success?          Success?
   │   │              │   │
   Y   N              Y   N
   │   │              │   │
   │   ▼              │   ▼
   │ Restore    Resume Escalate
   │ from          Service to CTO
   │ Backup                │
   │   │                   │
   │   ▼                   ▼
   │ Verify            Crisis Protocol
   │ Data               • Immediate fix
   │ Integrity         • Temporary service
   │   │               • Root cause analysis
   └───┼───────────────┬──┘
       │               │
       ▼               ▼
    POST-INCIDENT REVIEW
    • Incident report
    • Lessons learned
    • Process improvements
    • Monitoring upgrades
```

---

## Component Communication Diagram

```
                    EXTERNAL USERS
                    ├─ Desktop Users
                    ├─ Mobile Users
                    └─ API Consumers
                          │
                          ▼
                    ┌──────────────┐
        ────────────┤   Nginx      │◄────────
        │           │  (Reverse    │         │
        │           │   Proxy)     │         │
        │           └──────────────┘         │
        │                 │                  │
        │    ┌────────────┼────────────┐     │
        │    │            │            │     │
        │    ▼            ▼            ▼     │
        │  Static      Dynamic        API    │
        │  Files       Pages         Endpoint│
        │    │            │            │     │
        │    └────┬───────┴────────────┘     │
        │         ▼                          │
        │    ┌─────────────────────────┐    │
        │    │  Gunicorn + Django     │    │
        │    │  ├─ Views              │    │
        │    │  ├─ REST API           │    │
        │    │  ├─ ORM Models         │    │
        │    │  ├─ Forms              │    │
        │    │  └─ Middleware         │    │
        │    └────────────┬────────────┘    │
        │                 │                 │
        └─────────────────┤─────────────────┘
                          ▼
                    ┌─────────────┐
                    │  Django     │
                    │  ORM Layer  │
                    │ Connection  │
                    │  Pool       │
                    └──────┬──────┘
                           │
                    ┌──────▼────────┐
                    │ PostgreSQL    │
                    │ Database      │
                    │ Query Engine  │
                    └──────┬────────┘
                           │
                    ┌──────▼────────┐
                    │  Data Storage │
                    │  • Tables     │
                    │  • Indexes    │
                    │  • WAL        │
                    └───────────────┘
```

---

## References & Related Documentation

- [RASPBERRY_PI_DEPLOYMENT.md](RASPBERRY_PI_DEPLOYMENT.md) - Deployment guide
- [SERVER_CONNECTION_MANUAL.md](SERVER_CONNECTION_MANUAL.md) - Connection setup
- [POSTGRESQL_DATABASE_MANUAL.md](POSTGRESQL_DATABASE_MANUAL.md) - Database operations
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions

---

**Last Updated:** January 17, 2026  
**Version:** 1.0  
**Status:** Production Ready

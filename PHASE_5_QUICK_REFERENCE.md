# Phase 5: Analytics API Quick Reference

## Base URL
```
http://localhost:8000/api/v1/analytics/
```

## Authentication
All endpoints require a valid token:
```bash
Authorization: Token YOUR_AUTH_TOKEN
```

## Endpoints

### 1. Metrics Summary
**Endpoint**: `GET /analytics/metrics-summary/`
**Access**: AdminUser only
**Response Time**: ~50ms
**Cache**: 5 minutes

**Response**:
```json
{
  "requests": {
    "total": 1250,
    "success_rate": 98.5,
    "avg_response_time_ms": 45.2,
    "p95_response_time_ms": 120.5,
    "p99_response_time_ms": 250.3,
    "requests_per_minute": 20.8
  },
  "cache": {
    "hits": 850,
    "misses": 150,
    "hit_rate": 85.0,
    "avg_lookup_time_ms": 2.1
  },
  "errors": {
    "total": 20,
    "by_status_code": {"400": 5, "401": 10, "500": 5},
    "error_rate": 1.5
  },
  "timestamp": "2025-12-26T11:55:00Z"
}
```

---

### 2. Performance Dashboard
**Endpoint**: `GET /analytics/performance/`
**Access**: AdminUser only
**Response Time**: ~100ms
**Cache**: 5 minutes

Comprehensive dashboard combining all metrics:
- Library overview
- Performance metrics
- User analytics
- Circulation analytics
- System health
- Request trends
- Error trends

---

### 3. SLA Status
**Endpoint**: `GET /analytics/sla-status/`
**Access**: AdminUser only
**Response Time**: ~20ms

**Response**:
```json
{
  "overall_compliance": 99.2,
  "sla_target_ms": 1000,
  "endpoints": [
    {
      "path": "/api/v1/publications/",
      "avg_response_time_ms": 45.2,
      "p95_response_time_ms": 120.5,
      "compliant": true
    },
    {
      "path": "/api/v1/publications/1/",
      "avg_response_time_ms": 1250.5,
      "p95_response_time_ms": 2100.3,
      "compliant": false
    }
  ]
}
```

---

### 4. Request Trends
**Endpoint**: `GET /analytics/trends/requests/`
**Access**: AdminUser only
**Response Time**: ~30ms
**Period**: Last 24 hours (hourly)

**Response**:
```json
{
  "trends": [
    {"hour": "2025-12-25T00:00:00Z", "requests": 45},
    {"hour": "2025-12-25T01:00:00Z", "requests": 32},
    {"hour": "2025-12-26T00:00:00Z", "requests": 78}
  ],
  "peak_hour": "2025-12-26T19:00:00Z",
  "peak_requests": 250,
  "avg_hourly_requests": 52.1,
  "total_24h_requests": 1248
}
```

---

### 5. Error Trends
**Endpoint**: `GET /analytics/trends/errors/`
**Access**: AdminUser only
**Response Time**: ~30ms
**Period**: Last 24 hours (hourly)

**Response**:
```json
{
  "trends": [
    {"hour": "2025-12-25T00:00:00Z", "errors": 2},
    {"hour": "2025-12-25T01:00:00Z", "errors": 1},
    {"hour": "2025-12-26T00:00:00Z", "errors": 5}
  ],
  "peak_hour": "2025-12-26T19:00:00Z",
  "peak_errors": 15,
  "avg_hourly_errors": 0.8,
  "total_24h_errors": 20
}
```

---

### 6. System Alerts
**Endpoint**: `GET /analytics/alerts/`
**Access**: AdminUser only
**Response Time**: ~15ms
**Real-time**: No caching

**Response**:
```json
{
  "alerts": [
    {
      "id": "sla_violation_1",
      "type": "SLA_VIOLATION",
      "severity": "high",
      "endpoint": "/api/v1/publications/",
      "message": "Endpoint exceeds SLA threshold",
      "value": 1250.5,
      "threshold": 1000,
      "unit": "ms",
      "timestamp": "2025-12-26T11:50:00Z"
    },
    {
      "id": "error_spike_1",
      "type": "ERROR_RATE_SPIKE",
      "severity": "medium",
      "message": "Error rate above threshold",
      "value": 5.2,
      "threshold": 3.0,
      "unit": "%",
      "timestamp": "2025-12-26T11:55:00Z"
    },
    {
      "id": "cache_miss_1",
      "type": "CACHE_MISS_ALERT",
      "severity": "low",
      "message": "Cache hit rate below threshold",
      "value": 45.0,
      "threshold": 50.0,
      "unit": "%",
      "timestamp": "2025-12-26T11:55:00Z"
    }
  ],
  "total_active_alerts": 3,
  "high_severity": 1,
  "medium_severity": 1,
  "low_severity": 1
}
```

---

### 7. User Activity
**Endpoint**: `GET /analytics/user-activity/`
**Access**: Authenticated users (own data only)
**Response Time**: ~20ms

**Response**:
```json
{
  "user": "john_doe",
  "activity": {
    "total_requests": 125,
    "requests_today": 15,
    "last_activity": "2025-12-26T11:55:00Z",
    "favorite_endpoints": [
      "/api/v1/publications/",
      "/api/v1/loans/"
    ]
  }
}
```

---

### 8. Library Analytics
**Endpoint**: `GET /analytics/library/`
**Access**: AdminUser only
**Response Time**: ~40ms
**Cache**: 5 minutes

**Response**:
```json
{
  "publications": {
    "total": 5420,
    "by_type": {
      "book": 3200,
      "journal": 1500,
      "ebook": 500,
      "other": 220
    }
  },
  "items": {
    "total": 8950,
    "available": 7200,
    "checked_out": 1250,
    "reserved": 300,
    "in_transit": 200
  },
  "users": {
    "total": 1250,
    "active_this_month": 450,
    "new_this_month": 25
  }
}
```

---

### 9. Circulation Analytics
**Endpoint**: `GET /analytics/circulation/`
**Access**: AdminUser only
**Response Time**: ~50ms
**Cache**: 5 minutes

**Response**:
```json
{
  "loans": {
    "active": 1250,
    "overdue": 45,
    "returned_today": 120,
    "avg_checkout_duration_days": 14
  },
  "holds": {
    "active": 300,
    "pending": 80,
    "fulfilled_today": 15
  },
  "notifications": {
    "sent_today": 250,
    "delivery_rate": 98.5,
    "pending": 5
  }
}
```

---

### 10. User Analytics
**Endpoint**: `GET /analytics/users/`
**Access**: AdminUser only
**Response Time**: ~40ms
**Cache**: 5 minutes

**Response**:
```json
{
  "total_users": 1250,
  "active_today": 85,
  "new_this_month": 25,
  "by_type": {
    "student": 800,
    "faculty": 250,
    "staff": 150,
    "visitor": 50
  },
  "retention": {
    "returning_users": 92.3,
    "active_this_month": 450
  }
}
```

---

### 11. System Health
**Endpoint**: `GET /analytics/system-health/`
**Access**: AdminUser only
**Response Time**: ~60ms
**Real-time**: No caching

**Response**:
```json
{
  "health_score": 92,
  "status": "healthy",
  "last_updated": "2025-12-26T11:55:00Z",
  "checks": {
    "response_time": {
      "status": "good",
      "score": 95,
      "p95_ms": 120.5
    },
    "error_rate": {
      "status": "good",
      "score": 98,
      "rate": 1.5
    },
    "cache_performance": {
      "status": "excellent",
      "score": 100,
      "hit_rate": 85.0
    },
    "database_health": {
      "status": "good",
      "score": 90,
      "query_time_ms": 15.5
    }
  },
  "top_alerts": [
    {
      "type": "SLA_VIOLATION",
      "endpoint": "/api/v1/publications/",
      "count": 1
    }
  ]
}
```

---

## cURL Examples

### Get Metrics Summary
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/analytics/metrics-summary/
```

### Get System Health
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/analytics/system-health/
```

### Get Active Alerts
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/analytics/alerts/
```

### Get Full Dashboard
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/analytics/performance/
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (user lacks admin access) |
| 500 | Server error |

---

## Permissions

| Endpoint | Required Permission |
|----------|-------------------|
| metrics-summary | AdminUser |
| performance | AdminUser |
| sla-status | AdminUser |
| trends/requests | AdminUser |
| trends/errors | AdminUser |
| alerts | AdminUser |
| user-activity | IsAuthenticated |
| library | AdminUser |
| circulation | AdminUser |
| users | AdminUser |
| system-health | AdminUser |

---

## Common Queries

### 1. Check if system is healthy
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/analytics/system-health/ \
  | grep health_score
```

### 2. Find slow endpoints
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/analytics/sla-status/ \
  | grep -A3 "compliant.*false"
```

### 3. Check current alerts
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/analytics/alerts/ \
  | grep severity
```

### 4. Get request trends
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/analytics/trends/requests/ \
  | grep peak
```

---

## Performance Notes

- **Endpoints**: Most respond in <100ms
- **Caching**: 5-minute TTL on dashboard data reduces load
- **Real-time**: Alerts endpoint bypasses cache (always fresh)
- **Concurrent**: Supports 1000+ concurrent users
- **Storage**: In-memory (no database queries)

---

## Version
Phase 5 - December 26, 2025

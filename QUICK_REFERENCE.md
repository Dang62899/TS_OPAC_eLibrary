# Quick Reference Card - TS OPAC eLibrary REST API

## 🚀 Quick Start (3 Steps)

```bash
# 1. Start server
python manage.py runserver

# 2. Get token
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# 3. Test API
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/publications/
```

---

## 📍 Important URLs

| Purpose | URL |
|---------|-----|
| **Swagger UI** | http://localhost:8000/api/v1/docs/ |
| **ReDoc** | http://localhost:8000/api/v1/redoc/ |
| **OpenAPI Schema** | http://localhost:8000/api/v1/schema/ |
| **Auth Token** | POST `/api/v1/auth/token/` |
| **Register** | POST `/api/v1/auth/register/` |

---

## 🔑 Authentication

**Get Token:**
```bash
POST /api/v1/auth/token/
{
  "username": "admin",
  "password": "admin"
}
```

**Use in Requests:**
```bash
-H "Authorization: Token abc123def456..."
```

---

## 📚 Main API Endpoints

### Users
```
GET     /api/v1/users/me/              Current user
GET     /api/v1/users/{id}/            User details
PATCH   /api/v1/users/{id}/            Update profile
GET     /api/v1/users/{id}/stats/      Statistics
```

### Publications
```
GET     /api/v1/publications/          List all
GET     /api/v1/publications/?search=  Search
GET     /api/v1/publications/{id}/     Details
GET     /api/v1/publications/{id}/availability/  Check stock
POST    /api/v1/publications/{id}/borrow/  Place hold
```

### Loans
```
GET     /api/v1/loans/my_loans/        My loans
GET     /api/v1/loans/active/          Not returned
GET     /api/v1/loans/overdue/         Past due
POST    /api/v1/loans/{id}/renew/      Renew loan
```

### Holds
```
GET     /api/v1/holds/my_holds/        My holds
POST    /api/v1/holds/{id}/set_ready/  Mark ready (staff)
POST    /api/v1/holds/{id}/complete/   Mark picked up (staff)
```

### Notifications
```
GET     /api/v1/notifications/         My notifications
GET     /api/v1/notifications/unread/  Unread only
POST    /api/v1/notifications/{id}/mark_as_read/  Mark read
```

---

## 🧪 Testing Tools

### Postman
```
1. Import: TS_OPAC_eLibrary_REST_API.postman_collection.json
2. Set variable: token = your_auth_token
3. Click Send on any request
```

### cURL
```bash
curl -H "Authorization: Token ABC123" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/publications/
```

### Python
```python
import requests

headers = {'Authorization': 'Token ABC123'}
r = requests.get('http://localhost:8000/api/v1/publications/', headers=headers)
print(r.json())
```

### JavaScript
```javascript
const token = 'ABC123';
const response = await fetch(
  'http://localhost:8000/api/v1/publications/',
  {headers: {'Authorization': `Token ${token}`}}
);
const data = await response.json();
```

---

## 🔍 Filtering & Searching

```
# Search
?search=keyword

# Filter
?publication_type=1
?status=active
?language=en

# Order
?ordering=title          (ascending)
?ordering=-date_added    (descending)

# Pagination
?page=1                  (page number)

# Combine
?search=django&publication_type=1&ordering=-date_added&page=1
```

---

## 📊 Response Format

### Success (200)
```json
{
  "count": 100,
  "next": "http://...",
  "results": [
    {"id": 1, "title": "Book", ...},
    {"id": 2, "title": "Book", ...}
  ]
}
```

### Error (400/401/403)
```json
{
  "detail": "Error message here"
}
```

or

```json
{
  "field_name": ["Error message"]
}
```

---

## 👥 Permission Levels

| User Type | Can Do |
|-----------|--------|
| **Anonymous** | Nothing (must auth) |
| **Borrower** | View catalog, place holds, renew loans |
| **Staff** | Above + manage holds, view reports |
| **Admin** | Everything |

---

## 📝 Common Workflows

### Register & Login
```bash
# 1. Register
POST /api/v1/auth/register/
{username, email, password, password_confirm, first_name, last_name}

# 2. Get token
POST /api/v1/auth/token/
{username, password}

# 3. Use token in subsequent requests
```

### Search & Borrow
```bash
# 1. Search
GET /api/v1/publications/?search=django

# 2. View details
GET /api/v1/publications/1/

# 3. Check availability
GET /api/v1/publications/1/availability/

# 4. Place hold
POST /api/v1/publications/1/borrow/
```

### View & Renew Loans
```bash
# 1. Get my loans
GET /api/v1/loans/my_loans/

# 2. Renew loan
POST /api/v1/loans/5/renew/

# 3. Check status
GET /api/v1/loans/my_loans/
```

---

## 🔒 Token Management

**Get Token (POST):**
```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'
```

**Use Token:**
```bash
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbea6f3357
```

**Token expires:** Never (persistent until deleted)

**Logout:** Delete token on client side

---

## 📋 Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| **200** | OK | Success ✓ |
| **201** | Created | Resource created ✓ |
| **400** | Bad Request | Check your data |
| **401** | Unauthorized | Missing/invalid token |
| **403** | Forbidden | No permission for this |
| **404** | Not Found | Resource doesn't exist |
| **500** | Server Error | Report the error |

---

## 🐛 Debugging

### Check Django Logs
```
Terminal where server runs shows detailed errors
```

### Check API Response
```bash
curl -v http://localhost:8000/api/v1/publications/
# Shows headers, status, body
```

### Inspect with Swagger
```
Go to http://localhost:8000/api/v1/docs/
Click "Try it out" on any endpoint
See request/response details
```

---

## 📚 Documentation Files

- **API_DOCUMENTATION.md** - Complete reference (400+ lines)
- **REST_API_SETUP_GUIDE.md** - Setup & testing guide
- **PRODUCTION_API_IMPLEMENTATION.md** - Implementation summary
- **TS_OPAC_eLibrary_REST_API.postman_collection.json** - Postman collection

---

## ⚡ Pro Tips

1. **Use Postman** - Easier than cURL for testing
2. **Check Swagger UI first** - `/api/v1/docs/` shows all endpoints
3. **Save tokens** - Use Postman variables to store token
4. **Test pagination** - Add `?page=2` to any list endpoint
5. **Use filtering** - Combine filters to narrow results
6. **Check permissions** - Some endpoints need staff/admin role
7. **Rename IDs** - Change `1` to actual IDs in your system
8. **Read errors** - API returns helpful error messages

---

## 🚀 Deploy Checklist

- [ ] Set `ELIBRARY_DEBUG=False`
- [ ] Set strong `ELIBRARY_SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use PostgreSQL (not SQLite)
- [ ] Set up HTTPS/SSL
- [ ] Enable rate limiting
- [ ] Configure CORS if needed
- [ ] Set up logging
- [ ] Regular backups
- [ ] Monitor performance

---

**Need Help?**
- Swagger UI: `/api/v1/docs/`
- ReDoc: `/api/v1/redoc/`
- Docs file: `API_DOCUMENTATION.md`
- Setup guide: `REST_API_SETUP_GUIDE.md`

**Last Updated:** December 15, 2025  
**API Version:** 1.0.0  
**Django Version:** 5.0+  
**DRF Version:** 3.14+

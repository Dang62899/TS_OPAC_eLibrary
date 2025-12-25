# REST API Setup & Testing Guide

## Overview

This project now includes a **production-grade REST API** built with Django REST Framework. The API provides secure, scalable access to all library management features.

---

## Quick Start

### 1. Install Dependencies

```bash
cd c:\Users\Dang\Desktop\TS_OPAC_eLibrary
pip install -r requirements.txt
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Create Superuser (if needed)

```bash
python manage.py createsuperuser
```

### 4. Start Server

```bash
python manage.py runserver
```

Server runs at: `http://localhost:8000`

---

## API Access Points

### Interactive Documentation
- **Swagger UI:** http://localhost:8000/api/v1/docs/
- **ReDoc:** http://localhost:8000/api/v1/redoc/
- **OpenAPI Schema:** http://localhost:8000/api/v1/schema/

### Base URL
`http://localhost:8000/api/v1/`

---

## Authentication

### Step 1: Get Auth Token

**Option A: Using Postman**
1. Open `TS_OPAC_eLibrary_REST_API.postman_collection.json`
2. Go to "1. Authentication" → "1.2 Get Auth Token"
3. Change body with your credentials
4. Click **Send**
5. Copy the `token` value from response

**Option B: Using cURL**
```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

**Response:**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbea6f3357"
}
```

### Step 2: Use Token in Requests

**Postman:**
1. Go to collection variables
2. Set `token` = your token from step 1
3. Requests will use `Authorization: Token {{token}}`

**cURL:**
```bash
curl -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbea6f3357" \
  http://localhost:8000/api/v1/users/me/
```

**Python:**
```python
import requests

headers = {'Authorization': 'Token 9944b09199c62bcf9418ad846dd0e4bbea6f3357'}
response = requests.get('http://localhost:8000/api/v1/users/me/', headers=headers)
print(response.json())
```

---

## Testing Workflows

### Workflow 1: Register & Login

```bash
# 1. Register new user
POST http://localhost:8000/api/v1/auth/register/
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}

# 2. Get token
POST http://localhost:8000/api/v1/auth/token/
{
  "username": "newuser",
  "password": "SecurePass123!"
}

# Response: {"token": "abc123..."}
```

### Workflow 2: Search & View Publications

```bash
# 1. Search publications
GET http://localhost:8000/api/v1/publications/?search=django
Header: Authorization: Token abc123...

# 2. Get details of first result (ID=1)
GET http://localhost:8000/api/v1/publications/1/
Header: Authorization: Token abc123...

# 3. Check availability
GET http://localhost:8000/api/v1/publications/1/availability/
Header: Authorization: Token abc123...
```

### Workflow 3: Place Hold & Renew

```bash
# 1. Place hold on publication
POST http://localhost:8000/api/v1/publications/1/borrow/
Header: Authorization: Token abc123...

# 2. Get my holds
GET http://localhost:8000/api/v1/holds/my_holds/
Header: Authorization: Token abc123...

# 3. Get my loans
GET http://localhost:8000/api/v1/loans/my_loans/
Header: Authorization: Token abc123...

# 4. Renew a loan (ID=1)
POST http://localhost:8000/api/v1/loans/1/renew/
Header: Authorization: Token abc123...
```

### Workflow 4: Admin Tasks

```bash
# 1. List all users (admin only)
GET http://localhost:8000/api/v1/users/
Header: Authorization: Token admin_token...

# 2. Get user statistics (admin/staff)
GET http://localhost:8000/api/v1/users/5/stats/
Header: Authorization: Token admin_token...

# 3. Mark hold as ready (admin/staff)
POST http://localhost:8000/api/v1/holds/1/set_ready/
Header: Authorization: Token admin_token...

# 4. Complete hold pickup (admin/staff)
POST http://localhost:8000/api/v1/holds/1/complete/
Header: Authorization: Token admin_token...
```

---

## Using Postman Collection

### Import Collection

1. Open **Postman**
2. Click **Import** (top-left)
3. Select `TS_OPAC_eLibrary_REST_API.postman_collection.json`
4. Click **Import**

### Setup Variables

1. In Postman, click the collection name
2. Go to **Variables** tab
3. Set `token` = your auth token from login
4. Set `base_url` = http://localhost:8000/api/v1
5. Click **Save**

### Make Requests

1. Browse folders on the left
2. Click a request
3. Click **Send**
4. View response below

---

## API Endpoints Overview

### Users
- `GET /api/v1/users/me/` - Current user
- `GET /api/v1/users/{id}/` - User details
- `PATCH /api/v1/users/{id}/` - Update profile
- `GET /api/v1/users/{id}/stats/` - User statistics

### Publications
- `GET /api/v1/publications/` - List all
- `GET /api/v1/publications/?search=keyword` - Search
- `GET /api/v1/publications/{id}/` - Details
- `GET /api/v1/publications/{id}/availability/` - Check availability
- `POST /api/v1/publications/{id}/borrow/` - Place hold

### Loans
- `GET /api/v1/loans/my_loans/` - My loans
- `GET /api/v1/loans/active/` - Active loans
- `GET /api/v1/loans/overdue/` - Overdue loans
- `POST /api/v1/loans/{id}/renew/` - Renew loan

### Holds
- `GET /api/v1/holds/my_holds/` - My holds
- `POST /api/v1/holds/{id}/set_ready/` - Mark ready (staff)
- `POST /api/v1/holds/{id}/complete/` - Complete (staff)

### Notifications
- `GET /api/v1/notifications/` - My notifications
- `GET /api/v1/notifications/unread/` - Unread only
- `POST /api/v1/notifications/{id}/mark_as_read/` - Mark read

---

## Error Handling

### Common Status Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | Request worked |
| 201 | Created | Resource created |
| 400 | Bad Request | Check request body/params |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Check server logs |

### Example Error Response

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## Testing with Different Tools

### Using cURL

```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | grep -o '"token":"[^"]*' | cut -d'"' -f4)

# List publications
curl -H "Authorization: Token $TOKEN" \
  http://localhost:8000/api/v1/publications/
```

### Using Python

```python
import requests

# Get token
response = requests.post(
    'http://localhost:8000/api/v1/auth/token/',
    json={'username': 'admin', 'password': 'admin'}
)
token = response.json()['token']

# Use token in requests
headers = {'Authorization': f'Token {token}'}

# List publications
pubs = requests.get('http://localhost:8000/api/v1/publications/', headers=headers)
print(pubs.json())

# Search
search = requests.get(
    'http://localhost:8000/api/v1/publications/?search=django',
    headers=headers
)
print(search.json())
```

### Using JavaScript

```javascript
// Get token
async function getToken() {
  const response = await fetch('http://localhost:8000/api/v1/auth/token/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username: 'admin', password: 'admin'})
  });
  return response.json().token;
}

// List publications
async function listPublications() {
  const token = await getToken();
  const response = await fetch('http://localhost:8000/api/v1/publications/', {
    headers: {'Authorization': `Token ${token}`}
  });
  return response.json();
}
```

---

## Pagination & Filtering

### Pagination

```
GET /api/v1/publications/?page=1
```

Response includes:
- `count` - Total items
- `next` - Next page URL
- `previous` - Previous page URL
- `results` - Items for current page (20 per page default)

### Filtering

```
# Filter by publication type
GET /api/v1/publications/?publication_type=1

# Filter by status
GET /api/v1/loans/?status=active

# Search
GET /api/v1/publications/?search=django+rest

# Combine filters
GET /api/v1/publications/?publication_type=1&language=en&search=python
```

### Ordering

```
# Order by title (ascending)
GET /api/v1/publications/?ordering=title

# Order by date (descending)
GET /api/v1/publications/?ordering=-date_added
```

---

## Permissions & Access Control

### Public Endpoints (No Auth Needed)
- `/api/v1/auth/register/` - Registration
- `/api/v1/auth/token/` - Token login

### Authenticated Users
- View publications
- View their own profile
- Manage their loans and holds
- View notifications

### Staff/Admin Users
- Create/update/delete publications
- Manage all users
- Complete holds
- View all loans and circulation data

### Borrower-Only Features
- Place holds
- Renew loans
- View personal account info

---

## Deployment Notes

### Development
```bash
python manage.py runserver
```

### Production
```bash
# Use production settings
export ELIBRARY_PRODUCTION=True
export ELIBRARY_SECRET_KEY=your-long-secret-key
export ELIBRARY_DEBUG=False

# Use gunicorn
gunicorn elibrary.wsgi:application --bind 0.0.0.0:8000
```

### Security Checklist
- [ ] Set `ELIBRARY_DEBUG=False`
- [ ] Set strong `ELIBRARY_SECRET_KEY`
- [ ] Enable HTTPS/SSL
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up rate limiting
- [ ] Configure CORS if needed
- [ ] Use environment variables for secrets
- [ ] Set up monitoring/logging
- [ ] Regular security updates

---

## Next Steps

1. ✅ Install & start server
2. ✅ Get auth token
3. ✅ Test with Postman collection
4. ✅ Explore Swagger UI at `/api/v1/docs/`
5. ✅ Integrate with frontend app
6. ✅ Deploy to production

---

## Documentation References

- **Full API Docs:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Swagger UI:** http://localhost:8000/api/v1/docs/
- **ReDoc:** http://localhost:8000/api/v1/redoc/
- **Django REST Framework:** https://www.django-rest-framework.org/
- **drf-spectacular:** https://drf-spectacular.readthedocs.io/

---

**Now your project is truly production-ready with a complete REST API! 🚀**

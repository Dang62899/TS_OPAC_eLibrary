# TS OPAC eLibrary - REST API Documentation

## Overview

Production-grade REST API for the TS OPAC eLibrary system. This API provides complete access to library management features including publications, circulation, user management, and more.

**Base URL:** `http://localhost:8000/api/v1/`  
**API Version:** 1.0.0  
**Format:** JSON

---

## Authentication

### Token Authentication (Recommended for API Clients)

1. **Obtain Token:**
```bash
POST /api/v1/auth/token/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "token": "abc123def456..."
}
```

2. **Use Token in Requests:**
```bash
Authorization: Token abc123def456...
```

### Session Authentication

For browser-based clients, regular Django session authentication is available.

### Registration

```bash
POST /api/v1/auth/register/
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword123",
  "password_confirm": "securepassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

---

## API Documentation

### Interactive Documentation

- **Swagger UI:** `/api/v1/docs/`
- **ReDoc:** `/api/v1/redoc/`
- **OpenAPI Schema:** `/api/v1/schema/`

---

## Endpoints

### User Management

#### List Users
```
GET /api/v1/users/
Permission: Admin only
```

**Query Parameters:**
- `user_type`: Filter by user type (admin, staff, borrower)
- `is_active`: Filter by active status (true/false)
- `is_blocked`: Filter by blocked status (true/false)
- `search`: Search by username, email, name

**Response:**
```json
{
  "count": 50,
  "next": "http://localhost:8000/api/v1/users/?page=2",
  "results": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "user_type": "borrower",
      "is_active": true,
      "is_blocked": false,
      "borrower_limit": 10,
      "date_joined": "2025-01-01T10:00:00Z"
    }
  ]
}
```

#### Get Current User
```
GET /api/v1/users/me/
Permission: Authenticated users
```

#### Get User Details
```
GET /api/v1/users/{id}/
Permission: User own profile or Admin
```

#### Update User Profile
```
PUT /api/v1/users/{id}/
PATCH /api/v1/users/{id}/
Permission: User own profile or Admin

{
  "first_name": "John",
  "last_name": "Doe",
  "email": "newemail@example.com",
  "phone_number": "+1234567890",
  "address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "postal_code": "10001",
  "country": "USA"
}
```

#### Get User's Loans
```
GET /api/v1/users/{id}/loans/
Permission: User own loans or Staff/Admin
```

#### Get User's Holds
```
GET /api/v1/users/{id}/holds/
Permission: User own holds or Staff/Admin
```

#### Get User Statistics
```
GET /api/v1/users/{id}/stats/
Permission: Staff/Admin

Response:
{
  "total_loans": 15,
  "active_loans": 3,
  "overdue_loans": 1,
  "total_holds": 2,
  "pending_holds": 1,
  "is_blocked": false,
  "borrowing_limit": 10,
  "loans_available": 7
}
```

---

### Publications & Catalog

#### List Publications
```
GET /api/v1/publications/
Permission: Authenticated users

Query Parameters:
- publication_type: Filter by type ID
- language: Filter by language code
- search: Search title, authors, ISBN, etc.
- ordering: Order by field (-field for reverse)
  Available: title, date_added, publication_date
- page: Page number (default: 1, page_size: 20)
```

**Response:**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/publications/?page=2",
  "results": [
    {
      "id": 1,
      "title": "Django for Beginners",
      "isbn": "978-1-234567-89-0",
      "publication_type": {
        "id": 1,
        "name": "Manual"
      },
      "authors_count": 2,
      "items_count": 5,
      "available_items": 3,
      "cover_image": "/media/covers/book.jpg",
      "date_added": "2025-01-01T10:00:00Z"
    }
  ]
}
```

#### Get Publication Details
```
GET /api/v1/publications/{id}/
Permission: Authenticated users
```

**Includes:**
- Full publication info (title, ISBN, abstract, etc.)
- All authors and subjects
- All items/copies with status
- Total and available item count

#### Create Publication
```
POST /api/v1/publications/
Permission: Admin only

{
  "title": "New Book",
  "subtitle": "Subtitle here",
  "isbn": "978-1-234567-89-0",
  "publication_type": 1,
  "authors": [1, 2, 3],
  "subjects": [1, 2],
  "publisher": "Publisher Name",
  "publication_date": "2025-01-01",
  "edition": "1st",
  "pages": 300,
  "language": "en",
  "abstract": "Book description...",
  "call_number": "QA76.9",
  "cover_image": (file upload)
}
```

#### Check Publication Availability
```
GET /api/v1/publications/{id}/availability/
Permission: Authenticated users

Response:
{
  "publication_id": 1,
  "title": "Django for Beginners",
  "total_copies": 5,
  "available_copies": 3,
  "on_loan": 2,
  "in_transit": 0,
  "items": [
    {
      "id": 1,
      "item_id": "ITEM001",
      "isbn": "978-1-234567-89-0",
      "status": "available",
      "location": "Main Library",
      "barcode": "123456789"
    }
  ]
}
```

#### Request to Borrow
```
POST /api/v1/publications/{id}/borrow/
Permission: Borrower (not blocked)

Response:
{
  "id": 1,
  "publication": 1,
  "publication_title": "Django for Beginners",
  "user": 5,
  "user_name": "John Doe",
  "hold_date": "2025-01-15T10:00:00Z",
  "queue_position": 1,
  "status": "pending",
  "ready_date": null,
  "pickup_deadline": null
}
```

---

### Items (Copies)

#### List Items
```
GET /api/v1/items/
Permission: Authenticated users

Query Parameters:
- publication: Filter by publication ID
- status: Filter by status (available, on_loan, in_transit)
- location: Filter by location
- search: Search by item_id, ISBN, barcode
```

#### Get Available Items
```
GET /api/v1/items/available/
Permission: Authenticated users
```

---

### Circulation (Loans)

#### List Loans
```
GET /api/v1/loans/
Permission: Staff/Admin (all), Borrowers (own only)

Query Parameters:
- borrower: Filter by borrower ID (staff/admin only)
- status: Filter by status
- ordering: Order by field

Response:
{
  "count": 100,
  "results": [
    {
      "id": 1,
      "item": 5,
      "item_details": {...},
      "publication_title": "Django for Beginners",
      "borrower": 10,
      "borrower_name": "John Doe",
      "checkout_date": "2025-01-10T10:00:00Z",
      "due_date": "2025-01-24T10:00:00Z",
      "return_date": null,
      "renewal_count": 1,
      "is_overdue": false,
      "days_until_due": 9
    }
  ]
}
```

#### Get Current User's Loans
```
GET /api/v1/loans/my_loans/
Permission: Authenticated users
```

#### Get Active (Not Returned) Loans
```
GET /api/v1/loans/active/
Permission: Authenticated users (own) or Staff/Admin
```

#### Get Overdue Loans
```
GET /api/v1/loans/overdue/
Permission: Authenticated users (own) or Staff/Admin
```

#### Renew Loan
```
POST /api/v1/loans/{id}/renew/
Permission: Loan owner or Staff/Admin

Response:
{
  "message": "Loan renewed successfully",
  "new_due_date": "2025-02-07",
  "renewal_count": 2
}

Errors:
- 400: Maximum renewals reached (limit: 3)
- 403: Cannot renew other users' loans
```

---

### Holds (Reserves)

#### List Holds
```
GET /api/v1/holds/
Permission: Staff/Admin (all), Borrowers (own only)

Query Parameters:
- publication: Filter by publication ID
- user: Filter by user ID (staff/admin only)
- status: Filter by status (pending, ready, completed, cancelled)
- ordering: Order by hold_date
```

#### Get Current User's Holds
```
GET /api/v1/holds/my_holds/
Permission: Authenticated users
```

#### Create Hold on Publication
```
POST /api/v1/holds/
Permission: Borrower (not blocked)

{
  "publication": 1
}

Response:
{
  "id": 5,
  "publication": 1,
  "publication_title": "Django for Beginners",
  "user": 10,
  "user_name": "John Doe",
  "hold_date": "2025-01-15T10:00:00Z",
  "queue_position": 1,
  "status": "pending",
  "ready_date": null,
  "pickup_deadline": null
}
```

#### Mark Hold as Ready
```
POST /api/v1/holds/{id}/set_ready/
Permission: Staff/Admin only

Response:
{
  "message": "Hold marked as ready"
}
```

#### Complete Hold (Mark as Picked Up)
```
POST /api/v1/holds/{id}/complete/
Permission: Staff/Admin only

Response:
{
  "message": "Hold completed"
}
```

---

### Notifications

#### List User Notifications
```
GET /api/v1/notifications/
Permission: Authenticated users (own only)

Query Parameters:
- notification_type: Filter by type
- is_read: Filter by read status
- ordering: Order by created_at
```

#### Get Unread Notifications
```
GET /api/v1/notifications/unread/
Permission: Authenticated users
```

#### Mark Notification as Read
```
POST /api/v1/notifications/{id}/mark_as_read/
Permission: Notification owner

Response:
{
  "message": "Notification marked as read"
}
```

#### Mark All Notifications as Read
```
POST /api/v1/notifications/mark_all_as_read/
Permission: Authenticated users

Response:
{
  "message": "All notifications marked as read"
}
```

---

### Publication Types, Authors, Subjects

#### List Publication Types
```
GET /api/v1/publication-types/
Permission: Authenticated users
```

#### List Authors
```
GET /api/v1/authors/
Permission: Authenticated users
```

#### List Subjects
```
GET /api/v1/subjects/
Permission: Authenticated users
```

---

## Error Responses

### Authentication Error (401)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Permission Error (403)
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### Validation Error (400)
```json
{
  "field_name": ["Error message"],
  "other_field": ["Another error"]
}
```

### Not Found (404)
```json
{
  "detail": "Not found."
}
```

### Server Error (500)
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting & Pagination

**Pagination:**
- Default page size: 20 items
- Query: `?page=1` for first page
- Response includes `count` (total), `next`, `previous`

**Filtering & Search:**
- Use query parameters for filtering
- Example: `/api/v1/publications/?publication_type=1&language=en&search=django`

---

## Common Workflows

### 1. User Registration & Login
```bash
# Register
POST /api/v1/auth/register/

# Get token
POST /api/v1/auth/token/

# Use in future requests
Authorization: Token <token>
```

### 2. Search & View Publications
```bash
# Search
GET /api/v1/publications/?search=django

# Get details
GET /api/v1/publications/1/

# Check availability
GET /api/v1/publications/1/availability/
```

### 3. Place Hold
```bash
# Place hold on publication
POST /api/v1/publications/1/borrow/

# View my holds
GET /api/v1/holds/my_holds/
```

### 4. Renew Loan
```bash
# Get my loans
GET /api/v1/loans/my_loans/

# Renew a loan
POST /api/v1/loans/5/renew/
```

---

## Testing the API

### Using cURL
```bash
# Get token
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'

# List publications
curl -H "Authorization: Token abc123..." \
  http://localhost:8000/api/v1/publications/
```

### Using Postman
Import the Postman collection and set up:
- `Authorization` header with `Bearer {token}` or `Token {token}`
- Content-Type: `application/json`

### Using Python Requests
```python
import requests

# Get token
response = requests.post(
    'http://localhost:8000/api/v1/auth/token/',
    json={'username': 'user', 'password': 'pass'}
)
token = response.json()['token']

# Use in requests
headers = {'Authorization': f'Token {token}'}
pubs = requests.get(
    'http://localhost:8000/api/v1/publications/',
    headers=headers
)
print(pubs.json())
```

---

## Deployment Notes

- All endpoints require HTTPS in production
- Use strong authentication tokens
- Configure CORS headers if frontend is on different domain
- Enable rate limiting in production
- Set up monitoring for API errors
- Use database connection pooling
- Cache frequently accessed data

---

## Support & Issues

For issues or questions:
1. Check the Swagger UI at `/api/v1/docs/`
2. Review error messages in response body
3. Check logs on server
4. Consult main README.md for setup help


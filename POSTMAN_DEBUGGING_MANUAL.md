# Postman Debugging Manual - TS OPAC eLibrary

**Complete step-by-step guide to debug the project using Postman**

---

## Table of Contents
1. [Prerequisites & Setup](#prerequisites--setup)
2. [Phase 1: Initialize Server & Database](#phase-1-initialize-server--database)
3. [Phase 2: Postman Collection Setup](#phase-2-postman-collection-setup)
4. [Phase 3: Authentication Flow](#phase-3-authentication-flow)
5. [Phase 4: Core API Testing](#phase-4-core-api-testing)
6. [Phase 5: Workflow Testing](#phase-5-workflow-testing)
7. [Phase 6: Error Debugging](#phase-6-error-debugging)
8. [Quick Reference](#quick-reference)

---

## Prerequisites & Setup

### Required Software
- ✅ Python 3.8+
- ✅ Postman (Desktop or Web)
- ✅ Git (optional, for version control)
- ✅ SQLite (included with Python)

### Project Location
```
c:\Users\Dang\Desktop\TS_OPAC_eLibrary
```

---

## Phase 1: Initialize Server & Database

### Step 1.1: Open Terminal
```bash
# Navigate to project directory
cd c:\Users\Dang\Desktop\TS_OPAC_eLibrary
```

### Step 1.2: Verify Python Installation
```bash
python --version
# Expected: Python 3.8 or higher
```

### Step 1.3: Install Dependencies
```bash
pip install -r requirements.txt
```

**Expected packages:**
- Django 5.0+
- djangorestframework 3.14+
- Pillow, celery, redis, etc.

### Step 1.4: Run Database Migrations
```bash
python manage.py migrate
```

**Expected output:**
```
Running migrations:
  Applying accounts.0001_initial... OK
  Applying catalog.0001_initial... OK
  Applying circulation.0001_initial... OK
  ... (more migrations)
```

### Step 1.5: Create Superuser (Admin Account)
```bash
python manage.py createsuperuser
```

**Follow prompts:**
```
Username: admin
Email address: admin@example.com
Password: Admin123!
Password (again): Admin123!
Superuser created successfully.
```

### Step 1.6: (Optional) Load Sample Data
```bash
python manage.py loaddata sample_data
```
*Only if sample data fixture exists*

### Step 1.7: Start Development Server
```bash
python manage.py runserver
```

**Expected output:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

✅ **Server should now be running on `http://localhost:8000`**

---

## Phase 2: Postman Collection Setup

### Step 2.1: Open Postman
- Launch Postman (Desktop or Web)
- Log in if required

### Step 2.2: Import the REST API Collection

**Method A: Import from File**
1. Click **Import** button (top-left)
2. Select **File**
3. Navigate to: `TS_OPAC_eLibrary_REST_API.postman_collection.json`
4. Click **Import**

**Method B: Import from Link (if available)**
1. Click **Import**
2. Paste collection URL
3. Click **Import**

### Step 2.3: Set Collection Variables

1. Click on the collection name: **TS_OPAC_eLibrary_REST_API**
2. Go to **Variables** tab
3. Set the following variables:

| Variable | Current Value | Notes |
|----------|---------------|-------|
| `base_url` | `http://localhost:8000/api` | Local development |
| `token` | (leave empty for now) | Will be populated after login |
| `user_id` | (leave empty) | Will be set after getting user info |
| `publication_id` | (leave empty) | Will be set after searching publications |

4. Click **Save**

### Step 2.4: Verify Base URL

1. Open any request in the collection
2. Check the URL bar shows: `{{base_url}}/...`
3. Postman should auto-replace with `http://localhost:8000/api/...`

✅ **Collection is now ready for testing**

---

## Phase 3: Authentication Flow

### Step 3.1: Get Authentication Token

1. **Navigate to:** Authentication → Get Auth Token
2. **Method:** POST
3. **URL:** `{{base_url}}/auth/token/`
4. **Headers:** Automatically set to `Content-Type: application/json`
5. **Body (Raw JSON):**
   ```json
   {
     "username": "admin",
     "password": "Admin123!"
   }
   ```
   *Replace with your superuser credentials*

6. **Click Send**

**Expected Response (Status: 200 OK):**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbea6f3357"
}
```

### Step 3.2: Save Token to Variable

1. Look at the response
2. Copy the token value (without quotes)
3. In Postman, click collection name → **Variables**
4. Set `token` = `9944b09199c62bcf9418ad846dd0e4bbea6f3357`
5. Click **Save**

**Now all requests will include:**
```
Authorization: Token {{token}}
```

### Step 3.3: Verify Authentication

1. **Navigate to:** Users → Get Current User Info
2. **Method:** GET
3. **URL:** `{{base_url}}/users/me/`
4. **Headers:** Authorization header should auto-populate with your token
5. **Click Send**

**Expected Response (Status: 200 OK):**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "first_name": "",
  "last_name": "",
  "user_type": "STAFF",
  "date_joined": "2025-01-15T10:30:45Z",
  "is_active": true,
  "borrower_limit": 10,
  "is_blocked": false
}
```

✅ **Authentication is working correctly**

---

## Phase 4: Core API Testing

### Step 4.1: Test Publication Types

**Request:**
1. **Navigate to:** Catalog → Publication Types → List All
2. **Method:** GET
3. **URL:** `{{base_url}}/publication-types/`
4. **Click Send**

**Check Response:**
- Status: 200 OK
- Contains array of publication types (Manual, SOP, Capstone, TTP, etc.)

### Step 4.2: Test Authors

**Request:**
1. **Navigate to:** Catalog → Authors → List All
2. **Method:** GET
3. **URL:** `{{base_url}}/authors/`
4. **Click Send**

**Check Response:**
- Status: 200 OK
- Contains array of authors

### Step 4.3: Test Subjects

**Request:**
1. **Navigate to:** Catalog → Subjects → List All
2. **Method:** GET
3. **URL:** `{{base_url}}/subjects/`
4. **Click Send**

**Check Response:**
- Status: 200 OK
- Contains array of subjects

### Step 4.4: Test Publications (Search)

**Request:**
1. **Navigate to:** Catalog → Publications → Search Publications
2. **Method:** GET
3. **URL:** `{{base_url}}/publications/?search=django&limit=10`
4. **Parameters:** 
   - `search=django` (or any keyword)
   - `limit=10` (optional, limits results)
5. **Click Send**

**Check Response:**
- Status: 200 OK
- Contains publication results with:
  - `id`, `title`, `author`, `isbn`, `call_number`
  - `available_copies`, `total_copies`
  - `cover_image_url`

### Step 4.5: Test Items (Copies)

**Request:**
1. **Navigate to:** Catalog → Items → List All Items
2. **Method:** GET
3. **URL:** `{{base_url}}/items/?limit=10`
4. **Click Send**

**Check Response:**
- Status: 200 OK
- Each item shows: `barcode`, `status`, `publication`, `location`

**Save an item ID for later testing:**
- Copy an `id` from response
- Go to Variables → Set `item_id` = that ID

---

## Phase 5: Workflow Testing

### Workflow 1: Register New User

**Step 5.1.1: Register**
1. **Navigate to:** Authentication → Register User
2. **Method:** POST
3. **URL:** `{{base_url}}/auth/register/`
4. **Body:**
   ```json
   {
     "username": "testuser1",
     "email": "testuser1@example.com",
     "password": "TestPass123!",
     "password_confirm": "TestPass123!",
     "first_name": "Test",
     "last_name": "User"
   }
   ```
5. **Click Send**

**Check Response:**
- Status: 201 Created
- Response includes `id`, `username`, `email`

**Step 5.1.2: Login as New User**
1. **Navigate to:** Authentication → Get Auth Token
2. **Body:**
   ```json
   {
     "username": "testuser1",
     "password": "TestPass123!"
   }
   ```
3. **Click Send**
4. **Copy the new token**
5. **Save to variable:** `testuser_token` = `new_token_value`

---

### Workflow 2: Borrow a Publication

**Step 5.2.1: Check Publication Availability**
1. **Navigate to:** Catalog → Publications → Get Publication Details
2. **Method:** GET
3. **URL:** `{{base_url}}/publications/1/` (or use a valid ID)
4. **Click Send**

**Check Response:**
```json
{
  "id": 1,
  "title": "Django for Beginners",
  "available_copies": 3,
  "total_copies": 5,
  ...
}
```

**Step 5.2.2: Check Availability Endpoint**
1. **Method:** GET
2. **URL:** `{{base_url}}/publications/1/availability/`
3. **Click Send**

**Response shows detailed item availability**

**Step 5.2.3: Borrow the Publication**
1. **Navigate to:** Circulation → Loans → Create Loan
2. **Method:** POST
3. **URL:** `{{base_url}}/loans/`
4. **Body:**
   ```json
   {
     "publication": 1,
     "item": 5
   }
   ```
5. **Click Send**

**Check Response (Status: 201 Created):**
```json
{
  "id": 1,
  "publication": 1,
  "item": 5,
  "borrower": 1,
  "checkout_date": "2025-01-15T10:30:45Z",
  "due_date": "2025-01-29T10:30:45Z",
  "status": "CHECKED_OUT"
}
```

---

### Workflow 3: Renew a Loan

**Step 5.3.1: Get My Loans**
1. **Navigate to:** Circulation → Loans → Get My Loans
2. **Method:** GET
3. **URL:** `{{base_url}}/loans/my_loans/`
4. **Click Send**

**Check Response:**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "publication": "Django for Beginners",
      "status": "CHECKED_OUT",
      "due_date": "2025-01-29T10:30:45Z"
    }
  ]
}
```

**Step 5.3.2: Renew Loan**
1. **Navigate to:** Circulation → Loans → Renew Loan
2. **Method:** POST
3. **URL:** `{{base_url}}/loans/1/renew/` (use actual loan ID)
4. **Body:** (empty or `{}`)
5. **Click Send**

**Check Response (Status: 200 OK):**
```json
{
  "id": 1,
  "due_date": "2025-02-12T10:30:45Z",
  "renew_count": 1
}
```

---

### Workflow 4: Place and Manage Holds

**Step 5.4.1: Check if User Can Place Hold**
1. **Navigate to:** Catalog → Publications → Get Publication Details
2. **Check:** `available_copies` and `total_copies`
3. If `available_copies < total_copies`, holds might be needed

**Step 5.4.2: Place Hold**
1. **Navigate to:** Circulation → Holds → Create Hold
2. **Method:** POST
3. **URL:** `{{base_url}}/holds/`
4. **Body:**
   ```json
   {
     "publication": 1
   }
   ```
5. **Click Send**

**Check Response (Status: 201 Created):**
```json
{
  "id": 1,
  "publication": 1,
  "borrower": 1,
  "request_date": "2025-01-15T10:30:45Z",
  "status": "PENDING",
  "queue_position": 1
}
```

**Step 5.4.3: Get My Holds**
1. **Navigate to:** Circulation → Holds → Get My Holds
2. **Method:** GET
3. **URL:** `{{base_url}}/holds/my_holds/`
4. **Click Send**

**Step 5.4.4: Cancel Hold**
1. **Navigate to:** Circulation → Holds → Delete Hold
2. **Method:** DELETE
3. **URL:** `{{base_url}}/holds/1/` (use actual hold ID)
4. **Click Send**

**Check Response (Status: 204 No Content)** - Successful deletion

---

## Phase 6: Error Debugging

### Common HTTP Status Codes

| Code | Meaning | What to Check |
|------|---------|---------------|
| 200 | OK | Request successful ✅ |
| 201 | Created | Resource created ✅ |
| 204 | No Content | Deletion successful ✅ |
| 400 | Bad Request | Check JSON format, required fields |
| 401 | Unauthorized | Token missing or expired, add Authorization header |
| 403 | Forbidden | Permission denied, check user role (admin/staff) |
| 404 | Not Found | Resource doesn't exist, check ID |
| 500 | Server Error | Check Django terminal for error logs |

### Debugging Steps

**Issue: 401 Unauthorized**
```
"detail": "Authentication credentials were not provided."
```
**Solution:**
1. Go to Variables tab
2. Verify `token` is set
3. Verify token is valid (not expired)
4. Regenerate token if needed

**Issue: 403 Forbidden**
```
"detail": "You do not have permission to perform this action."
```
**Solution:**
1. Check if endpoint requires admin/staff permissions
2. Verify user type in profile (`user_type: STAFF` for admin endpoints)
3. Use admin token instead

**Issue: 400 Bad Request**
```
"password": ["This field is required."]
```
**Solution:**
1. Check required fields in request body
2. Verify JSON syntax is valid
3. Look at response for specific field errors

**Issue: 404 Not Found**
```
"detail": "Not found."
```
**Solution:**
1. Verify the ID exists (list endpoint first)
2. Check URL spelling
3. Use correct resource ID

**Issue: 500 Server Error**
```
"detail": "Internal server error"
```
**Solution:**
1. Check Django terminal for detailed error
2. Look for Python exceptions
3. Check database connection
4. Verify migrations were run

### Django Terminal Debugging

**Watch terminal output while sending requests:**
```
[15/Jan/2025 10:30:45] "GET /api/publications/ HTTP/1.1" 200 1234
[15/Jan/2025 10:30:47] "POST /api/loans/ HTTP/1.1" 400 567
```

**For errors, you'll see:**
```
Traceback (most recent call last):
  File "...", line XXX, in YYY
    raise SomeException("error message")
```

---

## Quick Reference

### Essential URLs

| Purpose | Method | URL |
|---------|--------|-----|
| **Auth Token** | POST | `{{base_url}}/auth/token/` |
| **Register** | POST | `{{base_url}}/auth/register/` |
| **My Profile** | GET | `{{base_url}}/users/me/` |
| **All Publications** | GET | `{{base_url}}/publications/` |
| **Search Pubs** | GET | `{{base_url}}/publications/?search=keyword` |
| **Pub Details** | GET | `{{base_url}}/publications/{id}/` |
| **My Loans** | GET | `{{base_url}}/loans/my_loans/` |
| **My Holds** | GET | `{{base_url}}/holds/my_holds/` |
| **Create Loan** | POST | `{{base_url}}/loans/` |
| **Renew Loan** | POST | `{{base_url}}/loans/{id}/renew/` |
| **Create Hold** | POST | `{{base_url}}/holds/` |

### Authorization Header

**All requests (except auth/register/token) must include:**
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbea6f3357
```

In Postman:
1. Go to **Headers** tab
2. Key: `Authorization`
3. Value: `Token {{token}}`

### Postman Tips & Tricks

1. **Save Response to Variable:**
   - In request → **Tests** tab
   - Add: `pm.environment.set("token", pm.response.json().token)`

2. **Debug Request/Response:**
   - Click **Console** (bottom-left) to see full request/response

3. **Use Pre-request Scripts:**
   - Automatically set values before request
   - Example: Generate timestamps

4. **Create Postman Tests:**
   - Validate status codes
   - Check response content
   - Automate workflows

5. **Export Results:**
   - Right-click collection → **Export**
   - Share test results

---

## Troubleshooting Checklist

- [ ] Django server running on `http://localhost:8000`
- [ ] Database migrations applied (`python manage.py migrate`)
- [ ] Superuser created (`python manage.py createsuperuser`)
- [ ] Postman collection imported
- [ ] Collection variables set (`base_url`, `token`)
- [ ] Authentication token obtained and valid
- [ ] All required headers included
- [ ] Request body valid JSON format
- [ ] No typos in endpoint URLs

---

## Next Steps

✅ **After completing all phases:**
1. Document any custom workflows
2. Create regression test suite in Postman
3. Save successful requests as templates
4. Export collection for team sharing
5. Set up monitoring/alerting for production API

---

**Last Updated:** December 25, 2025  
**Project:** TS OPAC eLibrary  
**API Version:** v1

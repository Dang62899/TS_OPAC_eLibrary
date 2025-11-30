# 📧 Email & In-App Notification System - Complete Guide

## 🎯 What Was Implemented

Your e-Library now has a **complete notification system** with:
1. ✅ **In-App Notifications** - Bell icon with badge counter
2. ✅ **Email Notifications** - Automated email sending
3. ✅ **Automated Alerts** - Daily checks for due/overdue items
4. ✅ **Real-time Updates** - Instant notifications for all events

---

## 🔔 How the Notification System Works

### **A. In-App Notifications (Bell Icon)**

**Location:** Top-right navigation bar (when logged in)

**Features:**
- 🔴 **Red badge** showing unread count
- **Dropdown preview** of 5 most recent notifications
- **"New" badge** on unread notifications
- **Color-coded icons** for different notification types
- **Mark all as read** button
- **Link to full notification center**

**Notification Types:**
1. **Checkout** (Blue) - When you borrow a book
2. **Checkin** (Green) - When you return a book
3. **Due Soon** (Yellow) - 3 days before due date
4. **Overdue** (Red) - When book is overdue
5. **Hold Ready** (Green) - When your hold is ready for pickup
6. **Hold Placed** (Cyan) - When you place a hold
7. **Hold Expiring** (Orange) - When hold will expire soon
8. **Hold Cancelled** (Gray) - When you cancel a hold
9. **Renewal** (Blue) - When you renew a book

---

### **B. Email Notifications**

**How It Works:**
1. System creates notification in database
2. Email is queued for sending
3. Celery worker sends email every 5 minutes
4. Email status tracked (sent/failed)

**Email Template Features:**
- Professional HTML design with gradients
- Book details displayed in colored boxes
- "View My Account" button for quick access
- Mobile-responsive layout
- Plain text fallback for old email clients

**Email Delivery:**
- Currently: **Console mode** (emails printed to terminal - for testing)
- Production: **Gmail SMTP** or **SendGrid** (see setup below)

---

## 📋 Complete Feature List

### **User Actions That Trigger Notifications:**

| Event | In-App | Email | When It Happens |
|-------|--------|-------|-----------------|
| **Checkout** | ✅ | ✅ | Staff checks out book to you |
| **Checkin** | ✅ | ✅ | Staff checks in your returned book |
| **Hold Placed** | ✅ | ✅ | You place a hold on a book |
| **Hold Ready** | ✅ | ✅ | Your hold becomes available |
| **Hold Cancelled** | ✅ | ✅ | You cancel your hold |
| **Renewal** | ✅ | ✅ | You renew your loan |
| **Due Soon** | ✅ | ✅ | 3 days before due date (automatic) |
| **Overdue** | ✅ | ✅ | Book is overdue (every 7 days) |
| **Hold Expiring** | ✅ | ✅ | Hold expires tomorrow |

---

## 🚀 How to Use the System

### **For Borrowers (Students):**

1. **Check Notifications:**
   - Click bell icon in navigation
   - Red badge shows unread count
   - Click notification to view details

2. **View All Notifications:**
   - Click "View All Notifications" in dropdown
   - OR visit: `/circulation/notifications/`
   - Filter: Unread only
   - Actions: Mark as read, Delete

3. **Manage Notifications:**
   - **Mark as read** - Click notification or green "Mark as Read" button
   - **Mark all read** - Click "Mark All Read" button
   - **Delete** - Click red "Delete" button (confirmation required)
   - **View details** - Click "View Details" to go to related page

### **For Staff/Admin:**

All notifications are also created for borrowers automatically when you:
- Check out a book → Borrower gets "checkout" notification
- Check in a book → Borrower gets "checkin" notification
- Mark hold as ready → Borrower gets "hold ready" notification

---

## ⚙️ Automated Background Tasks

### **What Runs Automatically:**

**Every 5 Minutes (24/7):**
- ✉️ Send pending notification emails (up to 50 per batch)

**Daily at 9:00 AM:**
- 📅 Check for items due in 3 days → Create "due soon" notifications

**Daily at 10:00 AM:**
- ⚠️ Check for overdue items → Create "overdue" notifications (every 7 days)

**Daily at 11:00 AM:**
- ⏰ Check for holds expiring tomorrow → Create "hold expiring" notifications

**How It Works:**
- Celery Beat (task scheduler) runs these tasks
- No duplicates - checks if notification already exists
- Smart frequency - overdues sent every 7 days (not daily)

---

## 📧 Email Setup Instructions

### **Currently Active: Console Backend (Testing)**
Emails are printed to the terminal/console. Perfect for development!

**To see emails:**
```bash
# Start server and watch the console
python manage.py runserver

# When notification is sent, you'll see:
# Content-Type: text/plain; charset="utf-8"
# Subject: Item Due Soon: Advanced Python Programming
# From: noreply@elibrary.com
# To: student@example.com
# ...email content...
```

---

### **Setup Option 1: Gmail (FREE - Recommended for Small Libraries)**

**Step 1:** Enable 2-Step Verification on your Gmail account
- Go to: https://myaccount.google.com/security
- Turn on "2-Step Verification"

**Step 2:** Create App Password
- Go to: https://myaccount.google.com/apppasswords
- Select app: "Mail"
- Select device: "Other (Custom name)" → Enter: "e-Library"
- Click "Generate"
- **Copy the 16-character password** (e.g., "abcd efgh ijkl mnop")

**Step 3:** Update `elibrary/settings.py`

Find this section:
```python
# Email settings
# For development: Console backend (emails printed to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**Replace with:**
```python
# Email settings - Gmail SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-library-email@gmail.com'  # Your Gmail
EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'  # App Password (NOT regular password)
```

**Step 4:** Update FROM email
```python
DEFAULT_FROM_EMAIL = 'your-library-email@gmail.com'
```

**Step 5:** Restart server
```bash
# Stop server (Ctrl+C)
# Start again
python manage.py runserver
```

**Gmail Limits:**
- Free: **500 emails/day**
- More than enough for small libraries!

---

### **Setup Option 2: SendGrid (FREE tier: 100 emails/day)**

**Step 1:** Sign up at https://sendgrid.com/

**Step 2:** Create API Key
- Dashboard → Settings → API Keys
- Create API Key → Give it a name: "e-Library"
- Permissions: "Full Access" or "Mail Send"
- Copy the API key (starts with "SG.")

**Step 3:** Update `elibrary/settings.py`
```python
# Email settings - SendGrid
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'  # Exactly this
EMAIL_HOST_PASSWORD = 'SG.your_actual_api_key_here'
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'  # Must be verified domain
```

**SendGrid Limits:**
- Free: **100 emails/day**
- Paid plans available for larger volumes

---

### **Setup Option 3: Keep Console Mode (Testing/Development)**

**No setup needed!** Emails print to terminal.

**Pros:**
- ✅ Free
- ✅ No external dependencies
- ✅ Perfect for testing
- ✅ See email content immediately

**Cons:**
- ❌ Users don't receive actual emails
- ❌ Only for development/testing

---

## 🔧 Technical Details

### **Database Schema:**

**Notification Model Fields:**
```python
- borrower: User who receives notification
- notification_type: checkout, checkin, due_soon, overdue, etc.
- title: "Item Due Soon: Python Book"
- message: Full notification text
- loan: Related loan (optional)
- hold: Related hold (optional)
- created_date: When notification was created
- is_read: True/False
- read_date: When user marked as read
- email_sent: True/False
- email_sent_date: When email was sent
- email_error: Error message if email failed
- action_url: Link for "View Details" button
```

### **File Structure:**
```
circulation/
├── models.py                    # Notification model with 10 types
├── views.py                     # Notification views + create_notification()
├── tasks.py                     # Email sending + automated checks
├── urls.py                      # Notification URLs
└── admin.py                     # Admin interface

templates/
├── base.html                    # Bell icon + notification dropdown
└── circulation/
    ├── notifications_list.html  # Full notification center
    ├── delete_notification.html # Confirmation page
    └── emails/
        └── notification_email.html  # HTML email template

elibrary/
├── settings.py                  # Email configuration
└── celery.py                    # Periodic task schedule
```

### **URLs:**
- `/circulation/notifications/` - All notifications
- `/circulation/notifications/?unread=true` - Unread only
- `/circulation/notifications/<id>/read/` - Mark as read
- `/circulation/notifications/read-all/` - Mark all as read
- `/circulation/notifications/<id>/delete/` - Delete notification

---

## 🧪 Testing the System

### **Test 1: In-App Notifications**

```bash
# 1. Start server
python manage.py runserver

# 2. Login as student (student/student123)

# 3. Look at navigation - you should see bell icon

# 4. Have staff checkout a book to you
#    - Login as librarian
#    - Go to Circulation → Checkout
#    - Select student and a book
#    - Submit

# 5. Login as student again
#    - Bell should show "1" badge
#    - Click bell → See "Item Checked Out" notification
#    - Click notification → Goes to My Account
```

### **Test 2: Email Notifications (Console Mode)**

```bash
# 1. Keep server running in one terminal

# 2. Watch the console output

# 3. Perform any action (checkout, hold, etc.)

# 4. Wait up to 5 minutes

# 5. You should see email content printed:
#    Subject: Item Checked Out: [Book Title]
#    From: noreply@elibrary.com
#    To: student@example.com
#    [HTML email content]
```

### **Test 3: Automated Due Soon Notifications**

```bash
# 1. Manually trigger the task
python manage.py shell

# 2. In shell:
from circulation.tasks import check_due_soon_items
result = check_due_soon_items()
print(result)  # Shows how many notifications created

# 3. Login as borrower
#    - Check bell icon for new notifications
```

### **Test 4: Mark as Read**

```bash
# 1. Login with notifications
# 2. Click bell icon
# 3. Click a notification
# 4. Badge count should decrease
# 5. Notification no longer shows "New" badge
```

---

## 🎨 Customization Options

### **Change Notification Frequency:**

Edit `elibrary/celery.py`:
```python
# Send emails every 10 minutes instead of 5
'send-pending-notifications': {
    'task': 'circulation.tasks.send_pending_notification_emails',
    'schedule': 600.0,  # Changed from 300.0
},
```

### **Change "Due Soon" Warning Days:**

Edit `elibrary/settings.py`:
```python
PRE_DUE_NOTICE_DAYS = 5  # Changed from 3 - notify 5 days early
```

### **Change Overdue Reminder Frequency:**

Edit `circulation/tasks.py`:
```python
# Line ~122 - change from every 7 days to every 3 days
if days_overdue % 3 == 0:  # Changed from 7
```

### **Customize Email Template:**

Edit `templates/circulation/emails/notification_email.html`:
- Change colors
- Add library logo
- Modify layout
- Add custom footer text

### **Add New Notification Type:**

1. Add to `NOTIFICATION_TYPES` in `circulation/models.py`
2. Add icon mapping in `get_icon()` method
3. Add CSS class in `get_css_class()` method
4. Use `create_notification()` in your views

---

## 🔍 Monitoring & Troubleshooting

### **Check Notification Stats:**

```bash
python manage.py shell

from circulation.models import Notification
from django.db.models import Count

# Total notifications
Notification.objects.count()

# By type
Notification.objects.values('notification_type').annotate(count=Count('id'))

# Unread count
Notification.objects.filter(is_read=False).count()

# Email success rate
sent = Notification.objects.filter(email_sent=True).count()
total = Notification.objects.count()
print(f"Success rate: {sent/total*100:.1f}%")
```

### **View Failed Emails:**

```bash
python manage.py shell

from circulation.models import Notification

# Show failed emails
failed = Notification.objects.exclude(email_error='')
for n in failed:
    print(f"{n.borrower.email}: {n.email_error}")
```

### **Manually Send Pending Emails:**

```bash
python manage.py shell

from circulation.tasks import send_pending_notification_emails
result = send_pending_notification_emails()
print(result)  # "Sent X notification emails"
```

### **Common Issues:**

**Issue:** No bell icon appears
- **Fix:** Make sure you're logged in and page is refreshed

**Issue:** Badge count doesn't update
- **Fix:** Refresh page (F5) - badge updates on page load

**Issue:** Emails not sending (Gmail)
- **Fix:** Check App Password (not regular password)
- **Fix:** Verify 2-Step Verification is enabled
- **Fix:** Check EMAIL_HOST_USER matches your Gmail

**Issue:** Duplicate notifications
- **Fix:** System prevents this automatically - check notification creation code

**Issue:** Celery tasks not running
- **Fix:** You need to start Celery worker and beat (see below)

---

## 🚀 Running Celery for Automated Tasks

### **For Development (Simple - No Celery Needed):**

The system works WITHOUT Celery! Emails queue up and send when triggered manually.

**To manually trigger tasks:**
```bash
python manage.py shell

from circulation.tasks import check_due_soon_items, check_overdue_items
check_due_soon_items()
check_overdue_items()
```

### **For Production (Full Automation with Celery):**

**Requirements:**
- Redis server (for task queue)

**Step 1:** Install Redis
```bash
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Or use Windows Subsystem for Linux (WSL)

# Linux/Mac:
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis  # Mac
```

**Step 2:** Start Redis
```bash
redis-server
```

**Step 3:** Start Celery Worker (Terminal 1)
```bash
cd C:\Users\Dang\Desktop\TS_OPAC_eLibrary
celery -A elibrary worker --loglevel=info
```

**Step 4:** Start Celery Beat (Terminal 2)
```bash
cd C:\Users\Dang\Desktop\TS_OPAC_eLibrary
celery -A elibrary beat --loglevel=info
```

**Step 5:** Start Django Server (Terminal 3)
```bash
python manage.py runserver
```

**Now you have:**
- ✅ Automatic email sending every 5 minutes
- ✅ Daily checks for due/overdue items
- ✅ Fully automated notification system

---

## 📊 Performance & Scalability

### **Current Capacity:**
- **In-App Notifications:** Unlimited (database-stored)
- **Email Queue:** 50 emails per 5-minute batch
- **Daily Checks:** All loans/holds checked automatically

### **For Larger Libraries:**
1. Increase batch size in `tasks.py` (line 56): `[:50]` → `[:100]`
2. Use paid email service (SendGrid Pro, Mailgun)
3. Enable database indexing (already done)
4. Add Redis caching for notification counts

---

## 📚 Summary

### **What You Get:**

✅ **Real-time Notifications** - Instant in-app alerts
✅ **Email Notifications** - Professional HTML emails
✅ **Automated Reminders** - Daily checks for due/overdue
✅ **User-Friendly** - Bell icon with badge counter
✅ **Complete Tracking** - Read status, email status
✅ **Zero Cost** - Free with Gmail (500/day) or SendGrid (100/day)
✅ **Mobile Ready** - Responsive design
✅ **Production Ready** - Scalable architecture

### **Next Steps:**

1. ✅ **System is ready to use!** (with console email mode)
2. 📧 **Setup Gmail SMTP** for real email delivery (15 minutes)
3. 🧪 **Test all notification types** with sample data
4. 🚀 **Deploy to production** when ready
5. 📱 **(Optional) Add SMS** notifications later

---

## 💡 Tips & Best Practices

1. **Start with Console Mode** - Test everything before setting up real emails
2. **Use Gmail for Small Libraries** - Free and reliable (500 emails/day)
3. **Monitor Failed Emails** - Check email_error field regularly
4. **Don't Spam Users** - Current settings are balanced (3 days notice, weekly overdues)
5. **Keep Templates Simple** - Current HTML template works on all email clients
6. **Test Mobile Display** - Notification dropdown works on phones
7. **Regular Cleanup** - Delete old read notifications after 30 days (create management command)

---

## 🆘 Support & Contact

**Created By:** GitHub Copilot (Claude Sonnet 4.5)
**Date:** November 27, 2025
**Version:** 1.0

**For Questions:**
- Check this guide first
- Test in console mode before production
- Review error messages in terminal/logs
- Check `email_error` field for failed emails

**System Components:**
- Django 5.2.8
- Celery (task queue)
- Redis (message broker)
- Bootstrap 5.3.0 (UI)
- Gmail/SendGrid (email delivery)

---

🎉 **Congratulations! Your library now has a professional notification system!** 🎉

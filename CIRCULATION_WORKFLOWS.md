# CIRCULATION WORKFLOWS - COMPLETE GUIDE

## Overview
Your e-Library system now has two complete reservation/pickup workflows:
1. **Checkout Requests** - For books that are currently available
2. **Holds** - For books that are currently unavailable (all copies checked out)

---

## WORKFLOW 1: CHECKOUT REQUESTS (For Available Books)

### Student Actions:
1. Browse catalog and find a book they want
2. Click "Request This Book" button (only shows if book has available copies)
3. Fill out request form with preferred pickup location
4. Submit request → Status: **PENDING**
5. Wait for staff approval notification

### Staff Actions (Approve Request):
1. Login as admin/staff
2. Go to "Circulation" → "Checkout Requests"
3. Click on pending request
4. Click "Approve Request"
5. Set pickup location and pickup deadline
6. Submit → Status changes to **APPROVED**
7. System sends notification to student

### Student Gets Notified:
- Receives notification: "Request Approved"
- Shows pickup location and deadline
- Can view details in "My Account" page

### Staff Actions (Complete Pickup):
1. When student arrives to pick up the book
2. Go to "Circulation" → "Checkout Requests" → filter by "Approved"
3. Click "Complete Pickup" for the student's request
4. **Select the specific item** from dropdown (shows Item ID and location)
5. Submit → Creates loan, changes item status to `on_loan`
6. Status changes to **COMPLETED**
7. System sends checkout notification to student

### Key Points:
- Only works for publications with available copies
- Staff must approve before student can pick up
- Item is not reserved until staff selects it during completion
- If all items become unavailable after approval, completion will fail

---

## WORKFLOW 2: HOLDS (For Unavailable Books)

### Student Actions:
1. Browse catalog and find a book they want
2. All copies are currently checked out → "Place Hold" button shows
3. Click "Place Hold"
4. Select preferred pickup location
5. Submit → Status: **WAITING**
6. System shows queue position

### Automatic Hold Processing (When Item Returned):
1. Another student returns one copy of the book
2. Staff checks in the item using "Check In" form
3. **System automatically**:
   - Finds first waiting hold for that book
   - Changes item status to `on_hold_shelf`
   - Changes hold status to **READY**
   - Sets ready_date
   - Sends "Hold Ready" notification to student

### Manual Hold Processing (If item manually returned to shelf):
1. Staff can manually mark a hold as ready
2. Go to "Circulation" → "Manage Holds"
3. Click "Set Ready" for a waiting hold
4. **System checks if item is actually available**
5. If available: reserves item, moves to hold shelf, sends notification
6. If not available: shows error message

### Student Gets Notified:
- Receives notification: "Hold Ready for Pickup"
- Shows pickup location and expiry date
- Can view details in "My Account" page

### Staff Actions (Complete Pickup):
1. When student arrives to pick up the held book
2. Go to "Circulation" → "Manage Holds"
3. Click "Complete Pickup" for the ready hold
4. **Select the specific item** from dropdown (should show item on hold shelf)
5. Submit → Creates loan, changes item to `on_loan`
6. Hold status changes to **FULFILLED**
7. System sends checkout notification to student

### Key Points:
- Only works for publications with NO available copies
- Items are automatically reserved when returned
- Hold expires after pickup deadline
- First in queue gets the book first (by hold_date)

---

## ITEM STATUS FLOW

### Available Book → Checkout Request:
```
available → (staff completes pickup) → on_loan → (returned) → available
```

### Unavailable Book → Hold:
```
on_loan → (returned + hold waiting) → on_hold_shelf → (pickup completed) → on_loan
```

### Possible Item Statuses:
- `available` - Ready to be borrowed
- `on_loan` - Currently checked out to a borrower
- `on_hold_shelf` - Reserved for someone with a hold
- `in_transit` - Moving between locations (future use)
- `processing` - Being cataloged/repaired (future use)
- `missing` - Cannot be found
- `damaged` - Needs repair

---

## REQUEST/HOLD STATUS FLOW

### Checkout Request Statuses:
- `pending` - Waiting for staff review
- `approved` - Staff approved, waiting for student pickup
- `completed` - Student picked up, loan created
- `denied` - Staff rejected the request
- `cancelled` - Student cancelled before pickup

### Hold Statuses:
- `waiting` - In queue, waiting for item to become available
- `ready` - Item on hold shelf, ready for pickup
- `fulfilled` - Student picked up, loan created
- `cancelled` - Student cancelled the hold
- `expired` - Pickup deadline passed

---

## TESTING SCENARIOS

### Test Data Created (IDs 44-48):

1. **Publication 44**: "Available Book - Ready to Request"
   - 2 items: AVAIL-001 (available), AVAIL-002 (available)
   - **Test**: Create checkout request → Approve → Complete pickup
   - **Expected**: Should work smoothly

2. **Publication 45**: "Partial Availability Book"
   - 2 items: PARTIAL-001 (available), PARTIAL-002 (on_loan)
   - **Test**: Create checkout request OR place hold
   - **Expected**: Both workflows available

3. **Publication 46**: "Unavailable Book - All Copies On Loan"
   - 3 items: ALL ON LOAN
   - **Test**: Place hold → Check in one copy → Complete pickup
   - **Expected**: Hold automatically becomes ready when item returned

4. **Publication 47**: "Popular Book - Multiple Copies"
   - 5 items: 1 available, 4 on loan
   - **Test**: Create checkout request → Test with multiple holds
   - **Expected**: Can request available copy, holds wait for returns

5. **Publication 48**: "Single Copy Book - Currently Unavailable"
   - 1 item: SINGLE-001 (on_loan)
   - **Test**: Place hold → Check in → Complete pickup
   - **Expected**: Simple hold workflow

---

## NOTIFICATIONS

Students receive notifications for:
1. Checkout request approved
2. Checkout request denied
3. Hold ready for pickup
4. Hold cancelled
5. Hold expired
6. Item checked out (loan created)
7. Item returned
8. Overdue reminder
9. Overdue final notice
10. Pickup reminder (for ready holds)

All notifications appear:
- In "My Account" page (Notifications tab)
- Via email (if configured)

---

## TROUBLESHOOTING

### "No available items found"
**Cause**: All items are currently on loan or not on hold shelf
**Solution**: 
- For checkout requests: Wait for an item to be returned
- For holds: Check if item was properly checked in and moved to hold shelf

### Hold marked ready but no items available
**Cause**: Old issue - staff manually marked hold ready without checking item availability
**Solution**: Now fixed - system validates item availability before marking ready

### Checkout request approved but student can't pick up
**Cause**: Items were all checked out between approval and pickup attempt
**Solution**: Staff should check current availability before approving, or system should reserve item during approval

### Item on hold shelf but different student wants to borrow it
**Cause**: Item reserved for someone with a hold
**Solution**: Only that specific borrower can check out that item; other students must place their own hold

---

## FUTURE ENHANCEMENTS

1. **Reserve item during request approval**: When approving checkout request, automatically select and reserve a specific item
2. **Multiple pickup locations**: Support for transferring items between libraries
3. **Email configuration**: Set up email sending for notifications
4. **Overdue fine calculation**: Track and calculate late fees
5. **Renewal system**: Allow students to renew loans if no holds exist
6. **Barcode scanner integration**: Optional feature. By default barcode scanning is disabled; re-enable when scanner equipment is available and `BARCODE_ENABLED` is set.
7. **Statistics dashboard**: Track popular books, busiest times, etc.

---

## ADMIN QUICK REFERENCE

### Daily Tasks:
- Review pending checkout requests
- Complete pickups for approved requests/ready holds
- Check in returned items
- Check overdue report

### Weekly Tasks:
- Review waiting holds - check if items available
- Clear expired holds
- Review borrower blocks

### Navigation:
- Dashboard: `/circulation/`
- Checkout Requests: `/circulation/checkout-requests/`
- Manage Holds: `/circulation/holds/manage/`
- Check Out: `/circulation/checkout/`
- Check In: `/circulation/checkin/`
- Borrowers: `/circulation/borrowers/`
- Reports: `/circulation/reports/`

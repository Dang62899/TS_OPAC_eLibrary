from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.db.models import Q, Count
import logging
from datetime import timedelta
from .models import Loan, Hold, InTransit, Notification, CheckoutRequest
from .forms import (
    CheckoutForm,
    CheckinForm,
    HoldForm,
    InTransitForm,
    BorrowerSearchForm,
)
from django.db.models import F, Value
from django.db.models.functions import Replace
from catalog.models import Item, Publication, Location
from accounts.models import User


def is_staff_user(user):
    """Check if user is staff"""
    return user.is_authenticated and user.user_type in ['staff', 'admin']

@login_required
@user_passes_test(is_staff_user)


def circulation_dashboard(request):
    """Staff circulation dashboard"""
    today = timezone.now().date()

    # Statistics
    active_loans = Loan.objects.filter(status='active').count()
    overdue_loans = Loan.objects.filter(
        status='active',
        due_date__lt=today
    ).count()
    holds_waiting = Hold.objects.filter(status='waiting').count()
    holds_ready = Hold.objects.filter(status='ready').count()
    items_in_transit = InTransit.objects.filter(status='in_transit').count()

    # Recent activity
    recent_checkouts = Loan.objects.filter(
        checkout_date__gte=timezone.now() - timedelta(days=1)
    ).select_related('item__publication', 'borrower')[:10]

    recent_returns = Loan.objects.filter(
        return_date__gte=timezone.now() - timedelta(days=1),
        status__in=['returned', 'overdue_returned']
    ).select_related('item__publication', 'borrower')[:10]

    context = {
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
        'holds_waiting': holds_waiting,
        'holds_ready': holds_ready,
        'items_in_transit': items_in_transit,
        'recent_checkouts': recent_checkouts,
        'recent_returns': recent_returns,
    }
    return render(request, 'circulation/dashboard.html', context)

@login_required
@user_passes_test(is_staff_user)


def checkout(request):
    """Check out an item to a borrower"""
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.item = form.cleaned_data['item']
            loan.borrower = form.cleaned_data['borrower']
            loan.checkout_staff = request.user
            loan.save()

            # Update item statistics
            loan.item.times_borrowed += 1
            loan.item.last_borrowed_date = timezone.now()
            loan.item.save()

            # Create notification
            create_notification(
                borrower=loan.borrower,
                notification_type='checkout',
                title=f'Item Checked Out: {loan.item.publication.title}',
                message=f'You have successfully borrowed "{loan.item.publication.title}". Due date: {loan.due_date.strftime("%B %d, %Y")}. Please return on time to avoid late fees.',
                loan=loan,
                action_url='/accounts/my-account/'
            )

            messages.success(request, f"Item checked out successfully. Due date: {loan.due_date}")
            return redirect('circulation:checkout')
    else:
        form = CheckoutForm()

    return render(request, 'circulation/checkout.html', {'form': form})

@login_required
@user_passes_test(is_staff_user)


def checkin(request):
    """Check in a returned item"""
    if request.method == 'POST':
        form = CheckinForm(request.POST)
        if form.is_valid():
            loan = form.cleaned_data['loan']
            loan.return_date = timezone.now()
            loan.return_staff = request.user

            # Check if overdue
            was_overdue = False
            if loan.is_overdue():
                loan.status = 'overdue_returned'
                was_overdue = True
                messages.warning(request, f"Item was {loan.days_overdue()} day(s) overdue.")
            else:
                loan.status = 'returned'

            loan.save()

            # Create return notification
            create_notification(
                borrower=loan.borrower,
                notification_type='checkin',
                title=f'Item Returned: {loan.item.publication.title}',
                message=(
                    f"Thank you for returning \"{loan.item.publication.title}\". "
                    + ("Item was returned late." if was_overdue else "Item was returned on time.")
                ),
                loan=loan,
                action_url='/accounts/my-account/'
            )

            # Check if there's a hold on this item
            hold = Hold.objects.filter(
                publication=loan.item.publication,
                status='waiting'
            ).order_by('hold_date').first()

            if hold:
                hold.status = 'ready'
                hold.save()
                loan.item.status = 'on_hold_shelf'
                loan.item.save()

                # Create hold ready notification
                create_notification(
                    borrower=hold.borrower,
                    notification_type='hold_ready',
                    title=f'Hold Ready for Pickup: {hold.publication.title}',
                    message=f'Your hold for "{hold.publication.title}" is ready for pickup at {hold.pickup_location}. Please pick it up by {hold.expiry_date.strftime("%B %d, %Y")}.',
                    hold=hold,
                    action_url='/accounts/my-account/'
                )

                messages.info(request, f"Item placed on hold shelf for {hold.borrower}")

            messages.success(request, "Item checked in successfully.")
            return redirect('circulation:checkin')
    else:
        form = CheckinForm()

    return render(request, 'circulation/checkin.html', {'form': form})

@login_required
@user_passes_test(is_staff_user)


def renew_loan(request, loan_id):
    """Renew a loan (staff interface)"""
    loan = get_object_or_404(Loan, pk=loan_id)

    if loan.renew():
        messages.success(request, f"Loan renewed. New due date: {loan.due_date}")
    else:
        if loan.renewal_count >= 2:
            messages.error(request, "Maximum renewals reached.")
        elif loan.is_overdue():
            messages.error(request, "Cannot renew overdue item.")
        else:
            messages.error(request, "Cannot renew. Item may have holds.")

    return redirect('circulation:borrower_detail', user_id=loan.borrower.id)

@login_required


def renew_loan_online(request, loan_id):
    """Renew a loan (borrower interface)"""
    loan = get_object_or_404(Loan, pk=loan_id, borrower=request.user)

    if loan.renew():
        # Create renewal notification
        create_notification(
            borrower=loan.borrower,
            notification_type='renewal',
            title=f'Item Renewed: {loan.item.publication.title}',
            message=f'Your loan for "{loan.item.publication.title}" has been renewed. New due date: {loan.due_date.strftime("%B %d, %Y")}.',
            loan=loan,
            action_url='/accounts/my-account/'
        )
        messages.success(request, f"Item renewed. New due date: {loan.due_date}")
    else:
        if loan.renewal_count >= 2:
            messages.error(request, "Maximum renewals reached.")
        elif loan.is_overdue():
            messages.error(request, "Cannot renew overdue item.")
        else:
            messages.error(request, "Cannot renew. Item may have holds.")

    return redirect('accounts:my_account')

@login_required


def place_hold(request, publication_id):
    """Place a hold on a publication"""
    publication = get_object_or_404(Publication, pk=publication_id)

    # Check if user already has a hold
    existing_hold = Hold.objects.filter(
        publication=publication,
        borrower=request.user,
        status__in=['waiting', 'ready']
    ).first()

    if existing_hold:
        messages.warning(request, "You already have a hold on this item.")
        return redirect('catalog:publication_detail', pk=publication_id)

    if request.method == 'POST':
        form = HoldForm(request.POST)
        if form.is_valid():
            hold = form.save(commit=False)
            hold.publication = publication
            hold.borrower = request.user
            hold.save()
            hold.update_queue_position()

            # Create hold placed notification
            create_notification(
                borrower=request.user,
                notification_type='hold_placed',
                title=f'Hold Placed: {publication.title}',
                message=f'Your hold for "{publication.title}" has been placed successfully. Queue position: #{hold.queue_position}. We will notify you when it is ready for pickup.',
                hold=hold,
                action_url='/accounts/my-account/'
            )

            messages.success(request, f"Hold placed successfully. Your position in queue: {hold.queue_position}")
            return redirect('catalog:publication_detail', pk=publication_id)
    else:
        form = HoldForm()

    context = {
        'publication': publication,
        'form': form,
    }
    return render(request, 'circulation/place_hold.html', context)

@login_required


def cancel_hold(request, hold_id):
    """Cancel a hold"""
    hold = get_object_or_404(Hold, pk=hold_id, borrower=request.user)
    publication_title = hold.publication.title

    if hold.status in ['waiting', 'ready']:
        hold.status = 'cancelled'
        hold.save()

        # Create hold cancelled notification
        create_notification(
            borrower=request.user,
            notification_type='hold_cancelled',
            title=f'Hold Cancelled: {publication_title}',
            message=f'Your hold for "{publication_title}" has been cancelled.',
            hold=hold,
            action_url='/accounts/my-account/'
        )
        messages.success(request, "Hold cancelled successfully.")
    else:
        messages.error(request, "This hold cannot be cancelled.")

    return redirect('accounts:my_account')

@login_required
@user_passes_test(is_staff_user)


def manage_holds(request):
    """Manage hold requests"""
    waiting_holds = Hold.objects.filter(status='waiting').select_related(
        'publication', 'borrower', 'pickup_location'
    ).order_by('publication', 'hold_date')

    ready_holds = Hold.objects.filter(status='ready').select_related(
        'publication', 'borrower', 'pickup_location'
    ).order_by('ready_date')

    context = {
        'waiting_holds': waiting_holds,
        'ready_holds': ready_holds,
    }
    return render(request, 'circulation/manage_holds.html', context)

@login_required
@user_passes_test(is_staff_user)


def set_hold_ready(request, hold_id):
    """Mark a hold as ready for pickup - only if an item is available"""
    hold = get_object_or_404(Hold, pk=hold_id)
    logger = logging.getLogger(__name__)
    if hold.status == 'waiting':
        # Reserve an available item inside a transaction to avoid races
        try:
            with transaction.atomic():
                available_qs = Item.objects.select_for_update().filter(
                    publication=hold.publication,
                    status__in=['available', 'on_hold_shelf']
                )
                item = available_qs.first()
                if not item:
                    messages.error(request, "Cannot mark hold as ready - no available items found for this publication.")
                    return redirect('circulation:manage_holds')

                item.status = 'on_hold_shelf'
                item.save()

                hold.status = 'ready'
                hold.ready_date = timezone.now()
                # Set expiry/pickup-by date for the hold (default 7 days)
                pickup_days = getattr(settings, 'HOLD_PICKUP_DAYS', 7)
                hold.expiry_date = timezone.now() + timedelta(days=pickup_days)
                hold.save()

        except Exception as e:
            logger.exception("Error reserving item for hold %s: %s", hold_id, e)
            messages.error(request, "An error occurred while reserving an item for this hold.")
            return redirect('circulation:manage_holds')

        # Create hold ready notification
        create_notification(
            borrower=hold.borrower,
            notification_type='hold_ready',
            title=f'Hold Ready for Pickup: {hold.publication.title}',
            message=f'Your hold for "{hold.publication.title}" is ready for pickup at {hold.pickup_location}. Please pick it up by {hold.expiry_date.strftime("%B %d, %Y")}.',
            hold=hold,
            action_url='/accounts/my-account/'
        )

        messages.success(request, f"Hold marked as ready for {hold.borrower}. Item {item.barcode} placed on hold shelf.")
    else:
        messages.warning(request, f"Hold is already {hold.status}.")

    return redirect('circulation:manage_holds')

@login_required
@user_passes_test(is_staff_user)


def complete_hold(request, hold_id):
    """Complete a hold by checking out the item to the borrower"""
    hold = get_object_or_404(Hold, pk=hold_id)

    if hold.status != 'ready':
        messages.error(request, "This hold is not ready for pickup.")
        return redirect('circulation:manage_holds')

    if request.method == 'POST':
        item_identifier = request.POST.get('item_identifier', '').strip()

        if not item_identifier:
            messages.error(request, "Please select an item.")
            available_items = Item.objects.filter(
                publication=hold.publication,
                status__in=['available', 'on_hold_shelf']
            ).select_related('location')
            return render(request, 'circulation/complete_hold.html', {
                'hold': hold,
                'available_items': available_items
            })

        try:
            # Reserve & create loan atomically
            with transaction.atomic():
                item = Item.objects.select_for_update().get(
                    id=item_identifier,
                    publication=hold.publication,
                    status__in=['available', 'on_hold_shelf']
                )

                # Check borrower eligibility
                if hold.borrower.is_blocked:
                    messages.error(request, f"{hold.borrower.get_full_name()} is currently blocked from borrowing.")
                    return redirect('circulation:manage_holds')

                if hold.borrower.get_active_loans_count() >= hold.borrower.max_items_allowed:
                    messages.error(request, f"{hold.borrower.get_full_name()} has reached their borrowing limit.")
                    return redirect('circulation:manage_holds')

                # Create the loan with default 14-day period
                loan_period = 14
                due_date = timezone.now() + timedelta(days=loan_period)

                loan = Loan.objects.create(
                    item=item,
                    borrower=hold.borrower,
                    checkout_staff=request.user,
                    checkout_date=timezone.now(),
                    due_date=due_date,
                    status='active'
                )

                # Update item
                item.status = 'on_loan'
                item.times_borrowed += 1
                item.last_borrowed_date = timezone.now()
                item.save()

                # Update hold
                hold.status = 'fulfilled'
                hold.save()

        except Item.DoesNotExist:
            messages.error(request, "No available item found for this publication.")
            available_items = Item.objects.filter(
                publication=hold.publication,
                status__in=['available', 'on_hold_shelf']
            ).select_related('location')
            return render(request, 'circulation/complete_hold.html', {
                'hold': hold,
                'available_items': available_items
            })

        messages.success(
            request,
            f"Hold completed! Item checked out to {hold.borrower.get_full_name()}. Due: {loan.due_date.strftime('%B %d, %Y')}"
        )
        return redirect('circulation:manage_holds')

    # GET request - show form
    available_items = Item.objects.filter(
        publication=hold.publication,
        status__in=['available', 'on_hold_shelf']
    ).select_related('location')

    context = {
        'hold': hold,
        'available_items': available_items,
    }
    return render(request, 'circulation/complete_hold.html', context)

@login_required
@user_passes_test(is_staff_user)


def borrower_list(request):
    """List all borrowers"""
    form = BorrowerSearchForm(request.GET or None)
    borrowers = User.objects.filter(user_type='borrower')

    if form.is_valid():
        query = form.cleaned_data.get('query')
        is_blocked = form.cleaned_data.get('is_blocked')

        if query:
            borrowers = borrowers.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(library_card_number__icontains=query)
            )

        if is_blocked == 'yes':
            borrowers = borrowers.filter(is_blocked=True)
        elif is_blocked == 'no':
            borrowers = borrowers.filter(is_blocked=False)

    borrowers = borrowers.order_by('last_name', 'first_name')

    context = {
        'form': form,
        'borrowers': borrowers,
    }
    return render(request, 'circulation/borrower_list.html', context)

@login_required
@user_passes_test(is_staff_user)


def borrower_detail(request, user_id):
    """View borrower details and activity"""
    borrower = get_object_or_404(User, pk=user_id, user_type='borrower')

    active_loans = Loan.objects.filter(
        borrower=borrower,
        status='active'
    ).select_related('item__publication').order_by('due_date')

    loan_history = Loan.objects.filter(
        borrower=borrower
    ).select_related('item__publication').order_by('-checkout_date')[:20]

    active_holds = Hold.objects.filter(
        borrower=borrower,
        status__in=['waiting', 'ready']
    ).select_related('publication').order_by('hold_date')

    context = {
        'borrower': borrower,
        'active_loans': active_loans,
        'loan_history': loan_history,
        'active_holds': active_holds,
    }
    return render(request, 'circulation/borrower_detail.html', context)

@login_required
@user_passes_test(is_staff_user)


def block_borrower(request, user_id):
    """Block a borrower"""
    borrower = get_object_or_404(User, pk=user_id, user_type='borrower')

    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        borrower.is_blocked = True
        borrower.block_reason = reason
        borrower.save()
        messages.success(request, f"Borrower {borrower.get_full_name()} has been blocked.")
        return redirect('circulation:borrower_detail', user_id=user_id)

    return render(request, 'circulation/block_borrower.html', {'borrower': borrower})

@login_required
@user_passes_test(is_staff_user)


def unblock_borrower(request, user_id):
    """Unblock a borrower"""
    borrower = get_object_or_404(User, pk=user_id, user_type='borrower')

    borrower.is_blocked = False
    borrower.block_reason = ''
    borrower.save()

    messages.success(request, f"Borrower {borrower.get_full_name()} has been unblocked.")
    return redirect('circulation:borrower_detail', user_id=user_id)

@login_required
@user_passes_test(is_staff_user)


def send_in_transit(request):
    """Send an item in transit"""
    if request.method == 'POST':
        form = InTransitForm(request.POST)
        if form.is_valid():
            transit = form.save(commit=False)
            transit.item = form.cleaned_data['item']
            transit.from_location = transit.item.location
            transit.save()

            transit.item.status = 'in_transit'
            transit.item.save()

            messages.success(request, f"Item sent in transit to {transit.to_location}")
            return redirect('circulation:send_in_transit')
    else:
        form = InTransitForm()

    return render(request, 'circulation/send_in_transit.html', {'form': form})

@login_required
@user_passes_test(is_staff_user)


def receive_in_transit(request):
    """Receive items in transit"""
    if request.method == 'POST':
        # Prefer ISBN for transactions (barcode feature temporarily on hold)
        isbn = request.POST.get('isbn', '').strip()
        barcode = request.POST.get('barcode', '').strip()

        handled = False
        # If ISBN provided, try to find an in-transit record for that publication
        if isbn:
            try:
                # Try exact then normalized match (strip hyphens/spaces)
                normalized = isbn.replace('-', '').replace(' ', '')
                try:
                    publication = Publication.objects.get(isbn=isbn)
                except Publication.DoesNotExist:
                    publication = Publication.objects.annotate(
                        _norm=Replace(Replace(F('isbn'), Value('-'), Value('')), Value(' '), Value(''))
                    ).filter(_norm=normalized).first()

                if not publication:
                    messages.error(request, "No publication found with that ISBN.")
                    handled = True
                else:
                    transit = InTransit.objects.filter(item__publication=publication, status='in_transit').first()
                    if transit:
                        transit.mark_received()
                        messages.success(request, f"Item received at {transit.to_location}")
                        handled = True
                    else:
                        messages.error(request, "No in-transit record found for this ISBN.")
                        handled = True
            except Exception:
                messages.error(request, "Error while looking up in-transit record for ISBN.")
                handled = True

        # Fallback: if ISBN not provided or not handled, accept barcode for compatibility
        if not handled:
            try:
                item = Item.objects.get(barcode=barcode)
                transit = InTransit.objects.get(item=item, status='in_transit')
                transit.mark_received()
                messages.success(request, f"Item received at {transit.to_location}")
            except (Item.DoesNotExist, InTransit.DoesNotExist):
                messages.error(request, "No in-transit record found for this item.")

        return redirect('circulation:receive_in_transit')

    pending_transits = InTransit.objects.filter(
        status='in_transit'
    ).select_related('item__publication', 'from_location', 'to_location')

    return render(request, 'circulation/receive_in_transit.html', {'pending_transits': pending_transits})

@login_required
@user_passes_test(is_staff_user)


def transit_list(request):
    """List all transit records"""
    transits = InTransit.objects.all().select_related(
        'item__publication', 'from_location', 'to_location'
    ).order_by('-send_date')[:50]

    return render(request, 'circulation/transit_list.html', {'transits': transits})

@login_required
@user_passes_test(is_staff_user)


def reports(request):
    """Reports dashboard"""
    return render(request, 'circulation/reports.html')

@login_required
@user_passes_test(is_staff_user)


def overdue_report(request):
    """Report of overdue items"""
    today = timezone.now().date()
    overdue_loans = Loan.objects.filter(
        status='active',
        due_date__lt=today
    ).select_related('item__publication', 'borrower').order_by('due_date')

    context = {
        'overdue_loans': overdue_loans,
        'today': today,
    }
    return render(request, 'circulation/overdue_report.html', context)

@login_required
@user_passes_test(is_staff_user)


def circulation_stats(request):
    """Circulation statistics report"""
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)

    # Loan statistics
    total_checkouts = Loan.objects.filter(
        checkout_date__gte=last_30_days
    ).count()

    total_returns = Loan.objects.filter(
        return_date__gte=last_30_days
    ).count()

    # Most borrowed items
    popular_items = Item.objects.filter(
        loans__checkout_date__gte=last_30_days
    ).annotate(
        loan_count=Count('loans')
    ).select_related('publication').order_by('-loan_count')[:10]

    # Active borrowers
    active_borrowers = User.objects.filter(
        user_type='borrower',
        loans__checkout_date__gte=last_30_days
    ).annotate(
        loan_count=Count('loans')
    ).order_by('-loan_count')[:10]

    # By publication type
    by_type = Loan.objects.filter(
        checkout_date__gte=last_30_days
    ).values(
        'item__publication__publication_type__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    context = {
        'last_30_days': last_30_days,
        'total_checkouts': total_checkouts,
        'total_returns': total_returns,
        'popular_items': popular_items,
        'active_borrowers': active_borrowers,
        'by_type': by_type,
    }
    return render(request, 'circulation/circulation_stats.html', context)

@login_required


def notifications_list(request):
    """List all notifications for current user"""
    notifications = Notification.objects.filter(
        borrower=request.user
    ).select_related('loan__item__publication', 'hold__publication').order_by('-created_date')

    # Mark filter
    show_unread = request.GET.get('unread', '') == 'true'
    if show_unread:
        notifications = notifications.filter(is_read=False)

    context = {
        'notifications': notifications[:50],  # Limit to 50 most recent
        'unread_count': Notification.objects.filter(borrower=request.user, is_read=False).count(),
        'show_unread': show_unread,
    }
    return render(request, 'circulation/notifications_list.html', context)

@login_required


def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, borrower=request.user)
    notification.mark_as_read()

    # Redirect back to referring page or notifications list
    next_url = request.GET.get('next', 'circulation:notifications_list')
    return redirect(next_url)

@login_required


def mark_all_notifications_read(request):
    """Mark all notifications as read for current user"""
    if request.method == 'POST':
        Notification.objects.filter(
            borrower=request.user,
            is_read=False
        ).update(is_read=True, read_date=timezone.now())
        messages.success(request, 'All notifications marked as read.')

    return redirect('circulation:notifications_list')

@login_required


def delete_notification(request, notification_id):
    """Delete a notification"""
    notification = get_object_or_404(Notification, id=notification_id, borrower=request.user)

    if request.method == 'POST':
        notification.delete()
        messages.success(request, 'Notification deleted.')
        return redirect('circulation:notifications_list')

    return render(request, 'circulation/delete_notification.html', {'notification': notification})


def create_notification(borrower, notification_type, title, message, loan=None, hold=None, action_url=''):
    """
    Helper function to create notifications
    Used by other views to create notifications easily
    """
    notification = Notification.objects.create(
        borrower=borrower,
        notification_type=notification_type,
        title=title,
        message=message,
        loan=loan,
        hold=hold,
        action_url=action_url
    )
    return notification

# Checkout Request Views
@login_required


def request_checkout(request, publication_id):
    """Borrower requests to checkout a book"""
    publication = get_object_or_404(Publication, pk=publication_id)

    # Check if user already has an active request
    existing_request = CheckoutRequest.objects.filter(
        publication=publication,
        borrower=request.user,
        status__in=['pending', 'approved']
    ).first()

    if existing_request:
        messages.warning(request, f"You already have a {existing_request.get_status_display().lower()} checkout request for this item.")
        return redirect('catalog:publication_detail', pk=publication_id)

    # Check if item is available
    available_items = publication.items.filter(status='available')
    if not available_items.exists():
        messages.error(request, "No copies available. Please place a hold instead.")
        return redirect('catalog:publication_detail', pk=publication_id)

    if request.method == 'POST':
        notes = request.POST.get('notes', '')

        CheckoutRequest.objects.create(
            publication=publication,
            borrower=request.user,
            notes=notes,
            status='pending'
        )

        # Create notification
        create_notification(
            borrower=request.user,
            notification_type='hold_placed',  # Reusing hold_placed for now
            title=f'Checkout Request Submitted: {publication.title}',
            message=f'Your checkout request for "{publication.title}" has been submitted. Staff will review and approve it shortly. You will be notified when it\'s ready for pickup.',
            action_url='/accounts/my-account/'
        )

        messages.success(request, 'Checkout request submitted! Staff will review and notify you when ready for pickup.')
        return redirect('catalog:publication_detail', pk=publication_id)

    context = {
        'publication': publication,
        'available_items': available_items,
    }
    return render(request, 'circulation/request_checkout.html', context)

@login_required


def cancel_checkout_request(request, request_id):
    """Cancel a pending checkout request"""
    checkout_request = get_object_or_404(CheckoutRequest, pk=request_id, borrower=request.user)

    if checkout_request.status not in ['pending', 'approved']:
        messages.error(request, "Cannot cancel this request.")
        return redirect('accounts:my_account')

    if request.method == 'POST':
        checkout_request.status = 'cancelled'
        checkout_request.save()

        # Create notification
        create_notification(
            borrower=request.user,
            notification_type='hold_cancelled',
            title=f'Checkout Request Cancelled: {checkout_request.publication.title}',
            message=f'Your checkout request for "{checkout_request.publication.title}" has been cancelled.',
            action_url='/accounts/my-account/'
        )

        messages.success(request, 'Checkout request cancelled.')
        return redirect('accounts:my_account')

    return render(request, 'circulation/cancel_checkout_request.html', {'checkout_request': checkout_request})

@login_required
@user_passes_test(is_staff_user)


def manage_checkout_requests(request):
    """Staff view to manage checkout requests"""
    status_filter = request.GET.get('status', 'pending')

    requests_queryset = CheckoutRequest.objects.select_related(
        'publication', 'borrower', 'reviewed_by'
    ).order_by('-request_date')

    if status_filter and status_filter != 'all':
        requests_queryset = requests_queryset.filter(status=status_filter)

    context = {
        'checkout_requests': requests_queryset,
        'status_filter': status_filter,
        'pending_count': CheckoutRequest.objects.filter(status='pending').count(),
        'approved_count': CheckoutRequest.objects.filter(status='approved').count(),
    }
    return render(request, 'circulation/manage_checkout_requests.html', context)

@login_required
@user_passes_test(is_staff_user)


def approve_checkout_request(request, request_id):
    """Staff approves checkout request"""
    checkout_request = get_object_or_404(CheckoutRequest, pk=request_id)

    if checkout_request.status != 'pending':
        messages.error(request, "Request has already been reviewed.")
        return redirect('circulation:manage_checkout_requests')

    if not checkout_request.can_be_approved():
        messages.error(request, "No available copies to approve this request.")
        return redirect('circulation:manage_checkout_requests')

    if request.method == 'POST':
        pickup_location_id = request.POST.get('pickup_location')
        pickup_days = int(request.POST.get('pickup_days', 3))
        # Reserve an available item atomically when approving to prevent races
        try:
            with transaction.atomic():
                available_qs = Item.objects.select_for_update().filter(publication=checkout_request.publication, status='available')
                reserved = available_qs.first()
                if not reserved:
                    messages.error(request, "No available copies to reserve for this approval.")
                    return redirect('circulation:manage_checkout_requests')

                # mark item as on_hold_shelf to reserve it
                reserved.status = 'on_hold_shelf'
                reserved.save()

                checkout_request.reserved_item = reserved
                checkout_request.status = 'approved'
                checkout_request.reviewed_by = request.user
                checkout_request.review_date = timezone.now()
                checkout_request.pickup_by_date = timezone.now() + timedelta(days=pickup_days)

                if pickup_location_id:
                    checkout_request.pickup_location = Location.objects.get(pk=pickup_location_id)

                checkout_request.save()
        except Exception as e:
            logging.getLogger(__name__).exception("Error reserving item for checkout_request %s: %s", request_id, e)
            messages.error(request, "An unexpected error occurred while approving this request.")
            return redirect('circulation:manage_checkout_requests')

        # Create notification for borrower
        create_notification(
            borrower=checkout_request.borrower,
            notification_type='hold_ready',
            title=f'Checkout Request Approved: {checkout_request.publication.title}',
            message=f'Your checkout request for "{checkout_request.publication.title}" has been approved! Please come to {checkout_request.pickup_location or "the library"} to pick it up by {checkout_request.pickup_by_date.strftime("%B %d, %Y")}.',
            action_url='/accounts/my-account/'
        )

        messages.success(request, 'Checkout request approved. Borrower has been notified.')
        return redirect('circulation:manage_checkout_requests')

    locations = Location.objects.all()

    context = {
        'checkout_request': checkout_request,
        'locations': locations,
    }
    return render(request, 'circulation/approve_checkout_request.html', context)

@login_required
@user_passes_test(is_staff_user)


def deny_checkout_request(request, request_id):
    """Staff denies checkout request"""
    checkout_request = get_object_or_404(CheckoutRequest, pk=request_id)

    if checkout_request.status != 'pending':
        messages.error(request, "Request has already been reviewed.")
        return redirect('circulation:manage_checkout_requests')

    if request.method == 'POST':
        reason = request.POST.get('reason', '')

        checkout_request.status = 'denied'
        checkout_request.reviewed_by = request.user
        checkout_request.review_date = timezone.now()
        checkout_request.staff_notes = reason
        checkout_request.save()

        # Create notification
        create_notification(
            borrower=checkout_request.borrower,
            notification_type='hold_cancelled',
            title=f'Checkout Request Denied: {checkout_request.publication.title}',
            message=f'Your checkout request for "{checkout_request.publication.title}" could not be approved. {reason}',
            action_url='/accounts/my-account/'
        )

        messages.success(request, 'Checkout request denied. Borrower has been notified.')
        return redirect('circulation:manage_checkout_requests')

    return render(request, 'circulation/deny_checkout_request.html', {'checkout_request': checkout_request})

@login_required
@user_passes_test(is_staff_user)


def complete_checkout_request(request, request_id):
    """Staff completes checkout request by checking out the item to borrower"""
    checkout_request = get_object_or_404(CheckoutRequest, pk=request_id)

    if checkout_request.status != 'approved':
        messages.error(request, "This request must be approved before completing checkout.")
        return redirect('circulation:manage_checkout_requests')

    if request.method == 'POST':
        # TEMPORARY: Using ISBN instead of barcode (no scanner equipment yet)
        # When barcode scanner is available, uncomment the barcode section below

        item_identifier = request.POST.get('item_identifier', '').strip()

        if not item_identifier:
            messages.error(request, "Please select an item.")
            return render(request, 'circulation/complete_checkout_request.html', {
                'checkout_request': checkout_request,
                'available_items': Item.objects.filter(
                    publication=checkout_request.publication,
                    status__in=['available', 'on_hold_shelf']
                ).select_related('location')
            })

        try:
            # Reserve & create loan atomically
            with transaction.atomic():
                # CURRENT METHOD: Find item by ID (from dropdown selection)
                item = Item.objects.select_for_update().get(
                    id=item_identifier,
                    publication=checkout_request.publication,
                    status__in=['available', 'on_hold_shelf']
                )

                # Check if borrower can borrow
                if checkout_request.borrower.is_blocked:
                    messages.error(request, f"{checkout_request.borrower.get_full_name()} is currently blocked from borrowing.")
                    return redirect('circulation:manage_checkout_requests')

                if checkout_request.borrower.get_active_loans_count() >= checkout_request.borrower.max_items_allowed:
                    messages.error(request, f"{checkout_request.borrower.get_full_name()} has reached their borrowing limit.")
                    return redirect('circulation:manage_checkout_requests')

                # Create the loan with default 14-day period
                loan_period = 14  # Default loan period in days
                due_date = timezone.now() + timedelta(days=loan_period)

                loan = Loan.objects.create(
                    item=item,
                    borrower=checkout_request.borrower,
                    checkout_staff=request.user,
                    checkout_date=timezone.now(),
                    due_date=due_date,
                    status='active'
                )

                # Update item
                item.status = 'on_loan'
                item.times_borrowed += 1
                item.last_borrowed_date = timezone.now()
                item.save()

                # Update checkout request
                checkout_request.status = 'completed'
                checkout_request.loan = loan
                checkout_request.save()

        except Item.DoesNotExist:
            messages.error(request, "No available item found for this publication.")
            return render(request, 'circulation/complete_checkout_request.html', {
                'checkout_request': checkout_request,
                'available_items': Item.objects.filter(
                    publication=checkout_request.publication,
                    status__in=['available', 'on_hold_shelf']
                ).select_related('location')
            })

        # Create notification
        create_notification(
            borrower=checkout_request.borrower,
            notification_type='checkout',
            title=f'Item Checked Out: {checkout_request.publication.title}',
            message=f'You have successfully borrowed "{checkout_request.publication.title}". Due date: {loan.due_date.strftime("%B %d, %Y")}. Please return on time to avoid late fees.',
            loan=loan,
            action_url='/accounts/my-account/'
        )

        messages.success(
            request,
            f"Checkout completed! Item checked out to {checkout_request.borrower.get_full_name()}. Due: {loan.due_date.strftime('%B %d, %Y')}"
        )
        return redirect('circulation:manage_checkout_requests')

    # GET request - show form
    available_items = Item.objects.filter(
        publication=checkout_request.publication,
        status__in=['available', 'on_hold_shelf']
    ).select_related('location')

    context = {
        'checkout_request': checkout_request,
        'available_items': available_items,
    }
    return render(request, 'circulation/complete_checkout_request.html', context)

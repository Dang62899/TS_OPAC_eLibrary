from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.db.models import Q, Count, Exists, OuterRef
from django.core.paginator import Paginator
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Item, Publication, PublicationType, Subject, Author, Attachment, ViewLog, DownloadOTP
from .forms import SearchForm, PublicationForm, ItemForm, AttachmentForm, AttachmentDownloadPasswordForm
from .search import AdvancedSearch
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.utils.http import content_disposition_header
import hashlib
import os
import random
import re
import string
from .utils.pdf_utils import (
    merge_first_two_pages_with_watermark,
    watermark_text_for_date,
)
from .utils.download_watermarks import (
    UnsupportedWatermarkFormat,
    WatermarkProcessingError,
    watermarked_attachment_response,
)
from accounts.decorators import admin_required, staff_or_admin_required

DOWNLOAD_PASSWORD_MAX_ATTEMPTS = 5
DOWNLOAD_PASSWORD_LOCK_SECONDS = 900
DOWNLOAD_PASSWORD_SESSION_SECONDS = 600


def _has_download_password_access(request, attachment):
    if not attachment.has_download_password:
        return False
    access_until = request.session.get(f"download_password_access_{attachment.pk}", 0)
    return access_until > timezone.now().timestamp()


def _log_resource_access(request, attachment, action, user=None):
    actor = user or (request.user if request.user.is_authenticated else None)
    ViewLog.objects.create(
        user=actor,
        attachment=attachment,
        publication_id=attachment.publication_id,
        action=action,
        ip_address=request.META.get("REMOTE_ADDR", ""),
    )


def index(request):
    """Homepage with welcome text and library monitoring charts."""
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    publication_types = PublicationType.objects.annotate(pub_count=Count("publications")).order_by("name")
    available_item_count = Item.objects.filter(status="available").count()
    total_item_count = Item.objects.count()

    context = {
        "publication_types": publication_types,
        "available_item_count": available_item_count,
        "unavailable_item_count": total_item_count - available_item_count,
    }
    return render(request, "catalog/index.html", context)


@login_required
def search(request):
    """Advanced search functionality with boolean operators, phrase search, filters, and facets."""
    form = SearchForm(request.GET or None)

    if form.is_valid():
        query = form.cleaned_data.get("query") or ""
        search_in = form.cleaned_data.get("search_in") or "all"
        publication_types = form.cleaned_data.get("publication_types")
        language = form.cleaned_data.get("language")
        year_from = form.cleaned_data.get("year_from")
        year_to = form.cleaned_data.get("year_to")
        author_ids = form.cleaned_data.get("authors")
        subject_ids = form.cleaned_data.get("subjects")
        available_only = form.cleaned_data.get("available_only")
        location = form.cleaned_data.get("location")
        sort_by = form.cleaned_data.get("sort_by") or "relevance"

        result = AdvancedSearch.advanced_search(
            query=query,
            search_in=search_in,
            author_ids=[a.id for a in author_ids] if author_ids else None,
            subject_ids=[s.id for s in subject_ids] if subject_ids else None,
            pub_type_ids=[publication_type.id for publication_type in publication_types] if publication_types else None,
            language=language,
            date_from=f"{year_from}-01-01" if year_from else None,
            date_to=f"{year_to}-12-31" if year_to else None,
            available_only=available_only,
            sort_by=sort_by,
            location=location,
        )
        publications = result["results"]
        facets = result["facets"]
    else:
        publications = Publication.objects.all().order_by("title")
        facets = {
            "authors": [],
            "subjects": [],
            "publication_types": [],
            "languages": [],
            "availability": [],
        }

    research_class = request.GET.get("research_class", "").strip()
    unit = request.GET.get("unit", "").strip()
    resource_type = request.GET.get("resource_type", "").strip()
    tag = request.GET.get("tag", "").strip()
    file_format = request.GET.get("format", "").strip().lower().lstrip(".")
    downloadable = request.GET.get("downloadable", "")
    attachment_filters_applied = bool(
        unit or resource_type or tag or file_format or downloadable in {"true", "false"}
    )
    matching_attachments = Attachment.objects.filter(publication_id=OuterRef("pk"))
    if unit:
        matching_attachments = matching_attachments.filter(unit__iexact=unit)
    if resource_type:
        matching_attachments = matching_attachments.filter(attachment_type=resource_type)
    if tag:
        matching_attachments = matching_attachments.filter(tags__icontains=tag)
    if file_format:
        matching_attachments = matching_attachments.filter(file__iendswith=f".{file_format}")
    if downloadable in {"true", "false"}:
        matching_attachments = matching_attachments.filter(allow_download=(downloadable == "true"))

    if research_class and attachment_filters_applied:
        publications = publications.filter(
            (Q(research_class__icontains=research_class) & Exists(matching_attachments))
            | Exists(matching_attachments.filter(class_field__icontains=research_class))
        )
    elif research_class:
        publications = publications.filter(
            Q(research_class__icontains=research_class)
            | Exists(matching_attachments.filter(class_field__icontains=research_class))
        )
    elif attachment_filters_applied:
        publications = publications.filter(Exists(matching_attachments))

    paginator = Paginator(publications.distinct(), 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    pagination_params = request.GET.copy()
    pagination_params.pop("page", None)

    context = {
        "form": form,
        "page_obj": page_obj,
        "total_results": paginator.count,
        "facets": facets,
        "pagination_query": pagination_params.urlencode(),
        "active_filters": {
            "query": request.GET.get("query", ""),
            "publication_types": request.GET.getlist("publication_types"),
            "language": request.GET.get("language", ""),
            "authors": request.GET.getlist("authors"),
            "subjects": request.GET.getlist("subjects"),
            "year_from": request.GET.get("year_from", ""),
            "year_to": request.GET.get("year_to", ""),
            "location": request.GET.get("location", ""),
        },
    }
    return render(request, "catalog/search.html", context)


@login_required
def publication_detail(request, pk):
    """Detailed view of a publication"""
    publication = get_object_or_404(Publication, pk=pk)
    items = publication.items.all().select_related("location")
    attachments = publication.attachments.all().select_related("uploader")
    for attachment in attachments:
        access_until = request.session.get(f"video_access_{attachment.pk}", 0)
        attachment.download_password_access = (
            request.user.is_authenticated
            and attachment.allow_download
            and _has_download_password_access(request, attachment)
        )
        attachment.video_access = request.user.is_authenticated and (
            attachment.allow_download or access_until > timezone.now().timestamp()
        )
        attachment.preview_access = attachment.allow_download or (
            request.user.is_authenticated
            and request.session.get(f"attachment_access_{attachment.pk}", 0) > timezone.now().timestamp()
        )

    # Get hold information if user is authenticated
    hold = None
    checkout_request = None
    if request.user.is_authenticated:
        from circulation.models import Hold, CheckoutRequest

        try:
            hold = Hold.objects.get(publication=publication, borrower=request.user, status__in=["waiting", "ready"])
        except Hold.DoesNotExist:
            pass

        # Get checkout request if exists
        try:
            checkout_request = CheckoutRequest.objects.get(
                publication=publication, borrower=request.user, status__in=["pending", "approved"]
            )
        except CheckoutRequest.DoesNotExist:
            pass

    context = {
        "publication": publication,
        "items": items,
        "attachments": attachments,
        "hold": hold,
        "checkout_request": checkout_request,
    }
    # Log the view (non-blocking)
    try:
        ip = request.META.get("REMOTE_ADDR", "")
        ViewLog.objects.create(user=(request.user if request.user.is_authenticated else None), publication=publication, ip_address=ip)
    except Exception:
        pass

    return render(request, "catalog/publication_detail.html", context)


@login_required
@staff_or_admin_required
def upload_attachment(request, pk):
    publication = get_object_or_404(Publication, pk=pk)
    if request.method == "POST":
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.publication = publication
            attachment.uploader = request.user
            attachment.save()
            messages.success(request, "Attachment uploaded.")
            return redirect("catalog:publication_detail", pk=pk)
    else:
        form = AttachmentForm()
    return render(request, "catalog/upload_attachment.html", {"form": form, "publication": publication})


@login_required
@require_POST
def request_download_otp(request, attachment_id):
    """Generate an OTP for a protected attachment and return it (in real use email/SMS)."""
    attachment = get_object_or_404(Attachment, pk=attachment_id)
    if attachment.allow_download:
        return redirect("catalog:download_attachment", attachment_id=attachment.pk)

    # Create OTP
    code = "".join(random.choices(string.digits, k=6))
    timeout_minutes = int(getattr(settings, "DOWNLOAD_OTP_TIMEOUT_MINUTES", 15))
    expires = timezone.now() + timezone.timedelta(minutes=timeout_minutes)
    otp = DownloadOTP.objects.create(
        attachment=attachment,
        user=(request.user if request.user.is_authenticated else None),
        code=code,
        expires_at=expires,
    )

    # Queue email via Celery if user has an email; otherwise show code directly
    try:
        from .tasks import send_otp_email

        if otp.user and otp.user.email:
            send_otp_email.delay(otp.id)
            return render(request, "catalog/download_otp_sent.html", {"attachment": attachment})
    except Exception:
        # If Celery or mail sending not available, fall back to showing code
        pass

    if settings.DEBUG:
        return render(
            request,
            "catalog/download_otp.html",
            {"code": code, "attachment": attachment, "expires": expires},
        )
    return HttpResponse("OTP delivery is unavailable. Please contact the library administrator.", status=503)


@login_required
@require_POST
def unlock_attachment(request, attachment_id):
    attachment = get_object_or_404(Attachment, pk=attachment_id)
    if not attachment.allow_download:
        return HttpResponse("This resource is not configured for password downloads.", status=403)

    now = timezone.now().timestamp()
    lock_key = f"attachment-password-lock:{request.user.pk}:{attachment.pk}"
    attempts_key = f"attachment-password-attempts:{request.user.pk}:{attachment.pk}"
    if cache.get(lock_key, 0) > now:
        messages.error(request, "Too many incorrect attempts. Try again in 15 minutes.")
        return redirect("catalog:publication_detail", pk=attachment.publication_id)

    form = AttachmentDownloadPasswordForm(request.POST)
    if form.is_valid() and attachment.check_download_password(form.cleaned_data["password"]):
        cache.delete(attempts_key)
        cache.delete(lock_key)
        request.session[f"download_password_access_{attachment.pk}"] = int(
            now + DOWNLOAD_PASSWORD_SESSION_SECONDS
        )
        messages.success(request, "Resource unlocked for 10 minutes.")
        return redirect("catalog:publication_detail", pk=attachment.publication_id)

    attempts = int(cache.get(attempts_key, 0)) + 1
    if attempts >= DOWNLOAD_PASSWORD_MAX_ATTEMPTS:
        cache.delete(attempts_key)
        cache.set(lock_key, now + DOWNLOAD_PASSWORD_LOCK_SECONDS, DOWNLOAD_PASSWORD_LOCK_SECONDS)
        messages.error(request, "Too many incorrect attempts. Try again in 15 minutes.")
    else:
        cache.set(attempts_key, attempts, DOWNLOAD_PASSWORD_LOCK_SECONDS)
        messages.error(request, "Incorrect download password.")
    return redirect("catalog:publication_detail", pk=attachment.publication_id)


@login_required
def download_attachment(request, attachment_id):
    """Serve downloadable attachments with audit logging and PDF watermarking."""
    attachment = get_object_or_404(Attachment, pk=attachment_id)
    if not attachment.allow_download:
        return HttpResponse("This attachment requires a one-time code.", status=403)
    if not _has_download_password_access(request, attachment):
        return HttpResponse("Unlock this resource with its download password before downloading.", status=403)

    if attachment.is_external and attachment.external_url:
        _log_resource_access(request, attachment, "download")
        return redirect(attachment.external_url)
    if not attachment.file:
        return HttpResponse("No file available", status=404)

    try:
        response = watermarked_attachment_response(attachment, watermark_text_for_date())
    except UnsupportedWatermarkFormat:
        return HttpResponse("This file format cannot be safely watermarked for download.", status=415)
    except WatermarkProcessingError:
        return HttpResponse("Watermarking failed; the original file was not served.", status=500)
    _log_resource_access(request, attachment, "download")
    return response


@login_required
@require_POST
def confirm_download(request, otp_code):
    """Confirm OTP and serve file if valid."""
    otp = (
        DownloadOTP.objects.filter(code=otp_code, user=request.user, used=False)
        .order_by("-created_at")
        .first()
    )
    if otp is None:
        return HttpResponse("Invalid or expired code", status=400)

    if not otp.is_valid():
        return HttpResponse("OTP expired or used", status=400)

    attachment = otp.attachment
    if attachment.allow_download:
        return HttpResponse("This resource uses its download password, not a one-time code.", status=403)
    if attachment.is_external and attachment.external_url:
        otp.used = True
        otp.save(update_fields=["used"])
        _log_resource_access(request, attachment, "download", user=otp.user)
        return redirect(attachment.external_url)
    if not attachment.file:
        return HttpResponse("No file available", status=404)

    try:
        response = watermarked_attachment_response(attachment, watermark_text_for_date())
    except UnsupportedWatermarkFormat:
        return HttpResponse("This file format cannot be safely watermarked for download.", status=415)
    except WatermarkProcessingError:
        return HttpResponse("Watermarking failed; the original file was not served.", status=500)
    otp.used = True
    otp.save(update_fields=["used"])
    _log_resource_access(request, attachment, "download", user=otp.user)
    return response


@login_required
@require_POST
def confirm_attachment_otp(request, attachment_id):
    """Redeem a user's OTP from the attachment detail page."""
    attachment = get_object_or_404(Attachment, pk=attachment_id)
    code = request.POST.get("code", "").strip()
    otp = DownloadOTP.objects.filter(
        attachment=attachment,
        user=request.user,
        code=code,
        used=False,
    ).order_by("-created_at").first()
    if otp is None or not otp.is_valid():
        messages.error(request, "That code is invalid, expired, or already used. Request a new code and try again.")
        return redirect("catalog:publication_detail", pk=attachment.publication_id)
    if attachment.allow_download:
        return HttpResponse("This resource uses its download password, not a one-time code.", status=403)

    if attachment.attachment_type == "video":
        otp.used = True
        otp.save(update_fields=["used"])
        request.session[f"attachment_access_{attachment.pk}"] = int(otp.expires_at.timestamp())
        request.session[f"video_access_{attachment.pk}"] = int(otp.expires_at.timestamp())
        if attachment.is_external and attachment.external_url:
            _log_resource_access(request, attachment, "play")
            return redirect(attachment.external_url)
        return redirect("catalog:publication_detail", pk=attachment.publication_id)
    if attachment.is_external and attachment.external_url:
        otp.used = True
        otp.save(update_fields=["used"])
        request.session[f"attachment_access_{attachment.pk}"] = int(otp.expires_at.timestamp())
        _log_resource_access(request, attachment, "download")
        return redirect(attachment.external_url)
    if not attachment.file:
        return HttpResponse("No file available", status=404)

    try:
        response = watermarked_attachment_response(attachment, watermark_text_for_date())
    except UnsupportedWatermarkFormat:
        return HttpResponse("This file format cannot be safely watermarked for download.", status=415)
    except WatermarkProcessingError:
        return HttpResponse("Watermarking failed; the original file was not served.", status=500)

    otp.used = True
    otp.save(update_fields=["used"])
    request.session[f"attachment_access_{attachment.pk}"] = int(otp.expires_at.timestamp())
    _log_resource_access(request, attachment, "download")
    return response


@login_required
def stream_attachment(request, attachment_id):
    """Stream an uploaded MP4 for inline viewing, honoring byte-range requests."""
    attachment = get_object_or_404(Attachment, pk=attachment_id, attachment_type="video")
    if not attachment.file or not attachment.file.name.lower().endswith(".mp4"):
        return HttpResponse("Video not found", status=404)

    if not attachment.allow_download:
        access_until = request.session.get(f"video_access_{attachment.pk}", 0)
        if access_until <= timezone.now().timestamp():
            return HttpResponse("This video requires a one-time code.", status=403)

    size = attachment.file.size
    start, end = 0, size - 1
    status_code = 200
    range_header = request.headers.get("Range", "")
    if range_header:
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
        if not match or (not match.group(1) and not match.group(2)):
            return HttpResponse(status=416, headers={"Content-Range": f"bytes */{size}"})
        if match.group(1):
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else size - 1
        else:
            suffix_length = int(match.group(2))
            start = max(size - suffix_length, 0)
        if start >= size or start > end:
            return HttpResponse(status=416, headers={"Content-Range": f"bytes */{size}"})
        end = min(end, size - 1)
        status_code = 206

    file_stream = attachment.file.open("rb")
    file_stream.seek(start)
    remaining = max(end - start + 1, 0)

    def chunks():
        nonlocal remaining
        try:
            while remaining:
                chunk = file_stream.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk
        finally:
            file_stream.close()

    if start == 0:
        _log_resource_access(request, attachment, "play")
    response = StreamingHttpResponse(chunks(), status=status_code, content_type="video/mp4")
    response["Accept-Ranges"] = "bytes"
    response["Content-Length"] = str(max(end - start + 1, 0))
    response["Content-Disposition"] = content_disposition_header(
        False, os.path.basename(attachment.file.name)
    )
    if status_code == 206:
        response["Content-Range"] = f"bytes {start}-{end}/{size}"
    return response


@login_required
def preview_merged_attachment(request, attachment_id):
    """Generate and return a merged/watermarked preview for the first two pages of a PDF attachment."""
    attachment = get_object_or_404(Attachment, pk=attachment_id)
    if not attachment.file:
        return HttpResponse("No file to preview", status=404)

    if not attachment.allow_download:
        access_until = request.session.get(f"attachment_access_{attachment.pk}", 0)
        if not request.user.is_authenticated or access_until <= timezone.now().timestamp():
            return HttpResponse("This attachment requires a one-time code.", status=403)

    # Only support PDF previews for now
    name = attachment.file.name.lower()
    if not name.endswith(".pdf"):
        return HttpResponse("Preview not available for non-PDF files", status=400)

    _log_resource_access(request, attachment, "preview")

    watermark_text = watermark_text_for_date()
    cache_payload = (
        f"{attachment.pk}:{attachment.file.size}:{attachment.upload_date.timestamp()}:"
        f"{attachment.merge_first_two_pages}:{watermark_text}"
    )
    cache_key = f"attachment-preview:{hashlib.sha256(cache_payload.encode()).hexdigest()}"
    merged_bytes = cache.get(cache_key)
    try:
        if merged_bytes is None:
            with attachment.file.open("rb") as file_stream:
                merged_bytes = merge_first_two_pages_with_watermark(
                    file_stream,
                    watermark_text=watermark_text,
                    combine_first_two=attachment.merge_first_two_pages,
                )
            cache.set(cache_key, merged_bytes, timeout=24 * 60 * 60)
    except Exception as e:
        return HttpResponse(f"Error generating preview: {e}", status=500)

    response = HttpResponse(merged_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="preview_{attachment_id}.pdf"'
    return response


@login_required
def browse_by_type(request, type_id):
    """Browse publications by type"""
    publication_type = get_object_or_404(PublicationType, pk=type_id)
    publications = Publication.objects.filter(publication_type=publication_type).order_by("title")

    paginator = Paginator(publications, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "publication_type": publication_type,
        "page_obj": page_obj,
        "browse_title": publication_type.name,
        "browse_description": f"Browse all {publication_type.name} in the collection",
    }
    return render(request, "catalog/browse_results.html", context)


@login_required
def browse_by_subject(request, subject_id):
    """Browse publications by subject"""
    subject = get_object_or_404(Subject, pk=subject_id)
    publications = Publication.objects.filter(subjects=subject).order_by("title")

    paginator = Paginator(publications, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "subject": subject,
        "page_obj": page_obj,
        "browse_title": subject.name,
        "browse_description": f"Browse all publications on {subject.name}",
    }
    return render(request, "catalog/browse_results.html", context)


@login_required
def browse_by_author(request, author_id):
    """Browse publications by author"""
    author = get_object_or_404(Author, pk=author_id)
    publications = Publication.objects.filter(authors=author).order_by("title")

    paginator = Paginator(publications, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "author": author,
        "page_obj": page_obj,
        "browse_title": str(author),
        "browse_description": f"Browse all publications by {author}",
    }
    return render(request, "catalog/browse_results.html", context)


@login_required
def browse_research(request):
    """Browse research papers by year or class"""
    year = request.GET.get("year")
    cls = request.GET.get("class")

    qs = Publication.objects.filter(publication_type__code__icontains="paper").order_by("title")
    if year:
        try:
            qs = qs.filter(research_year=int(year))
        except ValueError:
            pass
    if cls:
        qs = qs.filter(research_class__icontains=cls)

    paginator = Paginator(qs.distinct(), 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "browse_title": "Research Papers",
        "active_filters": {"year": year or "", "class": cls or ""},
        "research_years": Publication.objects.filter(
            publication_type__code__icontains="paper", research_year__isnull=False
        ).values_list("research_year", flat=True).distinct().order_by("-research_year"),
        "research_classes": Publication.objects.filter(
            publication_type__code__icontains="paper"
        ).exclude(research_class="").values_list("research_class", flat=True).distinct().order_by("research_class"),
    }
    return render(request, "catalog/browse_results.html", context)


@login_required
@staff_or_admin_required
def manage_publications(request):
    """Staff/Admin view to manage publications"""
    publications = Publication.objects.all().select_related("publication_type").order_by("-date_added")
    search_query = request.GET.get("search", "")
    type_filter = request.GET.get("type", "")

    if search_query:
        publications = publications.filter(
            Q(title__icontains=search_query) | Q(isbn__icontains=search_query) | Q(call_number__icontains=search_query)
        )

    if type_filter:
        publications = publications.filter(publication_type_id=type_filter)

    paginator = Paginator(publications, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    publication_types = PublicationType.objects.all()

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "type_filter": type_filter,
        "publication_types": publication_types,
    }
    return render(request, "catalog/manage_publications.html", context)


@login_required
@admin_required
def delete_publication(request, pk):
    """Admin only - Delete a publication"""
    publication = get_object_or_404(Publication, pk=pk)
    if request.method == "POST":
        title = publication.title
        publication.delete()
        messages.success(request, f'Publication "{title}" has been deleted!')
        return redirect("catalog:manage_publications")
    return render(request, "catalog/delete_publication.html", {"publication": publication})


@login_required
@staff_or_admin_required
def add_publication(request):
    """Staff/Admin - Add a new publication"""
    if request.method == "POST":
        form = PublicationForm(request.POST, request.FILES)
        if form.is_valid():
            publication = form.save()
            messages.success(request, f'Publication "{publication.title}" has been created successfully!')
            return redirect("catalog:add_items", pk=publication.pk)
    else:
        form = PublicationForm()

    return render(request, "catalog/add_publication.html", {"form": form})


@login_required
@staff_or_admin_required
def edit_publication(request, pk):
    """Staff/Admin - Edit an existing publication"""
    publication = get_object_or_404(Publication, pk=pk)
    if request.method == "POST":
        form = PublicationForm(request.POST, request.FILES, instance=publication)
        if form.is_valid():
            form.save()
            messages.success(request, f'Publication "{publication.title}" has been updated!')
            return redirect("catalog:manage_publications")
    else:
        form = PublicationForm(instance=publication)

    return render(request, "catalog/edit_publication.html", {"form": form, "publication": publication})


@login_required
@staff_or_admin_required
def add_items(request, pk):
    """Staff/Admin - Add items (copies) to a publication"""
    publication = get_object_or_404(Publication, pk=pk)
    items = publication.items.all()

    if request.method == "POST":
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.publication = publication
            item.save()
            messages.success(request, f"Item {item.barcode} has been added!")
            return redirect("catalog:add_items", pk=pk)
    else:
        form = ItemForm()

    return render(request, "catalog/add_items.html", {"form": form, "publication": publication, "items": items})


# API Endpoints for AJAX functionality
@login_required
def search_suggestions(request):
    """API endpoint for autocomplete suggestions in search box"""
    query = (request.GET.get("query") or request.GET.get("q") or "").strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Get unique publication titles matching the query
    titles = Publication.objects.filter(
        title__icontains=query
    ).values_list('title', flat=True).distinct()[:10]
    
    # Get author names matching the query
    authors = Author.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query)
    ).values_list("first_name", "last_name")[:5]
    
    # Get subjects matching the query
    subjects = Subject.objects.filter(
        name__icontains=query
    ).values_list('name', flat=True).distinct()[:5]
    
    # Combine and limit suggestions
    author_names = [" ".join(name for name in author if name) for author in authors]
    suggestions = list(titles) + author_names + list(subjects)
    suggestions = list(set(suggestions))[:15]  # Remove duplicates and limit to 15
    
    return JsonResponse({'suggestions': sorted(suggestions)})

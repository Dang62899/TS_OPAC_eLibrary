from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Publication, PublicationType, Subject, Author
from .forms import SearchForm, PublicationForm, ItemForm
from accounts.decorators import admin_required, staff_or_admin_required


def index(request):
    """Homepage with featured publications"""
    recent_publications = Publication.objects.all().order_by("-date_added")[:8]
    publication_types = PublicationType.objects.annotate(pub_count=Count("publications")).order_by("name")

    context = {
        "recent_publications": recent_publications,
        "publication_types": publication_types,
    }
    return render(request, "catalog/index.html", context)


def search(request):
    """Advanced search functionality"""
    form = SearchForm(request.GET or None)
    publications = Publication.objects.all()

    if form.is_valid():
        query = form.cleaned_data.get("query")
        search_field = form.cleaned_data.get("search_field")
        publication_type = form.cleaned_data.get("publication_type")
        language = form.cleaned_data.get("language")
        year_from = form.cleaned_data.get("year_from")
        year_to = form.cleaned_data.get("year_to")
        available_only = form.cleaned_data.get("available_only")

        # Apply search query
        if query:
            if search_field == "all":
                publications = publications.filter(
                    Q(title__icontains=query)
                    | Q(subtitle__icontains=query)
                    | Q(authors__first_name__icontains=query)
                    | Q(authors__last_name__icontains=query)
                    | Q(subjects__name__icontains=query)
                    | Q(call_number__icontains=query)
                    | Q(isbn__icontains=query)
                    | Q(abstract__icontains=query)
                ).distinct()
            elif search_field == "title":
                publications = publications.filter(Q(title__icontains=query) | Q(subtitle__icontains=query))
            elif search_field == "author":
                publications = publications.filter(
                    Q(authors__first_name__icontains=query) | Q(authors__last_name__icontains=query)
                ).distinct()
            elif search_field == "subject":
                publications = publications.filter(subjects__name__icontains=query).distinct()
            elif search_field == "call_number":
                publications = publications.filter(call_number__icontains=query)
            elif search_field == "isbn":
                publications = publications.filter(isbn__icontains=query)

        # Apply filters
        if publication_type:
            publications = publications.filter(publication_type=publication_type)

        if language:
            publications = publications.filter(language__icontains=language)

        if year_from:
            publications = publications.filter(publication_date__year__gte=year_from)

        if year_to:
            publications = publications.filter(publication_date__year__lte=year_to)

        if available_only:
            publications = publications.filter(items__status="available").distinct()

    # Pagination
    paginator = Paginator(publications.distinct().order_by("title"), 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "form": form,
        "page_obj": page_obj,
        "total_results": paginator.count,
    }
    return render(request, "catalog/search.html", context)


def publication_detail(request, pk):
    """Detailed view of a publication"""
    publication = get_object_or_404(Publication, pk=pk)
    items = publication.items.all().select_related("location")

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
        "hold": hold,
        "checkout_request": checkout_request,
    }
    return render(request, "catalog/publication_detail.html", context)


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
        "browse_title": author.name,
        "browse_description": f"Browse all publications by {author.name}",
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
from django.http import JsonResponse


def search_suggestions(request):
    """API endpoint for autocomplete suggestions in search box"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Get unique publication titles matching the query
    titles = Publication.objects.filter(
        title__icontains=query
    ).values_list('title', flat=True).distinct()[:10]
    
    # Get author names matching the query
    from accounts.models import Author
    authors = Author.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query)
    ).values_list('get_full_name', flat=True).distinct()[:5]
    
    # Get subjects matching the query
    subjects = Subject.objects.filter(
        name__icontains=query
    ).values_list('name', flat=True).distinct()[:5]
    
    # Combine and limit suggestions
    suggestions = list(titles) + list(authors) + list(subjects)
    suggestions = list(set(suggestions))[:15]  # Remove duplicates and limit to 15
    
    return JsonResponse({'suggestions': sorted(suggestions)})

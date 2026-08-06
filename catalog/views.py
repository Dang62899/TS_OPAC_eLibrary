from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Publication, PublicationType, Subject, Author, Location
from .forms import SearchForm, PublicationForm, ItemForm
from .search import AdvancedSearch
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
    """Advanced search functionality with boolean operators, phrase search, filters, and facets."""
    form = SearchForm(request.GET or None)

    if form.is_valid():
        query = form.cleaned_data.get("query") or ""
        search_field = form.cleaned_data.get("search_field") or "all"
        publication_type = form.cleaned_data.get("publication_type")
        language = form.cleaned_data.get("language")
        year_from = form.cleaned_data.get("year_from")
        year_to = form.cleaned_data.get("year_to")
        available_only = form.cleaned_data.get("available_only")
        location = form.cleaned_data.get("location")
        sort_by = form.cleaned_data.get("sort_by") or "relevance"

        if query and search_field != "all":
            field_query = query
            if search_field == "title":
                field_query = f"title:{query}"
            elif search_field == "author":
                field_query = f"author:{query}"
            elif search_field == "subject":
                field_query = f"subject:{query}"
            elif search_field == "call_number":
                field_query = f"call_number:{query}"
            elif search_field == "isbn":
                field_query = f"isbn:{query}"
            query = field_query

        result = AdvancedSearch.advanced_search(
            query=query,
            pub_type_ids=[publication_type.id] if publication_type else None,
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

    paginator = Paginator(publications.distinct(), 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "form": form,
        "page_obj": page_obj,
        "total_results": paginator.count,
        "facets": facets,
        "active_filters": {
            "query": request.GET.get("query", ""),
            "publication_type": request.GET.get("publication_type", ""),
            "language": request.GET.get("language", ""),
            "year_from": request.GET.get("year_from", ""),
            "year_to": request.GET.get("year_to", ""),
            "location": request.GET.get("location", ""),
        },
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
        "browse_title": str(author),
        "browse_description": f"Browse all publications by {author}",
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

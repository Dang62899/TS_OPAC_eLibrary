# Advanced Search Module for TS OPAC eLibrary

import re
from django.db.models import Q, Count
from catalog.models import Publication, Author, Subject, PublicationType, Item


class AdvancedSearch:
    """Advanced search engine with boolean operators, phrases, filters, and facets."""

    @staticmethod
    def _build_term_query(term):
        if not term:
            return Q()

        search_term = term.strip().strip('"').strip("'")
        if not search_term:
            return Q()

        return (
            Q(title__icontains=search_term)
            | Q(subtitle__icontains=search_term)
            | Q(abstract__icontains=search_term)
            | Q(summary__icontains=search_term)
            | Q(authors__first_name__icontains=search_term)
            | Q(authors__last_name__icontains=search_term)
            | Q(subjects__name__icontains=search_term)
            | Q(call_number__icontains=search_term)
            | Q(isbn__icontains=search_term)
            | Q(publication_type__name__icontains=search_term)
        )

    @staticmethod
    def _parse_boolean_query(query):
        normalized_query = (query or "").strip()
        if not normalized_query:
            return None

        tokens = re.findall(r'"[^"]*"|\S+', normalized_query)
        clauses = []
        pending_operator = "AND"

        for token in tokens:
            upper_token = token.upper()
            if upper_token in {"AND", "OR", "NOT"}:
                pending_operator = upper_token if upper_token != "NOT" else "NOT"
                continue

            clause_term = token.strip('"').strip("'")
            if not clause_term:
                continue

            clauses.append((pending_operator, clause_term))
            pending_operator = "AND"

        if not clauses:
            return None

        combined_query = None
        for operator, term in clauses:
            term_query = AdvancedSearch._build_term_query(term)
            if combined_query is None:
                combined_query = term_query
            elif operator == "AND":
                combined_query &= term_query
            elif operator == "OR":
                combined_query |= term_query
            elif operator == "NOT":
                combined_query &= ~term_query

        return combined_query

    @staticmethod
    def full_text_search(query):
        """Perform full-text search across publication fields with boolean support."""
        normalized_query = (query or "").strip()
        if not normalized_query:
            return Publication.objects.none()

        boolean_query = AdvancedSearch._parse_boolean_query(normalized_query)
        if boolean_query is not None:
            return Publication.objects.filter(boolean_query).distinct()

        return Publication.objects.filter(AdvancedSearch._build_term_query(normalized_query)).distinct()

    @staticmethod
    def filter_by_date_range(queryset, start_date=None, end_date=None):
        if start_date:
            queryset = queryset.filter(publication_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(publication_date__lte=end_date)
        return queryset

    @staticmethod
    def filter_by_authors(queryset, author_ids):
        if author_ids:
            queryset = queryset.filter(authors__id__in=author_ids).distinct()
        return queryset

    @staticmethod
    def filter_by_subjects(queryset, subject_ids):
        if subject_ids:
            queryset = queryset.filter(subjects__id__in=subject_ids).distinct()
        return queryset

    @staticmethod
    def filter_by_publication_type(queryset, pub_type_ids):
        if pub_type_ids:
            queryset = queryset.filter(publication_type_id__in=pub_type_ids)
        return queryset

    @staticmethod
    def filter_by_language(queryset, language):
        if language:
            queryset = queryset.filter(language__icontains=language)
        return queryset

    @staticmethod
    def filter_by_location(queryset, location):
        if location:
            queryset = queryset.filter(items__location=location).distinct()
        return queryset

    @staticmethod
    def filter_by_availability(queryset, available_only=False):
        if available_only:
            queryset = queryset.filter(items__status="available").distinct()
        return queryset

    @staticmethod
    def sort_results(queryset, sort_by="relevance"):
        if sort_by == "date":
            queryset = queryset.order_by("-publication_date")
        elif sort_by == "date_asc":
            queryset = queryset.order_by("publication_date")
        elif sort_by == "title":
            queryset = queryset.order_by("title")
        elif sort_by == "title_desc":
            queryset = queryset.order_by("-title")
        elif sort_by == "popularity":
            queryset = queryset.annotate(checkout_count=Count("items__loans")).order_by("-checkout_count")
        else:
            queryset = queryset.order_by("-date_added")

        return queryset

    @staticmethod
    def faceted_search(queryset):
        return {
            "authors": Author.objects.filter(publications__in=queryset)
            .annotate(count=Count("publications"))
            .values("id", "first_name", "last_name", "count")
            .order_by("last_name", "first_name"),
            "subjects": Subject.objects.filter(publications__in=queryset)
            .annotate(count=Count("publications"))
            .values("id", "name", "count")
            .order_by("name"),
            "publication_types": PublicationType.objects.filter(publications__in=queryset)
            .annotate(count=Count("publications"))
            .values("id", "name", "count")
            .order_by("name"),
            "languages": queryset.values("language")
            .exclude(language="")
            .distinct()
            .annotate(count=Count("id"))
            .order_by("-count", "language"),
            "availability": [
                {"status": "available", "count": queryset.filter(items__status="available").distinct().count()},
                {"status": "on_loan", "count": queryset.filter(items__status="on_loan").distinct().count()},
                {"status": "on_hold_shelf", "count": queryset.filter(items__status="on_hold_shelf").distinct().count()},
            ],
        }

    @staticmethod
    def advanced_search(
        query="",
        author_ids=None,
        subject_ids=None,
        pub_type_ids=None,
        language=None,
        date_from=None,
        date_to=None,
        available_only=False,
        sort_by="relevance",
        limit=None,
        location=None,
    ):
        if query:
            queryset = AdvancedSearch.full_text_search(query)
        else:
            queryset = Publication.objects.all()

        queryset = AdvancedSearch.filter_by_authors(queryset, author_ids)
        queryset = AdvancedSearch.filter_by_subjects(queryset, subject_ids)
        queryset = AdvancedSearch.filter_by_publication_type(queryset, pub_type_ids)
        queryset = AdvancedSearch.filter_by_language(queryset, language)
        queryset = AdvancedSearch.filter_by_location(queryset, location)
        queryset = AdvancedSearch.filter_by_date_range(queryset, date_from, date_to)
        queryset = AdvancedSearch.filter_by_availability(queryset, available_only)
        queryset = AdvancedSearch.sort_results(queryset, sort_by)

        facets = AdvancedSearch.faceted_search(queryset)

        if limit:
            queryset = queryset[:limit]

        return {"results": queryset, "total_count": queryset.count(), "facets": facets}

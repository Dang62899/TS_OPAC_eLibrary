# Enhanced API views for Advanced Search - Add to api/views.py

from rest_framework import generics, filters, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from catalog.models import Publication, Author, Subject, PublicationType
from catalog.search import AdvancedSearch
from api.serializers import PublicationSerializer
from datetime import datetime


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AdvancedPublicationSearchView(generics.ListAPIView):
    """
    Advanced publication search with multiple filters.
    
    Query Parameters:
    - q: Full text search query
    - authors: Comma-separated author IDs
    - subjects: Comma-separated subject IDs
    - pub_type: Comma-separated publication type IDs
    - language: Language code (e.g., 'en', 'es')
    - date_from: Start date (YYYY-MM-DD)
    - date_to: End date (YYYY-MM-DD)
    - available_only: Boolean (true/false)
    - sort_by: relevance|date|date_asc|title|title_desc|popularity
    - page: Page number (default 1)
    - page_size: Results per page (default 20, max 100)
    
    Example:
    GET /api/search/advanced/?q=fiction&subjects=1,2&available_only=true&sort_by=date
    """
    
    serializer_class = PublicationSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        author_ids = self._parse_ids(self.request.query_params.get('authors', ''))
        subject_ids = self._parse_ids(self.request.query_params.get('subjects', ''))
        pub_type_ids = self._parse_ids(self.request.query_params.get('pub_type', ''))
        language = self.request.query_params.get('language', '')
        date_from = self._parse_date(self.request.query_params.get('date_from'))
        date_to = self._parse_date(self.request.query_params.get('date_to'))
        available_only = self.request.query_params.get('available_only', 'false').lower() == 'true'
        sort_by = self.request.query_params.get('sort_by', 'relevance')
        
        # Perform advanced search
        results = AdvancedSearch.advanced_search(
            query=query,
            author_ids=author_ids,
            subject_ids=subject_ids,
            pub_type_ids=pub_type_ids,
            language=language,
            date_from=date_from,
            date_to=date_to,
            available_only=available_only,
            sort_by=sort_by
        )
        
        # Store facets for later retrieval in response
        self.facets = results['facets']
        
        return results['results']
    
    def list(self, request, *args, **kwargs):
        """Override to include facets in response"""
        response = super().list(request, *args, **kwargs)
        
        # Add facets to response
        response.data = {
            'count': response.data.get('count'),
            'next': response.data.get('next'),
            'previous': response.data.get('previous'),
            'results': response.data.get('results'),
            'facets': self.facets if hasattr(self, 'facets') else {}
        }
        
        return response
    
    @staticmethod
    def _parse_ids(ids_string):
        """Parse comma-separated IDs into list of integers"""
        if not ids_string:
            return None
        try:
            return [int(id) for id in ids_string.split(',') if id.strip().isdigit()]
        except:
            return None
    
    @staticmethod
    def _parse_date(date_string):
        """Parse date string (YYYY-MM-DD) into datetime"""
        if not date_string:
            return None
        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except:
            return None


@api_view(['GET'])
def search_facets(request):
    """
    Get available search facets (for filter options)
    
    Returns all authors, subjects, publication types, and languages
    available in the system.
    
    Example:
    GET /api/search/facets/
    """
    
    authors = Author.objects.all().values('id', 'first_name', 'last_name')
    subjects = Subject.objects.all().values('id', 'name')
    pub_types = PublicationType.objects.all().values('id', 'name', 'code')
    languages = Publication.objects.values_list('language', flat=True).distinct()
    
    return Response({
        'authors': list(authors),
        'subjects': list(subjects),
        'publication_types': list(pub_types),
        'languages': sorted(list(languages))
    })


@api_view(['GET'])
def search_suggestions(request):
    """
    Get search suggestions based on partial query
    
    Query Parameters:
    - q: Partial query string (minimum 2 characters)
    - type: 'all'|'title'|'author'|'subject' (default: 'all')
    
    Returns up to 10 suggestions
    
    Example:
    GET /api/search/suggestions/?q=harry&type=title
    """
    
    query = request.query_params.get('q', '')
    search_type = request.query_params.get('type', 'all')
    
    if len(query) < 2:
        return Response({'suggestions': []})
    
    suggestions = []
    
    if search_type in ['all', 'title']:
        titles = Publication.objects.filter(
            title__icontains=query
        ).values_list('title', flat=True).distinct()[:5]
        suggestions.extend([{'type': 'title', 'value': t} for t in titles])
    
    if search_type in ['all', 'author']:
        authors = Author.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).values('id', 'first_name', 'last_name')[:5]
        suggestions.extend([{
            'type': 'author',
            'value': f"{a['first_name']} {a['last_name']}",
            'id': a['id']
        } for a in authors])
    
    if search_type in ['all', 'subject']:
        subjects = Subject.objects.filter(
            name__icontains=query
        ).values('id', 'name')[:5]
        suggestions.extend([{
            'type': 'subject',
            'value': s['name'],
            'id': s['id']
        } for s in subjects])
    
    return Response({'suggestions': suggestions[:10]})


# ============================================================================
# FILTER BACKEND CLASSES
# ============================================================================

class PublicationFilterBackend(filters.FilterSet):
    """FilterSet for Publication model"""
    
    class Meta:
        model = Publication
        fields = {
            'title': ['icontains'],
            'language': ['exact'],
            'publication_date': ['gte', 'lte'],
            'authors': ['exact'],
            'subjects': ['exact'],
            'publication_type': ['exact'],
        }


# Add this to your main api/urls.py:
"""
from django.urls import path
from api.views import (
    AdvancedPublicationSearchView,
    search_facets,
    search_suggestions
)

urlpatterns = [
    # ... existing patterns ...
    
    # Advanced Search
    path('search/advanced/', AdvancedPublicationSearchView.as_view(), name='advanced-search'),
    path('search/facets/', search_facets, name='search-facets'),
    path('search/suggestions/', search_suggestions, name='search-suggestions'),
]
"""

from django.db.models import Q

# Advanced Search Module for TS OPAC eLibrary

from django.db.models import Q, Count
from django.utils import timezone
from catalog.models import Publication, Author, Subject, PublicationType, Item
from datetime import timedelta

class AdvancedSearch:
    """Advanced search engine with multiple filtering capabilities"""
    
    @staticmethod
    def full_text_search(query):
        """
        Perform full-text search across all publication fields
        
        Args:
            query (str): Search query string
            
        Returns:
            QuerySet: Publications matching the search query
        """
        if not query or len(query.strip()) == 0:
            return Publication.objects.none()
        
        q_objects = Q()
        q_objects |= Q(title__icontains=query)
        q_objects |= Q(subtitle__icontains=query)
        q_objects |= Q(abstract__icontains=query)
        q_objects |= Q(summary__icontains=query)
        q_objects |= Q(authors__first_name__icontains=query)
        q_objects |= Q(authors__last_name__icontains=query)
        q_objects |= Q(subjects__name__icontains=query)
        
        return Publication.objects.filter(q_objects).distinct()
    
    @staticmethod
    def filter_by_date_range(queryset, start_date=None, end_date=None):
        """
        Filter publications by publication date range
        
        Args:
            queryset: Initial queryset
            start_date (datetime): Start date (inclusive)
            end_date (datetime): End date (inclusive)
            
        Returns:
            QuerySet: Filtered publications
        """
        if start_date:
            queryset = queryset.filter(publication_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(publication_date__lte=end_date)
        return queryset
    
    @staticmethod
    def filter_by_authors(queryset, author_ids):
        """
        Filter publications by specific authors
        
        Args:
            queryset: Initial queryset
            author_ids (list): List of author IDs
            
        Returns:
            QuerySet: Publications by specified authors
        """
        if author_ids:
            queryset = queryset.filter(authors__id__in=author_ids).distinct()
        return queryset
    
    @staticmethod
    def filter_by_subjects(queryset, subject_ids):
        """
        Filter publications by subjects
        
        Args:
            queryset: Initial queryset
            subject_ids (list): List of subject IDs
            
        Returns:
            QuerySet: Publications with specified subjects
        """
        if subject_ids:
            queryset = queryset.filter(subjects__id__in=subject_ids).distinct()
        return queryset
    
    @staticmethod
    def filter_by_publication_type(queryset, pub_type_ids):
        """
        Filter publications by type
        
        Args:
            queryset: Initial queryset
            pub_type_ids (list): List of publication type IDs
            
        Returns:
            QuerySet: Publications of specified types
        """
        if pub_type_ids:
            queryset = queryset.filter(publication_type_id__in=pub_type_ids)
        return queryset
    
    @staticmethod
    def filter_by_language(queryset, language):
        """
        Filter publications by language
        
        Args:
            queryset: Initial queryset
            language (str): Language code (e.g., 'en', 'es', 'fr')
            
        Returns:
            QuerySet: Publications in specified language
        """
        if language:
            queryset = queryset.filter(language__iexact=language)
        return queryset
    
    @staticmethod
    def filter_by_availability(queryset, available_only=False):
        """
        Filter publications by availability
        
        Args:
            queryset: Initial queryset
            available_only (bool): If True, show only available items
            
        Returns:
            QuerySet: Available or all publications
        """
        if available_only:
            # Get publications with at least one available item
            queryset = queryset.filter(
                item__status='available'
            ).distinct()
        return queryset
    
    @staticmethod
    def sort_results(queryset, sort_by='relevance'):
        """
        Sort search results
        
        Args:
            queryset: Initial queryset
            sort_by (str): Sort criteria
                - 'relevance': Sort by search relevance (default)
                - 'date': Sort by publication date (newest first)
                - 'date_asc': Sort by publication date (oldest first)
                - 'title': Sort by title (A-Z)
                - 'title_desc': Sort by title (Z-A)
                - 'popularity': Sort by number of checkouts
                
        Returns:
            QuerySet: Sorted publications
        """
        if sort_by == 'date':
            queryset = queryset.order_by('-publication_date')
        elif sort_by == 'date_asc':
            queryset = queryset.order_by('publication_date')
        elif sort_by == 'title':
            queryset = queryset.order_by('title')
        elif sort_by == 'title_desc':
            queryset = queryset.order_by('-title')
        elif sort_by == 'popularity':
            # Sort by number of checkouts (requires loans data)
            queryset = queryset.annotate(
                checkout_count=Count('item__loans')
            ).order_by('-checkout_count')
        else:  # relevance
            queryset = queryset.order_by('-date_added')
        
        return queryset
    
    @staticmethod
    def faceted_search(queryset):
        """
        Generate faceted search results with counts
        
        Args:
            queryset: Search results queryset
            
        Returns:
            dict: Faceted data with counts for each filter option
        """
        return {
            'authors': Author.objects.filter(
                publication__in=queryset
            ).annotate(count=Count('publication')).values('id', 'first_name', 'last_name', 'count'),
            
            'subjects': Subject.objects.filter(
                publication__in=queryset
            ).annotate(count=Count('publication')).values('id', 'name', 'count'),
            
            'publication_types': PublicationType.objects.filter(
                publication__in=queryset
            ).annotate(count=Count('publication')).values('id', 'name', 'count'),
            
            'languages': queryset.values('language').distinct().annotate(
                count=Count('id')
            ).order_by('-count'),
            
            'availability': [
                {
                    'status': 'available',
                    'count': queryset.filter(item__status='available').distinct().count()
                },
                {
                    'status': 'checked_out',
                    'count': queryset.filter(item__status='checked_out').distinct().count()
                },
                {
                    'status': 'reserved',
                    'count': queryset.filter(item__status='reserved').distinct().count()
                }
            ]
        }
    
    @staticmethod
    def advanced_search(query='', author_ids=None, subject_ids=None, 
                       pub_type_ids=None, language=None, date_from=None, 
                       date_to=None, available_only=False, sort_by='relevance', 
                       limit=None):
        """
        Comprehensive advanced search with all filters
        
        Args:
            query (str): Search query string
            author_ids (list): Filter by author IDs
            subject_ids (list): Filter by subject IDs
            pub_type_ids (list): Filter by publication type IDs
            language (str): Filter by language
            date_from (datetime): Start date for publication date range
            date_to (datetime): End date for publication date range
            available_only (bool): Show only available items
            sort_by (str): Sort criteria
            limit (int): Limit number of results
            
        Returns:
            dict: Search results and faceted data
        """
        # Start with full-text search if query provided
        if query:
            queryset = AdvancedSearch.full_text_search(query)
        else:
            queryset = Publication.objects.all()
        
        # Apply filters
        queryset = AdvancedSearch.filter_by_authors(queryset, author_ids)
        queryset = AdvancedSearch.filter_by_subjects(queryset, subject_ids)
        queryset = AdvancedSearch.filter_by_publication_type(queryset, pub_type_ids)
        queryset = AdvancedSearch.filter_by_language(queryset, language)
        queryset = AdvancedSearch.filter_by_date_range(queryset, date_from, date_to)
        queryset = AdvancedSearch.filter_by_availability(queryset, available_only)
        
        # Sort results
        queryset = AdvancedSearch.sort_results(queryset, sort_by)
        
        # Get faceted data
        facets = AdvancedSearch.faceted_search(queryset)
        
        # Limit results if specified
        if limit:
            queryset = queryset[:limit]
        
        return {
            'results': queryset,
            'total_count': queryset.count(),
            'facets': facets
        }

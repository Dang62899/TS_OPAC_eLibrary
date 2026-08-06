from django.test import TestCase

from catalog.models import Publication, PublicationType
from catalog.search import AdvancedSearch


class AdvancedSearchTests(TestCase):
    def setUp(self):
        self.pub_type = PublicationType.objects.create(name="Manual", code="MAN", description="Manual")
        self.publication = Publication.objects.create(
            title="Emergency Response Manual",
            abstract="A practical guide for incident response.",
            publication_type=self.pub_type,
        )
        self.other_publication = Publication.objects.create(
            title="Network Security Guide",
            abstract="A guide for secure system administration.",
            publication_type=self.pub_type,
        )

    def test_boolean_and_phrase_search_returns_expected_results(self):
        result = AdvancedSearch.advanced_search(query='"Emergency Response" AND manual')

        self.assertEqual(result["total_count"], 1)
        self.assertEqual(list(result["results"]), [self.publication])

    def test_not_operator_excludes_matching_terms(self):
        result = AdvancedSearch.advanced_search(query='response NOT security')

        self.assertEqual(result["total_count"], 1)
        self.assertEqual(list(result["results"]), [self.publication])

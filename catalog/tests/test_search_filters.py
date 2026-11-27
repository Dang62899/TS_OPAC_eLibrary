from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User
from catalog.models import Attachment, Publication, PublicationType, Author, Subject


class SearchFilterTests(TestCase):
    def setUp(self):
        self.client = Client()
        user = User.objects.create_user(
            username="catalog-search-user",
            password="pass1234",
            agreed_to_terms=True,
        )
        self.client.force_login(user)
        self.pub_type = PublicationType.objects.create(name="Article", code="article")
        self.author1 = Author.objects.create(first_name="Alice", last_name="Smith")
        self.author2 = Author.objects.create(first_name="Bob", last_name="Jones")
        self.subject1 = Subject.objects.create(name="Physics")
        self.subject2 = Subject.objects.create(name="Chemistry")

        p1 = Publication.objects.create(title="Quantum Mechanics", publication_type=self.pub_type)
        p1.authors.add(self.author1)
        p1.subjects.add(self.subject1)

        p2 = Publication.objects.create(title="Organic Chemistry", publication_type=self.pub_type)
        p2.authors.add(self.author2)
        p2.subjects.add(self.subject2)

    def test_search_by_author_and_subject_checkboxes(self):
        url = reverse("catalog:search")
        # search for author1 by id
        resp = self.client.get(url, {"authors": [self.author1.id]})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Quantum Mechanics")
        self.assertNotContains(resp, "Organic Chemistry")

        # filter by subject2
        resp = self.client.get(url, {"subjects": [self.subject2.id]})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Organic Chemistry")
        self.assertNotContains(resp, "Quantum Mechanics")

    def test_single_query_searches_all_catalog_fields(self):
        response = self.client.get(reverse("catalog:search"), {"query": "Alice"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quantum Mechanics")
        self.assertNotContains(response, "Organic Chemistry")

    def test_search_can_be_limited_to_a_specific_field(self):
        title_response = self.client.get(
            reverse("catalog:search"),
            {"query": "Alice", "search_in": "title"},
        )
        author_response = self.client.get(
            reverse("catalog:search"),
            {"query": "Alice", "search_in": "author"},
        )

        self.assertEqual(title_response.status_code, 200)
        self.assertNotContains(title_response, "Quantum Mechanics")
        self.assertEqual(author_response.status_code, 200)
        self.assertContains(author_response, "Quantum Mechanics")
        self.assertNotContains(author_response, "Organic Chemistry")

    def test_multiple_catalog_filters_combine(self):
        second_type = PublicationType.objects.create(name="Manual", code="manual")
        matching = Publication.objects.create(title="Alice Physics Manual", publication_type=second_type)
        matching.authors.add(self.author1)
        matching.subjects.add(self.subject1)
        other = Publication.objects.create(title="Alice Chemistry Manual", publication_type=second_type)
        other.authors.add(self.author1)
        other.subjects.add(self.subject2)

        response = self.client.get(
            reverse("catalog:search"),
            {
                "publication_types": [self.pub_type.pk, second_type.pk],
                "authors": [self.author1.pk],
                "subjects": [self.subject1.pk],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quantum Mechanics")
        self.assertContains(response, "Alice Physics Manual")
        self.assertNotContains(response, "Organic Chemistry")
        self.assertNotContains(response, "Alice Chemistry Manual")

    def test_search_page_has_one_query_and_checkbox_type_filters(self):
        response = self.client.get(reverse("catalog:search"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>Search Catalog - TS eLibrary</title>")
        self.assertContains(response, '/static/images/TS_Logo.jpg')
        self.assertContains(response, 'type="search" name="query"')
        self.assertContains(response, 'name="search_in"')
        self.assertContains(response, 'name="publication_types"')

    def test_search_suggestions_return_catalog_authors_for_query_parameter(self):
        response = self.client.get(reverse("catalog:search_suggestions"), {"query": "Alice"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["suggestions"], ["Alice Smith"])

    def test_search_page_exposes_autocomplete_endpoint(self):
        response = self.client.get(reverse("catalog:search"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="query"')
        self.assertContains(response, f'data-suggestions-url="{reverse("catalog:search_suggestions")}"')

    def test_research_browse_filters_by_year_and_class(self):
        research_type = PublicationType.objects.create(name="Research Paper", code="paper")
        matching = Publication.objects.create(
            title="Matching Paper",
            publication_type=research_type,
            research_year=2025,
            research_class="A",
        )
        Publication.objects.create(
            title="Different Class",
            publication_type=research_type,
            research_year=2025,
            research_class="B",
        )
        Publication.objects.create(
            title="Different Year",
            publication_type=research_type,
            research_year=2024,
            research_class="A",
        )
        Publication.objects.create(
            title="Not Research",
            publication_type=self.pub_type,
            research_year=2025,
            research_class="A",
        )

        response = self.client.get(
            reverse("catalog:browse_research"),
            {"year": "2025", "class": "A"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, matching.title)
        self.assertNotContains(response, "Different Class")
        self.assertNotContains(response, "Different Year")
        self.assertNotContains(response, "Not Research")
        self.assertContains(response, 'name="year"')
        self.assertContains(response, 'name="class"')

    def test_search_filters_by_class_format_and_download_permission(self):
        matching = Publication.objects.create(
            title="Class A PDF",
            publication_type=self.pub_type,
            research_class="Class A",
        )
        Attachment.objects.create(
            publication=matching,
            file=SimpleUploadedFile("guide.pdf", b"pdf-content", content_type="application/pdf"),
            allow_download=True,
            attachment_type="sop",
            class_field="Class A",
            unit="HAS",
            tags="safety, evacuation",
        )
        restricted = Publication.objects.create(
            title="Class A Restricted Video",
            publication_type=self.pub_type,
            research_class="Class A",
        )
        Attachment.objects.create(
            publication=restricted,
            attachment_type="video",
            class_field="Class A",
            is_external=True,
            external_url="https://example.com/video",
            allow_download=False,
            unit="951",
        )
        Publication.objects.create(
            title="Class B PDF",
            publication_type=self.pub_type,
            research_class="Class B",
        )
        split_resources = Publication.objects.create(
            title="Separate PDF and video resources",
            publication_type=self.pub_type,
            research_class="Class A",
        )
        Attachment.objects.create(
            publication=split_resources,
            file=SimpleUploadedFile("restricted.pdf", b"pdf-content", content_type="application/pdf"),
            attachment_type="sop",
            allow_download=False,
            unit="HAS",
            class_field="Class A",
            tags="safety",
        )
        Attachment.objects.create(
            publication=split_resources,
            is_external=True,
            external_url="https://example.com/sop",
            attachment_type="sop",
            allow_download=True,
            unit="HAS",
            class_field="Class A",
            tags="safety",
        )

        response = self.client.get(
            reverse("catalog:search"),
            {
                "research_class": "Class A",
                "resource_type": "sop",
                "tag": "safety",
                "format": "pdf",
                "downloadable": "true",
                "unit": "HAS",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, matching.title)
        self.assertNotContains(response, restricted.title)
        self.assertNotContains(response, "Class B PDF")
        self.assertNotContains(response, split_resources.title)

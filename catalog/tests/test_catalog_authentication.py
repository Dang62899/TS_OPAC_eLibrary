from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from catalog.models import Author, Publication, PublicationType, Subject


class CatalogAuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="catalog-reader",
            password="pass1234",
            agreed_to_terms=True,
        )
        self.publication_type = PublicationType.objects.create(name="Manual", code="manual")
        self.publication = Publication.objects.create(
            title="Library Operations Manual",
            publication_type=self.publication_type,
        )
        subject = Subject.objects.create(name="Library Science")
        author = Author.objects.create(first_name="Alex", last_name="Reader")
        self.publication.subjects.add(subject)
        self.publication.authors.add(author)

    def test_book_routes_redirect_anonymous_visitors_to_login(self):
        protected_urls = [
            reverse("catalog:search"),
            reverse("catalog:search_suggestions"),
            reverse("catalog:publication_detail", args=[self.publication.pk]),
            reverse("catalog:browse_by_type", args=[self.publication_type.pk]),
            reverse("catalog:browse_by_subject", args=[self.publication.subjects.first().pk]),
            reverse("catalog:browse_by_author", args=[self.publication.authors.first().pk]),
            reverse("catalog:browse_research"),
            reverse("catalog:preview_merged_attachment", args=[1]),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_homepage_hides_book_controls_until_login(self):
        homepage_url = reverse("catalog:index")

        anonymous_response = self.client.get(homepage_url)
        self.assertRedirects(anonymous_response, reverse("accounts:login"))

        self.client.force_login(self.user)
        authenticated_response = self.client.get(homepage_url)
        self.assertContains(authenticated_response, 'name="query"')
        self.assertContains(authenticated_response, "Browse by Type")
        self.assertContains(authenticated_response, "Find resources")

    def test_authenticated_user_can_view_publication(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("catalog:publication_detail", args=[self.publication.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.publication.title)

"""Tests for API endpoints"""

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class APIAuthenticationTests(TestCase):
    """Test API authentication"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )

    def test_token_auth(self):
        """Test obtaining authentication token"""
        response = self.client.post(
            "/api/v1/auth/token/",
            {"username": "testuser", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)

    def test_user_registration(self):
        """Test user registration endpoint"""
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "newuser",
                "email": "new@example.com",
                "password": "securepass123",
                "password_confirm": "securepass123",
            },
        )
        self.assertEqual(response.status_code, 201)


class APICatalogTests(TestCase):
    """Test catalog endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

    def test_list_publications(self):
        """Test listing publications"""
        response = self.client.get("/api/v1/publications/")
        self.assertEqual(response.status_code, 200)

    def test_list_requires_auth(self):
        """Test that publications list requires authentication"""
        client = APIClient()
        response = client.get("/api/v1/publications/")
        self.assertEqual(response.status_code, 401)

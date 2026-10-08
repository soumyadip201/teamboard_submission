from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Company, KBEntry, QueryLog


class TeamBoardTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="acmecorp",
            password="securepass123",
            email="dev@acmecorp.com",
        )
        self.user1.company.company_name = "Acme Corp"
        self.user1.company.save(update_fields=["company_name"])

        self.user2 = User.objects.create_user(
            username="betacorp",
            password="securepass123",
            email="dev@betacorp.com",
        )
        self.user2.company.company_name = "Beta Corp"
        self.user2.company.save(update_fields=["company_name"])

        KBEntry.objects.bulk_create([
            KBEntry(
                question="What is select_related in Django ORM?",
                answer="It performs a SQL JOIN for related objects.",
                category=KBEntry.Category.DATABASE,
            ),
            KBEntry(
                question="What is prefetch_related?",
                answer="It fetches related objects using additional queries.",
                category=KBEntry.Category.DATABASE,
            ),
            KBEntry(
                question="What is a JWT token?",
                answer="A signed token used for stateless authentication.",
                category=KBEntry.Category.API,
            ),
        ])

    def auth(self, user):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}"
        )


class SignalTests(TeamBoardTestCase):
    def test_user_creation_auto_creates_company_and_api_key(self):
        user = User.objects.create_user(
            username="newcompany",
            password="securepass123",
            email="hello@newcompany.com",
        )
        company = user.company
        self.assertEqual(company.role, Company.Role.CLIENT)
        self.assertTrue(company.api_key)
        self.assertLessEqual(len(company.api_key), 64)


class AuthenticationTests(TeamBoardTestCase):
    def test_register_returns_jwt_and_api_key(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "newco",
                "password": "securepass123",
                "company_name": "New Co",
                "email": "dev@newco.com",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["api_key"])
        self.assertTrue(response.data["access"])
        self.assertEqual(User.objects.get(username="newco").company.company_name, "New Co")

    def test_register_duplicate_username_returns_400(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "acmecorp",
                "password": "securepass123",
                "company_name": "Another Corp",
                "email": "other@example.com",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Username already exists", response.data["error"])

    def test_login_valid_credentials_returns_token_and_company_credentials(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "acmecorp", "password": "securepass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["access"])
        self.assertEqual(response.data["company_name"], "Acme Corp")
        self.assertEqual(response.data["api_key"], self.user1.company.api_key)

    def test_login_invalid_password_returns_401(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "acmecorp", "password": "wrongpassword"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)


class KnowledgeBaseQueryTests(TeamBoardTestCase):
    def test_query_without_token_returns_401(self):
        response = self.client.post(
            "/api/kb/query/",
            {"search": "select_related"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_query_uses_case_insensitive_question_or_answer_search(self):
        self.auth(self.user1)
        response = self.client.post(
            "/api/kb/query/",
            {"search": "SELECT_RELATED"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["category"], "database")

    def test_query_creates_query_log_with_result_count(self):
        self.auth(self.user1)
        response = self.client.post(
            "/api/kb/query/",
            {"search": "JWT"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        log = QueryLog.objects.get(company=self.user1.company)
        self.assertEqual(log.search_term, "JWT")
        self.assertEqual(log.results_count, 1)

    def test_zero_result_query_still_creates_log(self):
        self.auth(self.user1)
        response = self.client.post(
            "/api/kb/query/",
            {"search": "does-not-exist"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])
        log = QueryLog.objects.get(company=self.user1.company)
        self.assertEqual(log.results_count, 0)

    def test_missing_search_returns_400(self):
        self.auth(self.user1)
        response = self.client.post("/api/kb/query/", {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_query_is_scoped_to_authenticated_company_for_logging(self):
        self.auth(self.user2)
        self.client.post("/api/kb/query/", {"search": "JWT"}, format="json")
        self.assertEqual(QueryLog.objects.filter(company=self.user2.company).count(), 1)
        self.assertEqual(QueryLog.objects.filter(company=self.user1.company).count(), 0)

    @patch("api.views.QueryLog.objects.create")
    def test_query_log_failure_rolls_back_transaction(self, mock_create):
        mock_create.side_effect = IntegrityError("simulated failure")
        self.auth(self.user1)
        before = KBEntry.objects.count()
        with self.assertRaises(IntegrityError):
            self.client.post(
                "/api/kb/query/",
                {"search": "JWT"},
                format="json",
            )
        self.assertEqual(KBEntry.objects.count(), before)
        self.assertEqual(QueryLog.objects.filter(company=self.user1.company).count(), 0)


class AdminUsageTests(TeamBoardTestCase):
    def setUp(self):
        super().setUp()
        QueryLog.objects.create(company=self.user1.company, search_term="JWT", results_count=1)
        QueryLog.objects.create(company=self.user1.company, search_term="JWT", results_count=0)
        QueryLog.objects.create(company=self.user1.company, search_term="Q objects", results_count=1)

    def test_client_receives_403_for_usage_summary(self):
        self.auth(self.user1)
        response = self.client.get("/api/admin/usage-summary/")
        self.assertEqual(response.status_code, 403)

    def test_admin_receives_platform_usage_summary(self):
        self.user1.company.role = Company.Role.ADMIN
        self.user1.company.save(update_fields=["role"])
        self.auth(self.user1)
        response = self.client.get("/api/admin/usage-summary/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_queries"], 3)
        self.assertEqual(response.data["active_companies"], 1)
        self.assertEqual(response.data["top_search_terms"][0]["search_term"], "JWT")
        self.assertEqual(response.data["top_search_terms"][0]["count"], 2)

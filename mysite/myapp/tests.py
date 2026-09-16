from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import AnalyticsEvent, Country, Scholarship
from .analytics import get_client_ip, get_visitor_country, log_event


class CountryAnalyticsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="adminpassword123",
            email="admin@example.com"
        )
        self.country = Country.objects.create(name="Canada", slug="canada")
        self.scholarship = Scholarship.objects.create(
            title="Vanier Canada Graduate Scholarship",
            slug="vanier-canada-graduate-scholarship",
            country=self.country,
            degree_level="phd",
            funding_type="full",
            deadline=timezone.now().date(),
            description="Prestigious PhD scholarship in Canada.",
            eligibility="All nationalities",
            application_link="https://example.com/apply",
            is_published=True
        )

    def test_get_client_ip(self):
        # 1. CF-Connecting-IP
        req = self.factory.get("/")
        req.META["HTTP_CF_CONNECTING_IP"] = "102.89.23.4"
        self.assertEqual(get_client_ip(req), "102.89.23.4")

        # 2. X-Forwarded-For
        req = self.factory.get("/")
        req.META["HTTP_X_FORWARDED_FOR"] = "197.210.55.2, 10.0.0.1"
        self.assertEqual(get_client_ip(req), "197.210.55.2")

        # 3. REMOTE_ADDR
        req = self.factory.get("/")
        req.META["REMOTE_ADDR"] = "127.0.0.1"
        self.assertEqual(get_client_ip(req), "127.0.0.1")

    def test_get_visitor_country_from_headers(self):
        # Cloudflare header with "NG" -> Nigeria
        req = self.factory.get("/")
        req.session = {}
        req.META["HTTP_CF_IPCOUNTRY"] = "NG"
        country = get_visitor_country(req)
        self.assertEqual(country, "Nigeria")
        self.assertEqual(req.session.get("visitor_country"), "Nigeria")

        # Reverse proxy header with "GB" -> United Kingdom
        req2 = self.factory.get("/")
        req2.session = {}
        req2.META["HTTP_X_COUNTRY_CODE"] = "GB"
        self.assertEqual(get_visitor_country(req2), "United Kingdom")

        # Reverse proxy header with "GH" -> Ghana
        req3 = self.factory.get("/")
        req3.session = {}
        req3.META["HTTP_X_COUNTRY_CODE"] = "GH"
        self.assertEqual(get_visitor_country(req3), "Ghana")

        # Test header override
        req4 = self.factory.get("/")
        req4.session = {}
        req4.META["HTTP_X_TEST_COUNTRY"] = "England"
        self.assertEqual(get_visitor_country(req4), "England")

    def test_log_event_records_country(self):
        req = self.factory.get("/")
        req.session = self.client.session
        req.META["HTTP_CF_IPCOUNTRY"] = "NG"

        log_event(req, "scholarship_view", scholarship=self.scholarship)

        event = AnalyticsEvent.objects.latest("id")
        self.assertEqual(event.event_type, "scholarship_view")
        self.assertEqual(event.country, "Nigeria")
        self.assertEqual(event.scholarship, self.scholarship)

    def test_admin_statistics_sorted_by_country_visitors(self):
        # Create events for multiple countries:
        # Nigeria: 5 visitors
        # England: 4 visitors
        # United States: 3 visitors
        # Ghana: 1 visitor
        countries_distribution = [
            ("Nigeria", 5),
            ("England", 4),
            ("United States", 3),
            ("Ghana", 1),
        ]

        for country_name, visitor_count in countries_distribution:
            for i in range(visitor_count):
                AnalyticsEvent.objects.create(
                    event_type="page_view",
                    session_key=f"session_{country_name}_{i}",
                    country=country_name,
                    created_at=timezone.now()
                )

        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin_statistics"))
        self.assertEqual(response.status_code, 200)

        country_stats = response.context["country_stats"]
        self.assertEqual(len(country_stats), 4)

        # Verify ordering from highest to lowest: Nigeria (5), England (4), United States (3), Ghana (1)
        self.assertEqual(country_stats[0]["country"], "Nigeria")
        self.assertEqual(country_stats[0]["visitors"], 5)

        self.assertEqual(country_stats[1]["country"], "England")
        self.assertEqual(country_stats[1]["visitors"], 4)

        self.assertEqual(country_stats[2]["country"], "United States")
        self.assertEqual(country_stats[2]["visitors"], 3)

        self.assertEqual(country_stats[3]["country"], "Ghana")
        self.assertEqual(country_stats[3]["visitors"], 1)

        # Verify HTML contains the table and country names
        content = response.content.decode("utf-8")
        self.assertIn("Traffic by Country", content)
        self.assertIn("Nigeria", content)
        self.assertIn("England", content)
        self.assertIn("United States", content)
        self.assertIn("Ghana", content)

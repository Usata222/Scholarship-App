from django.contrib.sitemaps import Sitemap
from .models import Scholarship, Country

class ScholarshipSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Scholarship.objects.filter(is_published=True)

    def location(self, obj):
        return f"/scholarship/{obj.slug}/"

class CountrySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Country.objects.all()

    def location(self, obj):
        return f"/country/{obj.slug}/"
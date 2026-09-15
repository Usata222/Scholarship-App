from django.db import models
import uuid

# Create your models here.
class Country(models.Model): # creating the database country
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True) # slug is a url safe version

    class Meta: # to prevent countrys instead of countries
        verbose_name_plural = "Countries"

    def __str__(self): # to prevent "country object(1)"
        return self.name


class Scholarship(models.Model):
    DEGREE_LEVEL_CHOICES = [
        ("undergraduate", "Undergraduate"),
        ("masters", "Master's"),
        ("phd", "PhD"),
    ]

    FUNDING_TYPE_CHOICES = [
        ("full", "Fully Funded"),
        ("partial", "Partially Funded"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="scholarships") # if a country is deleted, all scholarships related to that country will also be deleted, to get all scholarships related to a country, we can use country.scholarships.all() 
    degree_level = models.CharField(max_length=20, choices=DEGREE_LEVEL_CHOICES)
    funding_type = models.CharField(max_length=10, choices=FUNDING_TYPE_CHOICES)
    deadline = models.DateField()
    description = models.TextField()
    eligibility = models.TextField()
    required_documents = models.TextField(blank=True) #blank=True means that this field is optional
    application_link = models.URLField()
    image = models.ImageField(upload_to='scholarships/', blank=True, null=True)

    is_featured = models.BooleanField(default=False)
    deadline_reminder_sent = models.BooleanField(default=False)  # prevents sending the "closing soon" email more than once per scholarship
    is_published = models.BooleanField(default=False) #default=False means that this new scholarship will not be published by default, it will be published only when the admin approves it
    view_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class AnalyticsEvent(models.Model):
    # One table for every tracked event type, instead of a separate model per event.
    # Each row is a single thing that happened: a page view, a scholarship view,
    # an application click, a search/filter, or a save.
    EVENT_TYPE_CHOICES = [
        ("page_view", "Page View"),
        ("scholarship_view", "Scholarship View"),
        ("application_click", "Application Click"),
        ("search", "Search / Filter"),
        ("save", "Scholarship Saved"),
    ]

    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, db_index=True)
    scholarship = models.ForeignKey(
        Scholarship, on_delete=models.SET_NULL, null=True, blank=True, related_name="analytics_events"
    )
    page_path = models.CharField(max_length=255, blank=True)
    search_summary = models.CharField(max_length=255, blank=True)  # e.g. "country=germany, level=masters"
    result_count = models.PositiveIntegerField(null=True, blank=True)  # only set for 'search' events

    # session_key (not the visitor's IP) stands in for "one visitor" -- an opaque,
    # rotating token Django already manages, so we get visitor counts without
    # permanently storing anything that identifies a real person.
    session_key = models.CharField(max_length=40, blank=True)
    utm_source = models.CharField(max_length=100, blank=True)
    referrer = models.CharField(max_length=300, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.event_type} @ {self.created_at:%Y-%m-%d %H:%M}"


class ScholarshipSubmission(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    organization_name = models.CharField(max_length=200)
    contact_email = models.EmailField()
    title = models.CharField(max_length=200)
    country_name = models.CharField(max_length=100)
    degree_level = models.CharField(max_length=20, choices=Scholarship.DEGREE_LEVEL_CHOICES)
    funding_type = models.CharField(max_length=10, choices=Scholarship.FUNDING_TYPE_CHOICES)
    deadline = models.DateField()
    description = models.TextField()
    eligibility = models.TextField()
    required_documents = models.TextField(blank=True)
    application_link = models.URLField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.organization_name})"


class CoachingRequest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
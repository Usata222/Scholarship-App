from django.db import models

# Create your models here.
class Country(models.Model): # creating the database country
    name = models.CharField(max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True) # slug is a url safe version

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

    is_published = models.BooleanField(default=False) #default=False means that this new scholarship will not be published by default, it will be published only when the admin approves it
    view_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
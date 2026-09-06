from django.contrib import admin
from .models import Country, Scholarship

class CountryAdmin(admin.ModelAdmin): # country admin class to customize the admin interface for the Country model
    prepopulated_fields = {"slug": ("name",)} # this line tells Django to automatically populate the slug field based on the name field when creating a new Country object in the admin interface
    search_fields = ["name"]# 

class ScholarshipAdmin(admin.ModelAdmin): # scholarship admin class to customize the admin interface for the Scholarship model
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["country"]
    list_display = ["title", "country", "is_published", "is_featured", "deadline"]

admin.site.register(Country, CountryAdmin) # Register the Country model with the custom admin class
admin.site.register(Scholarship, ScholarshipAdmin) # Register the Scholarship model with the custom admin class
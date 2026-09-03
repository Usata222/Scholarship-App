from django.contrib import admin
from .models import Country, Scholarship

class CountryAdmin(admin.ModelAdmin): # country admin class to customize the admin interface for the Country model
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]

class ScholarshipAdmin(admin.ModelAdmin): # scholarship admin class to customize the admin interface for the Scholarship model
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["country"]

admin.site.register(Country, CountryAdmin)
admin.site.register(Scholarship, ScholarshipAdmin)
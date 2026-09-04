from django.db.models import F # The F() function is used to reference the value of a model field in a query, allowing for database-level operations without having to retrieve the object into Python memory first. In this case, it is used to increment the click_count field of the Scholarship model directly in the database.
from .models import Scholarship, Country
from django.shortcuts import render, get_object_or_404, redirect

def scholarship_detail(request, slug): # every django view function takes at least one argument, which is the request object, and in this case we are also taking a slug argument to identify the scholarship
    scholarship = get_object_or_404(Scholarship, slug=slug, is_published=True) # it fetches the scholarship object from the database based on the slug and is_published=True, if it doesn't find it, it raises a 404 error
    scholarship.view_count = scholarship.view_count + 1 # incrementing the view count of the scholarship by 1 every time the scholarship detail page is accessed
    scholarship.save(update_fields=["view_count"])
    context = {                       # passing data to the template using a context dictionary, which is a way to pass data from the view to the template
        "scholarship": scholarship,
    }
    return render(request, "myapp/scholarship_detail.html", context) # tells Django to render the scholarship_detail.html template with the context data, which will be used to display the scholarship details on the webpage


def home(request):
    scholarships = Scholarship.objects.filter(is_published=True).order_by('-created_at') # this line fetches all the scholarships from the database that are published and orders them by their creation date in descending order

    country_slug = request.GET.get('country')# this line retrieves the value of the 'country' parameter from the GET request, which is used to filter scholarships by country if provided
    if country_slug:   # this line checks if a country slug was provided in the GET request, and if so, it filters the scholarships to only include those that belong to the specified country
        scholarships = scholarships.filter(country__slug=country_slug)   # this line filters the scholarships queryset to only include scholarships that belong to the country with the specified slug, using Django's double underscore notation to traverse relationships between models

    degree_level = request.GET.get('level')
    if degree_level:
        scholarships = scholarships.filter(degree_level=degree_level)

    funding_type = request.GET.get('funding')
    if funding_type:
        scholarships = scholarships.filter(funding_type=funding_type)

    context = {    # this line creates a context dictionary that will be passed to the template, containing the filtered scholarships and the choices for degree level and funding type, which can be used to populate filter options in the template
        "scholarships": scholarships, # this line adds the filtered scholarships to the context dictionary
        "degree_level_choices": Scholarship.DEGREE_LEVEL_CHOICES, # passing the degree level choices to the context dictionary, which can be used in the template to display filter options for degree levels
        "funding_type_choices": Scholarship.FUNDING_TYPE_CHOICES,
    }
    return render(request, "myapp/home.html", context)


def country_detail(request, slug):
    country = get_object_or_404(Country, slug=slug)
    scholarships = country.scholarships.filter(is_published=True).order_by('-created_at')
    context = {
        "country": country,
        "scholarships": scholarships,
    }
    return render(request, "myapp/country_detail.html", context)


def scholarship_redirect(request, slug):
    scholarship = get_object_or_404(Scholarship, slug=slug, is_published=True)
    Scholarship.objects.filter(pk=scholarship.pk).update(click_count=F('click_count') + 1)
    return redirect(scholarship.application_link)



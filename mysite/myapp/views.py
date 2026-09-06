from django.db.models import F # The F() function is used to reference the value of a model field in a query, allowing for database-level operations without having to retrieve the object into Python memory first. In this case, it is used to increment the click_count field of the Scholarship model directly in the database.
from .models import Scholarship, Country
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone # The timezone module is used to work with time zones in Django. It provides utilities for working with date and time, including functions to get the current time in a specific time zone. In this code, it is used to get the current date to filter scholarships based on their deadlines.
from datetime import timedelta

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

    today = timezone.now().date()
    featured_scholarships = Scholarship.objects.filter(is_published=True, is_featured=True).order_by('-created_at')[:5]
    deadline_soon = Scholarship.objects.filter(
        is_published=True,
        deadline__gte=today,
        deadline__lte=today + timedelta(days=14),
    ).order_by('deadline')[:5]

    context = {    # this line creates a context dictionary that will be passed to the template, containing the filtered scholarships and the choices for degree level and funding type, which can be used to populate filter options in the template
        "scholarships": scholarships, # this line adds the filtered scholarships to the context dictionary
        "countries": Country.objects.all().order_by('name'), # getting all the countries from the database and ordering them by name, which can be used in the template to display a list of countries for filtering scholarships
        "degree_level_choices": Scholarship.DEGREE_LEVEL_CHOICES, # passing the degree level choices to the context dictionary, which can be used in the template to display filter options for degree levels
        "funding_type_choices": Scholarship.FUNDING_TYPE_CHOICES,
        "featured_scholarships": featured_scholarships,
        "deadline_soon": deadline_soon,
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


def toggle_save(request, slug): # this function is used to toggle the saved status of a scholarship for the current user session. It checks if the scholarship is already saved in the session, and if so, it removes it; otherwise, it adds it to the saved list. The updated list of saved scholarships is then stored back in the session, and the user is redirected to the scholarship detail page.
    scholarship = get_object_or_404(Scholarship, slug=slug, is_published=True) # this line retrieves the scholarship object from the database based on the provided slug and ensures that it is published. If the scholarship does not exist or is not published, a 404 error is raised.
    saved = request.session.get('saved_scholarships', []) # this line retrieves the list of saved scholarships from the user's session. If the 'saved_scholarships' key does not exist in the session, it initializes an empty list. This allows the application to keep track of which scholarships the user has saved during their session.

    if scholarship.pk in saved:
        saved.remove(scholarship.pk) # this line checks if the primary key (pk) of the scholarship is already in the saved list. If it is, it removes the pk from the list, effectively "unsaving" the scholarship for the user.
    else:
        saved.append(scholarship.pk) # if the scholarship's pk is not in the saved list, this line adds it to the list, effectively "saving" the scholarship for the user.

    request.session['saved_scholarships'] = saved # this line updates the user's session with the modified list of saved scholarships. It ensures that the changes made to the saved list (either adding or removing a scholarship) are persisted in the session data.
    return redirect('scholarship_detail', slug=slug)

def saved_scholarships(request): # this function retrieves the list of saved scholarships from the user's session and fetches the corresponding Scholarship objects from the database. It then renders a template to display the saved scholarships to the user.
    saved_ids = request.session.get('saved_scholarships', []) # this line retrieves the list of saved scholarship IDs from the user's session. If the 'saved_scholarships' key does not exist in the session, it initializes an empty list. This allows the application to keep track of which scholarships the user has saved during their session.
    scholarships = Scholarship.objects.filter(pk__in=saved_ids, is_published=True)
    context = {
        "scholarships": scholarships,
    }
    return render(request, "myapp/saved_scholarships.html", context)



from django.db.models import F, Sum # The F() function is used to reference the value of a model field in a query, allowing for database-level operations without having to retrieve the object into Python memory first. In this case, it is used to increment the click_count field of the Scholarship model directly in the database.
from .models import Scholarship, Country
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone # The timezone module is used to work with time zones in Django. It provides utilities for working with date and time, including functions to get the current time in a specific time zone. In this code, it is used to get the current date to filter scholarships based on their deadlines.
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import ScholarshipForm
from .forms import ScholarshipForm, CountryForm
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from .models import Scholarship, Country, ScholarshipSubmission, CoachingRequest, NewsletterSubscriber
from .forms import ScholarshipForm, CountryForm, SubmissionForm, CoachingRequestForm, NewsletterForm


@login_required
def admin_country_list(request):
    countries = Country.objects.all().order_by('name')
    context = {"countries": countries}
    return render(request, "myapp/admin_country_list.html", context)


@login_required
def admin_country_add(request):
    if request.method == "POST":
        form = CountryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_country_list')
    else:
        form = CountryForm()

    context = {"form": form}
    return render(request, "myapp/admin_country_form.html", context)


@login_required
def admin_country_edit(request, pk):
    country = get_object_or_404(Country, pk=pk)
    if request.method == "POST":
        form = CountryForm(request.POST, instance=country)
        if form.is_valid():
            form.save()
            return redirect('admin_country_list')
    else:
        form = CountryForm(instance=country)

    context = {"form": form}
    return render(request, "myapp/admin_country_form.html", context)


@login_required
def admin_country_delete(request, pk):
    country = get_object_or_404(Country, pk=pk)
    scholarship_count = country.scholarships.count()
    if request.method == "POST":
        country.delete()
        return redirect('admin_country_list')

    context = {"country": country, "scholarship_count": scholarship_count}
    return render(request, "myapp/admin_country_delete.html", context)


@login_required
def admin_scholarship_delete(request, pk): # this function is decorated with the @login_required decorator, which means that only authenticated users can access this view. If an unauthenticated user tries to access it, they will be redirected to the login page. The function retrieves a Scholarship object based on its primary key (pk) and allows the admin user to delete it. If the request method is POST, it deletes the scholarship and redirects to the scholarship list. If the request method is GET, it renders a confirmation page asking the admin user to confirm the deletion.
    scholarship = get_object_or_404(Scholarship, pk=pk)
    if request.method == "POST":
        scholarship.delete()
        return redirect('admin_scholarship_list')

    context = {"scholarship": scholarship}
    return render(request, "myapp/admin_scholarship_delete.html", context)

@login_required 
def admin_scholarship_edit(request, pk): # this function is decorated with the @login_required decorator, which means that only authenticated users can access this view. If an unauthenticated user tries to access it, they will be redirected to the login page. The function retrieves a Scholarship object based on its primary key (pk) and allows the admin user to edit its details using a form. If the request method is POST, it processes the submitted form data; if valid, it saves the changes and redirects to the scholarship list. If the request method is GET, it displays the form pre-filled with the scholarship's current data.
    scholarship = get_object_or_404(Scholarship, pk=pk)
    if request.method == "POST":
        form = ScholarshipForm(request.POST, instance=scholarship)
        if form.is_valid():
            form.save()
            return redirect('admin_scholarship_list')
    else:
        form = ScholarshipForm(instance=scholarship)

    context = {"form": form}
    return render(request, "myapp/admin_scholarship_form.html", context)

@login_required
def admin_scholarship_add(request):
    if request.method == "POST":
        form = ScholarshipForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_scholarship_list')
    else:
        form = ScholarshipForm()

    context = {"form": form}
    return render(request, "myapp/admin_scholarship_form.html", context)

@login_required
def admin_dashboard(request): # this function is decorated with the @login_required decorator, which means that only authenticated users can access this view. If an unauthenticated user tries to access it, they will be redirected to the login page.
    total_scholarships = Scholarship.objects.count()
    published_count = Scholarship.objects.filter(is_published=True).count()
    total_clicks = Scholarship.objects.aggregate(total=Sum('click_count'))['total'] or 0

    context = { # this line creates a context dictionary that will be passed to the template, containing the total number of scholarships, the count of published scholarships, and the total number of clicks across all scholarships. This data can be used in the template to display statistics on the admin dashboard.
        "total_scholarships": total_scholarships,
        "published_count": published_count,
        "total_clicks": total_clicks,
    }
    return render(request, "myapp/admin_dashboard.html", context)

def admin_login(request): # this function handles the login process for the admin user. It checks if the request method is POST, retrieves the username and password from the request, and uses Django's built-in authenticate function to verify the credentials. If the authentication is successful, it logs in the user and redirects them to the admin dashboard. If authentication fails, it renders the login page again with an error message. If the request method is not POST, it simply renders the login page.
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            return render(request, "myapp/admin_login.html", {"error": "Invalid username or password"})
    return render(request, "myapp/admin_login.html")


def admin_logout(request): # this function logs out the currently authenticated user and redirects them to the admin login page. It uses Django's built-in logout function to clear the user's session and authentication data.
    logout(request)
    return redirect('admin_login')


@login_required
def admin_scholarship_list(request):
    scholarships = Scholarship.objects.all().order_by('-created_at')
    paginator = Paginator(scholarships, 20)
    page_number = request.GET.get('page')
    scholarships_page = paginator.get_page(page_number)
    context = {"scholarships": scholarships_page}
    return render(request, "myapp/admin_scholarship_list.html", context)


def scholarship_detail(request, slug): # every django view function takes at least one argument, which is the request object, and in this case we are also taking a slug argument to identify the scholarship
    scholarship = get_object_or_404(Scholarship, slug=slug, is_published=True) # it fetches the scholarship object from the database based on the slug and is_published=True, if it doesn't find it, it raises a 404 error
    scholarship.view_count = scholarship.view_count + 1 # incrementing the view count of the scholarship by 1 every time the scholarship detail page is accessed
    scholarship.save(update_fields=["view_count"])
    context = {                       # passing data to the template using a context dictionary, which is a way to pass data from the view to the template
        "scholarship": scholarship,
    }
    return render(request, "myapp/scholarship_detail.html", context) # tells Django to render the scholarship_detail.html template with the context data, which will be used to display the scholarship details on the webpage


def home(request):
    scholarships = Scholarship.objects.filter(is_published=True).order_by('-created_at')

    country_slug = request.GET.get('country')
    if country_slug:
        scholarships = scholarships.filter(country__slug=country_slug)

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

    paginator = Paginator(scholarships, 12)
    page_number = request.GET.get('page')
    scholarships_page = paginator.get_page(page_number)

    querydict = request.GET.copy()
    if 'page' in querydict:
        del querydict['page']
    querystring = querydict.urlencode()

    context = {
        "scholarships": scholarships_page,
        "countries": Country.objects.all().order_by('name'),
        "degree_level_choices": Scholarship.DEGREE_LEVEL_CHOICES,
        "funding_type_choices": Scholarship.FUNDING_TYPE_CHOICES,
        "featured_scholarships": featured_scholarships,
        "deadline_soon": deadline_soon,
        "querystring": querystring,
    }
    return render(request, "myapp/home.html", context)


def country_detail(request, slug):
    country = get_object_or_404(Country, slug=slug)
    scholarships = country.scholarships.filter(is_published=True).order_by('-created_at')

    paginator = Paginator(scholarships, 12)
    page_number = request.GET.get('page')
    scholarships_page = paginator.get_page(page_number)

    context = {
        "country": country,
        "scholarships": scholarships_page,
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


def submit_scholarship(request):
    if request.method == "POST":
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save()
            send_mail(
                subject=f"New scholarship submission: {submission.title}",
                message=f"Organization: {submission.organization_name}\nContact: {submission.contact_email}\nReview it in the dashboard at /dashboard/submissions/",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
            )
            return render(request, "myapp/submit_scholarship_success.html")
    else:
        form = SubmissionForm()
    return render(request, "myapp/submit_scholarship.html", {"form": form})


def request_coaching(request):
    if request.method == "POST":
        form = CoachingRequestForm(request.POST)
        if form.is_valid():
            coaching_request = form.save()
            send_mail(
                subject=f"New coaching request from {coaching_request.name}",
                message=f"Email: {coaching_request.email}\n\n{coaching_request.message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
            )
            return render(request, "myapp/request_coaching_success.html")
    else:
        form = CoachingRequestForm()
    return render(request, "myapp/request_coaching.html", {"form": form})


def newsletter_signup(request):
    if request.method == "POST":
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect('home')


@login_required
def admin_submission_list(request):
    submissions = ScholarshipSubmission.objects.filter(status="pending").order_by('-submitted_at')
    context = {"submissions": submissions}
    return render(request, "myapp/admin_submission_list.html", context)


@login_required
def admin_submission_review(request, pk):
    submission = get_object_or_404(ScholarshipSubmission, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            country, created = Country.objects.get_or_create(
                name=submission.country_name,
                defaults={"slug": submission.country_name.lower().replace(" ", "-")}
            )
            Scholarship.objects.create(
                title=submission.title,
                slug=submission.title.lower().replace(" ", "-")[:220],
                country=country,
                degree_level=submission.degree_level,
                funding_type=submission.funding_type,
                deadline=submission.deadline,
                description=submission.description,
                eligibility=submission.eligibility,
                required_documents=submission.required_documents,
                application_link=submission.application_link,
                is_published=True,
            )
            submission.status = "approved"
            submission.save()
            send_mail(
                subject="Your scholarship submission was approved",
                message=f"Hi, your submission '{submission.title}' is now live on ScholarHub.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[submission.contact_email],
            )
        elif action == "reject":
            submission.status = "rejected"
            submission.save()
            send_mail(
                subject="Your scholarship submission was not approved",
                message=f"Hi, your submission '{submission.title}' was not approved for listing on ScholarHub.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[submission.contact_email],
            )

        return redirect('admin_submission_list')

    context = {"submission": submission}
    return render(request, "myapp/admin_submission_review.html", context)


@login_required
def admin_coaching_list(request):
    coaching_requests = CoachingRequest.objects.all().order_by('-created_at')
    context = {"coaching_requests": coaching_requests}
    return render(request, "myapp/admin_coaching_list.html", context)



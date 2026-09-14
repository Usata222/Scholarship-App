import json
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
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import Scholarship, Country, ScholarshipSubmission, CoachingRequest, NewsletterSubscriber, AnalyticsEvent
from .analytics import log_event
from django.db.models import Count
from django.db.models.functions import TruncDate
from .forms import ScholarshipForm, CountryForm, SubmissionForm, CoachingRequestForm, NewsletterForm, NewsletterBroadcastForm
from django_ratelimit.decorators import ratelimit


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
def admin_scholarship_edit(request, pk): # this function is decorated with the @login_required decorator, which means that only authenticated users can access this view. If an unauthenticated user tries to access it, they will be redirected to the login page. The function retrieves a Scholarship object based on its primary key (pk) and allows the admin user to edit its details using a form. If the request method is POST, it processes the submitted form data; if valid, it saves the changes and checks if the scholarship was published. If it was not published before but is now published, it calls a function to notify subscribers of the new scholarship. Finally, it redirects to the scholarship list. If the request method is GET, it displays the form pre-filled with the scholarship's current details.
    scholarship = get_object_or_404(Scholarship, pk=pk)
    was_published = scholarship.is_published

    if request.method == "POST":
        form = ScholarshipForm(request.POST, request.FILES, instance=scholarship)
        if form.is_valid():
            scholarship = form.save()
            if not was_published and scholarship.is_published:
                notify_subscribers_of_new_scholarship(scholarship)
            return redirect('admin_scholarship_list')
    else:
        form = ScholarshipForm(instance=scholarship)

    context = {"form": form}
    return render(request, "myapp/admin_scholarship_form.html", context)


@login_required
def admin_scholarship_add(request): # this function is decorated with the @login_required decorator, which means that only authenticated users can access this view. If an unauthenticated user tries to access it, they will be redirected to the login page. The function allows the admin user to add a new scholarship using a form. If the request method is POST, it processes the submitted form data; if valid, it saves the new scholarship and checks if it is published. If published, it calls a function to notify subscribers of the new scholarship. Finally, it redirects to the scholarship list. If the request method is GET, it displays an empty form for adding a new scholarship.
    if request.method == "POST":
        form = ScholarshipForm(request.POST, request.FILES)
        if form.is_valid():
            scholarship = form.save()
            if scholarship.is_published:
                notify_subscribers_of_new_scholarship(scholarship)
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


@login_required
def admin_statistics(request):
    # Date-range selection: a few preset windows, defaulting to "last 30 days".
    range_param = request.GET.get('range', '30')
    today = timezone.now().date()

    range_days_map = {'today': 0, '7': 7, '30': 30, '90': 90}
    days = range_days_map.get(range_param, 30)
    start_date = today - timedelta(days=days)
    end_date = today

    # The previous period of equal length, used for the "up/down vs previous period" comparisons.
    period_length = (end_date - start_date).days + 1
    previous_end = start_date - timedelta(days=1)
    previous_start = previous_end - timedelta(days=period_length - 1)

    current_events = AnalyticsEvent.objects.filter(created_at__date__range=[start_date, end_date])
    previous_events = AnalyticsEvent.objects.filter(created_at__date__range=[previous_start, previous_end])

    def percent_change(current, previous):
        if previous == 0:
            return None  # no meaningful percentage when there's nothing to compare against
        return round(((current - previous) / previous) * 100, 1)

    # ---- 1. Overview metrics ----
    total_visitors = current_events.exclude(session_key="").values('session_key').distinct().count()
    previous_visitors = previous_events.exclude(session_key="").values('session_key').distinct().count()

    total_page_views = current_events.filter(event_type__in=["page_view", "scholarship_view"]).count()
    previous_page_views = previous_events.filter(event_type__in=["page_view", "scholarship_view"]).count()

    scholarship_page_views = current_events.filter(event_type="scholarship_view").count()
    application_clicks = current_events.filter(event_type="application_click").count()
    previous_clicks = previous_events.filter(event_type="application_click").count()

    ctr = round((application_clicks / scholarship_page_views) * 100, 1) if scholarship_page_views else 0

    newsletter_signups = NewsletterSubscriber.objects.filter(created_at__date__range=[start_date, end_date]).count()
    scholarship_submissions = ScholarshipSubmission.objects.filter(submitted_at__date__range=[start_date, end_date]).count()
    saves_count = current_events.filter(event_type="save").count()
    searches_count = current_events.filter(event_type="search").count()

    overview = {
        "total_visitors": total_visitors,
        "total_visitors_change": percent_change(total_visitors, previous_visitors),
        "total_page_views": total_page_views,
        "total_page_views_change": percent_change(total_page_views, previous_page_views),
        "scholarship_page_views": scholarship_page_views,
        "application_clicks": application_clicks,
        "application_clicks_change": percent_change(application_clicks, previous_clicks),
        "ctr": ctr,
        "newsletter_signups": newsletter_signups,
        "scholarship_submissions": scholarship_submissions,
        "saves_count": saves_count,
        "searches_count": searches_count,
    }

    # ---- 2. Visitor trend (for a simple line chart) ----
    daily_trend = (
        current_events.filter(event_type__in=["page_view", "scholarship_view"])
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    trend_labels = [entry["day"].strftime("%b %d") for entry in daily_trend]
    trend_values = [entry["count"] for entry in daily_trend]
    trend_labels_json = json.dumps(trend_labels)
    trend_values_json = json.dumps(trend_values)

    # ---- 3. Traffic sources ----
    # Groups by utm_source when present; otherwise falls back to the referrer's
    # domain so "google.com/search..." becomes just "google.com". Blank/unset
    # is bucketed as Direct/Unknown -- this is genuinely common (TikTok/Instagram's
    # in-app browsers often strip the referrer header entirely).
    source_counts = {}
    for event in current_events.exclude(event_type="save").only("utm_source", "referrer"):
        if event.utm_source:
            source = event.utm_source
        elif event.referrer:
            source = event.referrer.split("/")[2] if "//" in event.referrer else event.referrer
        else:
            source = "Direct / Unknown"
        source_counts[source] = source_counts.get(source, 0) + 1
    traffic_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:6]

    # ---- 5 & 6. Most viewed / most clicked scholarships ----
    most_viewed = (
        current_events.filter(event_type="scholarship_view")
        .values("scholarship__id", "scholarship__title")
        .annotate(views=Count("id"))
        .order_by("-views")[:10]
    )
    clicks_by_scholarship = dict(
        current_events.filter(event_type="application_click")
        .values("scholarship__id")
        .annotate(clicks=Count("id"))
        .values_list("scholarship__id", "clicks")
    )
    most_viewed_table = []
    for row in most_viewed:
        clicks = clicks_by_scholarship.get(row["scholarship__id"], 0)
        views = row["views"]
        most_viewed_table.append({
            "title": row["scholarship__title"],
            "views": views,
            "clicks": clicks,
            "ctr": round((clicks / views) * 100, 1) if views else 0,
        })

    most_clicked = (
        current_events.filter(event_type="application_click")
        .values("scholarship__id", "scholarship__title")
        .annotate(clicks=Count("id"))
        .order_by("-clicks")[:10]
    )
    views_by_scholarship = dict(
        current_events.filter(event_type="scholarship_view")
        .values("scholarship__id")
        .annotate(views=Count("id"))
        .values_list("scholarship__id", "views")
    )
    most_clicked_table = []
    for row in most_clicked:
        clicks = row["clicks"]
        views = views_by_scholarship.get(row["scholarship__id"], 0)
        most_clicked_table.append({
            "title": row["scholarship__title"],
            "views": views,
            "clicks": clicks,
            "ctr": round((clicks / views) * 100, 1) if views else 0,
        })

    # ---- 7. Popular categories & 8. Popular study destinations ----
    popular_degree_levels_raw = (
        current_events.filter(event_type="scholarship_view")
        .values("scholarship__degree_level")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    degree_level_labels = dict(Scholarship.DEGREE_LEVEL_CHOICES)
    popular_degree_levels = [
        {"label": degree_level_labels.get(row["scholarship__degree_level"], row["scholarship__degree_level"]), "count": row["count"]}
        for row in popular_degree_levels_raw if row["scholarship__degree_level"]
    ]

    popular_funding_types_raw = (
        current_events.filter(event_type="scholarship_view")
        .values("scholarship__funding_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    funding_type_labels = dict(Scholarship.FUNDING_TYPE_CHOICES)
    popular_funding_types = [
        {"label": funding_type_labels.get(row["scholarship__funding_type"], row["scholarship__funding_type"]), "count": row["count"]}
        for row in popular_funding_types_raw if row["scholarship__funding_type"]
    ]
    popular_destinations = (
        current_events.filter(event_type="scholarship_view")
        .values("scholarship__country__name")
        .annotate(count=Count("id"))
        .order_by("-count")[:8]
    )

    # ---- 9. Search analytics ----
    top_searches = (
        current_events.filter(event_type="search")
        .values("search_summary")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    zero_result_searches = (
        current_events.filter(event_type="search", result_count=0)
        .values("search_summary")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    context = {
        "range_param": range_param,
        "start_date": start_date,
        "end_date": end_date,
        "overview": overview,
        "trend_labels": trend_labels,
        "trend_labels_json": trend_labels_json,
        "trend_values_json": trend_values_json,
        "trend_values": trend_values,
        "traffic_sources": traffic_sources,
        "most_viewed_table": most_viewed_table,
        "most_clicked_table": most_clicked_table,
        "popular_degree_levels": popular_degree_levels,
        "popular_funding_types": popular_funding_types,
        "popular_destinations": popular_destinations,
        "top_searches": top_searches,
        "zero_result_searches": zero_result_searches,
    }
    return render(request, "myapp/admin_statistics.html", context)



@ratelimit(key='ip', rate='5/m', block=True) # this decorator is used to limit the rate of requests to the decorated view function. In this case, it limits the number of requests from a single IP address to 5 requests per minute. If the limit is exceeded, the request will be blocked, and the user will receive a response indicating that they have exceeded the allowed rate. This is useful for preventing abuse or excessive traffic to certain views, such as login pages or forms.
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
    log_event(request, "scholarship_view", scholarship=scholarship)  # analytics: records this view for the Statistics page
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

    # analytics: every homepage load counts as a page view
    log_event(request, "page_view", page_path=request.path)

    # analytics: if any filter was actually used, log it as a "search" event.
    # This is what powers the "most searched" and "zero-result searches" sections.
    filters_used = []
    if country_slug:
        filters_used.append(f"country={country_slug}")
    if degree_level:
        filters_used.append(f"level={degree_level}")
    if funding_type:
        filters_used.append(f"funding={funding_type}")
    if filters_used:
        log_event(
            request, "search",
            search_summary=", ".join(filters_used),
            result_count=paginator.count,
        )

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

    log_event(request, "page_view", page_path=request.path)  # analytics: counts as a page view

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
    log_event(request, "application_click", scholarship=scholarship)  # analytics: records the click for CTR
    return redirect(scholarship.application_link)


def toggle_save(request, slug): # this function is used to toggle the saved status of a scholarship for the current user session. It checks if the scholarship is already saved in the session, and if so, it removes it; otherwise, it adds it to the saved list. The updated list of saved scholarships is then stored back in the session, and the user is redirected to the scholarship detail page.
    scholarship = get_object_or_404(Scholarship, slug=slug, is_published=True) # this line retrieves the scholarship object from the database based on the provided slug and ensures that it is published. If the scholarship does not exist or is not published, a 404 error is raised.
    saved = request.session.get('saved_scholarships', []) # this line retrieves the list of saved scholarships from the user's session. If the 'saved_scholarships' key does not exist in the session, it initializes an empty list. This allows the application to keep track of which scholarships the user has saved during their session.

    if scholarship.pk in saved:
        saved.remove(scholarship.pk) # this line checks if the primary key (pk) of the scholarship is already in the saved list. If it is, it removes the pk from the list, effectively "unsaving" the scholarship for the user.
    else:
        saved.append(scholarship.pk) # if the scholarship's pk is not in the saved list, this line adds it to the list, effectively "saving" the scholarship for the user.
        log_event(request, "save", scholarship=scholarship)  # analytics: only log on save, not unsave

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
                message=f"Hi, your submission '{submission.title}' is now live on Scholarra.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[submission.contact_email],
            )
        elif action == "reject":
            submission.status = "rejected"
            submission.save()
            send_mail(
                subject="Your scholarship submission was not approved",
                message=f"Hi, your submission '{submission.title}' was not approved for listing on Scholarra.",
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


@login_required
def admin_send_newsletter(request):
    # Lets the admin write a one-off newsletter message and blast it to every
    # subscriber immediately, using the same styled HTML email layout as the
    # automatic "new scholarship" notification.
    sent_count = None

    if request.method == "POST":
        form = NewsletterBroadcastForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]
            subscribers = NewsletterSubscriber.objects.all()

            for subscriber in subscribers:
                unsubscribe_link = request_build_unsubscribe_link(subscriber)

                html_body = render_to_string("myapp/emails/newsletter_broadcast.html", {
                    "subject": subject,
                    "message": message,
                    "site_url": settings.SITE_URL,
                    "unsubscribe_link": unsubscribe_link,
                })

                email = EmailMultiAlternatives(
                    subject=subject,
                    body=f"{message}\n\nUnsubscribe: {unsubscribe_link}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[subscriber.email],
                )
                email.attach_alternative(html_body, "text/html")
                email.send()

            sent_count = subscribers.count()
            form = NewsletterBroadcastForm()
    else:
        form = NewsletterBroadcastForm()

    context = {"form": form, "sent_count": sent_count}
    return render(request, "myapp/admin_send_newsletter.html", context)


def notify_subscribers_of_new_scholarship(scholarship):
    # Sends a styled HTML email (myapp/emails/new_scholarship.html) to every subscriber,
    # with a plain-text version attached as a fallback for email clients that don't render HTML.
    subscribers = NewsletterSubscriber.objects.all()
    scholarship_link = f"{settings.SITE_URL}/scholarship/{scholarship.slug}/"

    for subscriber in subscribers:
        unsubscribe_link = request_build_unsubscribe_link(subscriber)

        plain_text_body = (
            f"{scholarship.title} — {scholarship.country.name}\n"
            f"Deadline: {scholarship.deadline}\n\n"
            f"View it: {scholarship_link}\n\n"
            f"Unsubscribe: {unsubscribe_link}"
        )

        html_body = render_to_string("myapp/emails/new_scholarship.html", {
            "scholarship": scholarship,
            "scholarship_link": scholarship_link,
            "unsubscribe_link": unsubscribe_link,
        })

        email = EmailMultiAlternatives(
            subject=f"New Scholarship: {scholarship.title}",
            body=plain_text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[subscriber.email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send()






from django.http import HttpResponse

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /dashboard/",
        "Sitemap: " + settings.SITE_URL + "/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")












############################################################






def request_build_unsubscribe_link(subscriber):
    return f"{settings.SITE_URL}/newsletter/unsubscribe/{subscriber.unsubscribe_token}/"

def newsletter_unsubscribe(request, token):
    subscriber = get_object_or_404(NewsletterSubscriber, unsubscribe_token=token)
    subscriber.delete()
    return render(request, "myapp/newsletter_unsubscribe_success.html")

def privacy_policy(request):
    return render(request, "myapp/privacy_policy.html")


def terms_of_use(request):
    return render(request, "myapp/terms_of_use.html")

from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Scholarship, NewsletterSubscriber


REMINDER_WINDOW_DAYS = 3  # send the reminder once a scholarship's deadline is this many days away or closer


def send_deadline_reminders():
    """
    Finds every published scholarship whose deadline is within REMINDER_WINDOW_DAYS
    (and hasn't already had a reminder sent), emails every newsletter subscriber
    about it, then marks it as sent so it never goes out twice.

    Returns a short summary string, so both the cron-triggered view and the
    management command can report what happened.
    """
    from .views import request_build_unsubscribe_link  # local import avoids a circular import at module load time

    today = timezone.now().date()
    cutoff = today + timedelta(days=REMINDER_WINDOW_DAYS)

    closing_soon = Scholarship.objects.filter(
        is_published=True,
        deadline_reminder_sent=False,
        deadline__gte=today,
        deadline__lte=cutoff,
    )
    candidate_count = closing_soon.count()  # captured now -- the queryset would shrink after we start marking scholarships as sent below

    subscribers = list(NewsletterSubscriber.objects.all())
    scholarships_notified = 0

    for scholarship in closing_soon:
        if not subscribers:
            break  # nothing to send, but still mark as sent below so we don't keep checking it forever once subscribers exist again -- actually: skip marking if no subscribers, see note below
        days_left = (scholarship.deadline - today).days
        scholarship_link = f"{settings.SITE_URL}/scholarship/{scholarship.slug}/"

        for subscriber in subscribers:
            unsubscribe_link = request_build_unsubscribe_link(subscriber)
            html_body = render_to_string("myapp/emails/deadline_reminder.html", {
                "scholarship": scholarship,
                "days_left": days_left,
                "scholarship_link": scholarship_link,
                "unsubscribe_link": unsubscribe_link,
            })
            plain_text_body = (
                f"{scholarship.title} closes in {days_left} day(s) -- {scholarship.deadline}\n"
                f"View it: {scholarship_link}\n\nUnsubscribe: {unsubscribe_link}"
            )
            email = EmailMultiAlternatives(
                subject=f"Closing Soon: {scholarship.title}",
                body=plain_text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[subscriber.email],
            )
            email.attach_alternative(html_body, "text/html")
            email.send()

        scholarship.deadline_reminder_sent = True
        scholarship.save(update_fields=["deadline_reminder_sent"])
        scholarships_notified += 1

    return f"Checked {candidate_count} candidate(s); sent reminders for {scholarships_notified} scholarship(s) to {len(subscribers)} subscriber(s)."

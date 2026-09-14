from .models import AnalyticsEvent


def log_event(request, event_type, scholarship=None, page_path="", search_summary="", result_count=None):
    """
    Records one AnalyticsEvent row. Called from views right where the tracked
    action happens (a page load, a scholarship view, a click, a filter/search).

    Uses the visitor's session key (not their IP address) as a stand-in for
    "one visitor" -- it's an opaque token Django already manages for sessions,
    so we can count distinct visitors without permanently storing anything
    that identifies a real person.
    """
    if not request.session.session_key:
        # A brand-new visitor with no session yet -- force Django to create
        # one now so we have something to count them by.
        request.session.save()

    AnalyticsEvent.objects.create(
        event_type=event_type,
        scholarship=scholarship,
        page_path=page_path[:255],
        search_summary=search_summary[:255],
        result_count=result_count,
        utm_source=request.GET.get("utm_source", "")[:100],
        referrer=request.META.get("HTTP_REFERER", "")[:300],
        session_key=request.session.session_key or "",
    )

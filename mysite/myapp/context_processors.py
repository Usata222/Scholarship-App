from django.conf import settings


def site_contact(request):
    """
    Makes the real contact email available to every template automatically,
    pulled from settings.ADMIN_EMAIL (which itself comes from .env).
    No view needs to pass this manually.
    """
    return {
        "site_contact_email": settings.ADMIN_EMAIL,
    }

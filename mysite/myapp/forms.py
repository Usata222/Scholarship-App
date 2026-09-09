from django import forms
from .models import Scholarship, Country, ScholarshipSubmission, CoachingRequest, NewsletterSubscriber

class ScholarshipForm(forms.ModelForm):
    class Meta:
        model = Scholarship
        fields = [
            "title", "slug", "country", "degree_level", "funding_type",
            "deadline", "description", "eligibility", "required_documents",
            "application_link", "image", "is_published", "is_featured",
        ]
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }


class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = ["name", "slug"]


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = ScholarshipSubmission
        fields = [
            "organization_name", "contact_email", "title", "country_name",
            "degree_level", "funding_type", "deadline", "description",
            "eligibility", "required_documents", "application_link",
        ]
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }


class CoachingRequestForm(forms.ModelForm):
    class Meta:
        model = CoachingRequest
        fields = ["name", "email", "message"]


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ["email"]
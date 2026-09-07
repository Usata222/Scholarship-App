from django import forms
from .models import Scholarship
from .models import Scholarship, Country

class ScholarshipForm(forms.ModelForm): # creating a form for the Scholarship model using Django's ModelForm, which automatically generates form fields based on the model's fields
    class Meta: # this inner class is used to specify the model and fields that the form will use, as well as any additional configurations such as widgets for customizing the form's appearance and behavior
        model = Scholarship
        fields = [
            "title", "slug", "country", "degree_level", "funding_type",
            "deadline", "description", "eligibility", "required_documents",
            "application_link", "is_published", "is_featured",
        ]
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }

class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = ["name", "slug"]
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from myapp.models import Country, Scholarship


DEMO_SCHOLARSHIPS = [
    {
        "country": "Germany",
        "title": "DAAD Master's Scholarship for Development-Related Studies",
        "degree_level": "masters",
        "funding_type": "full",
        "days_until_deadline": 45,
        "description": "The DAAD offers fully funded scholarships for students from developing countries pursuing a postgraduate degree in a development-related field at a German university.",
        "eligibility": "Applicants must hold a bachelor's degree with above-average grades and at least two years of relevant professional experience.",
        "required_documents": "CV, motivation letter, two reference letters, university transcripts, proof of English or German proficiency.",
        "application_link": "https://www.daad.de/en/",
        "is_featured": True,
    },
    {
        "country": "United Kingdom",
        "title": "Chevening Scholarship",
        "degree_level": "masters",
        "funding_type": "full",
        "days_until_deadline": 10,
        "description": "Chevening is the UK government's global scholarship programme, funding one-year master's degrees at any UK university for future leaders and influencers.",
        "eligibility": "Applicants must have at least two years of work experience and an unconditional offer from a UK university.",
        "required_documents": "Essays, two references, proof of English proficiency, degree certificate.",
        "application_link": "https://www.chevening.org/",
        "is_featured": True,
    },
    {
        "country": "Canada",
        "title": "Vanier Canada Graduate Scholarship",
        "degree_level": "phd",
        "funding_type": "full",
        "days_until_deadline": 90,
        "description": "The Vanier CGS is awarded to doctoral students demonstrating leadership skills and a high standard of scholarly achievement in the social sciences, humanities, natural sciences, engineering, or health.",
        "eligibility": "Open to Canadian and international students nominated by a Canadian institution.",
        "required_documents": "Research proposal, transcripts, three reference letters, leadership statement.",
        "application_link": "https://vanier.gc.ca/",
        "is_featured": False,
    },
    {
        "country": "Netherlands",
        "title": "Holland Scholarship",
        "degree_level": "undergraduate",
        "funding_type": "partial",
        "days_until_deadline": 30,
        "description": "A partial scholarship for non-EEA students starting a bachelor's or master's programme at a participating Dutch university.",
        "eligibility": "Applicants must not currently be enrolled in Dutch higher education and must not hold a Dutch degree.",
        "required_documents": "Motivation letter, transcripts, proof of admission.",
        "application_link": "https://www.studyinholland.nl/finances/holland-scholarship",
        "is_featured": False,
    },
    {
        "country": "United States",
        "title": "Fulbright Foreign Student Program",
        "degree_level": "masters",
        "funding_type": "full",
        "days_until_deadline": 7,
        "description": "The Fulbright program provides funding for graduate students, young professionals, and artists from abroad to study in the United States.",
        "eligibility": "Applicants must hold a bachelor's degree and demonstrate strong academic and leadership potential.",
        "required_documents": "Study objective statement, personal statement, transcripts, three reference letters, standardized test scores.",
        "application_link": "https://foreign.fulbrightonline.org/",
        "is_featured": True,
    },
    {
        "country": "Australia",
        "title": "Australia Awards Scholarship",
        "degree_level": "masters",
        "funding_type": "full",
        "days_until_deadline": 60,
        "description": "Long-term development awards for full-time undergraduate or postgraduate study at participating Australian universities.",
        "eligibility": "Open to citizens of eligible countries who meet academic and English language entry requirements.",
        "required_documents": "Application form, academic transcripts, proof of citizenship, English proficiency results.",
        "application_link": "https://www.dfat.gov.au/people-to-people/australia-awards",
        "is_featured": False,
    },
    {
        "country": "Japan",
        "title": "MEXT Scholarship (Japanese Government)",
        "degree_level": "phd",
        "funding_type": "full",
        "days_until_deadline": 120,
        "description": "The Japanese government offers fully funded scholarships covering tuition, a monthly stipend, and airfare for research students at Japanese universities.",
        "eligibility": "Applicants must be under 35 and hold a relevant bachelor's or master's degree.",
        "required_documents": "Application form, research plan, transcripts, recommendation letter, health certificate.",
        "application_link": "https://www.studyinjapan.go.jp/en/",
        "is_featured": False,
    },
]


class Command(BaseCommand):
    help = "Seeds the database with realistic demo scholarships and countries for testing/demo purposes."

    def handle(self, *args, **options):
        today = timezone.now().date()
        created_countries = 0
        created_scholarships = 0

        for entry in DEMO_SCHOLARSHIPS:
            country_name = entry["country"]
            country_slug = country_name.lower().replace(" ", "-")
            country, was_created = Country.objects.get_or_create(
                name=country_name,
                defaults={"slug": country_slug},
            )
            if was_created:
                created_countries += 1

            scholarship_slug = entry["title"].lower().replace(" ", "-").replace("'", "").replace("(", "").replace(")", "")[:220]

            if Scholarship.objects.filter(slug=scholarship_slug).exists():
                continue

            Scholarship.objects.create(
                title=entry["title"],
                slug=scholarship_slug,
                country=country,
                degree_level=entry["degree_level"],
                funding_type=entry["funding_type"],
                deadline=today + datetime.timedelta(days=entry["days_until_deadline"]),
                description=entry["description"],
                eligibility=entry["eligibility"],
                required_documents=entry["required_documents"],
                application_link=entry["application_link"],
                is_published=True,
                is_featured=entry["is_featured"],
            )
            created_scholarships += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {created_countries} new countries and {created_scholarships} new scholarships."
        ))

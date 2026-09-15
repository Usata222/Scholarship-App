from django.core.management.base import BaseCommand
from myapp.reminders import send_deadline_reminders


class Command(BaseCommand):
    help = "Checks for scholarships closing within 3 days and emails newsletter subscribers about them (won't re-send for the same scholarship twice)."

    def handle(self, *args, **options):
        summary = send_deadline_reminders()
        self.stdout.write(self.style.SUCCESS(summary))

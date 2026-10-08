from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from api.models import Company


class Command(BaseCommand):
    help = "Promote a user's Company profile to the TeamBoard admin role."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)

    def handle(self, *args, **options):
        username = options["username"]
        try:
            user = User.objects.get(username=username)
            company = user.company
        except (User.DoesNotExist, Company.DoesNotExist) as exc:
            raise CommandError(f"No company profile found for username '{username}'.") from exc

        company.role = Company.Role.ADMIN
        company.save(update_fields=["role"])
        self.stdout.write(self.style.SUCCESS(f"{username} is now an admin.") )

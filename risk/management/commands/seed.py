"""
Idempotent seed: regions of Uzbekistan + optional superuser.

Safe to run on every deploy (it is part of the Render build command).
Superuser is created from env vars if they are set:
    DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Profile
from risk.hazards import REGIONS
from risk.models import Region


class Command(BaseCommand):
    help = "Seed SPACE RISK reference data (regions, admin user)."

    def handle(self, *args, **options):
        created = updated = 0
        for data in REGIONS:
            _, was_created = Region.objects.update_or_create(slug=data["slug"], defaults={k: v for k, v in data.items() if k != "slug"})
            created += was_created
            updated += not was_created
        self.stdout.write(self.style.SUCCESS(f"Regions: {created} created, {updated} updated"))

        User = get_user_model()
        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "")
        if username and password:
            user, was_created = User.objects.get_or_create(username=username, defaults={"email": email})
            if was_created:
                user.set_password(password)
                user.is_staff = user.is_superuser = True
                user.first_name = "Admin"
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created"))
            else:
                self.stdout.write(f"Superuser '{username}' already exists")
        else:
            self.stdout.write("DJANGO_SUPERUSER_USERNAME/PASSWORD not set — skipping superuser")

        for user in User.objects.filter(profile__isnull=True):
            Profile.objects.create(user=user)

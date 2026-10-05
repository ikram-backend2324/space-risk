from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    organization = models.CharField("Tashkilot", max_length=160, blank=True)
    position = models.CharField("Lavozim", max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profillar"

    def __str__(self):
        return f"{self.user.get_username()} profili"

    @property
    def initials(self):
        name = self.user.get_full_name() or self.user.get_username()
        parts = name.split()
        return "".join(p[0] for p in parts[:2]).upper()

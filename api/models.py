import secrets

from django.conf import settings
from django.db import models


def _new_key():
    return secrets.token_hex(20)


class ApiToken(models.Model):
    """Bearer token for the Android app (one per signed-in device)."""

    key = models.CharField(max_length=40, unique=True, default=_new_key, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_tokens")
    device = models.CharField("Qurilma", max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "API token"
        verbose_name_plural = "API tokenlar"

    def __str__(self):
        return f"{self.user} · {self.device or 'device'}"

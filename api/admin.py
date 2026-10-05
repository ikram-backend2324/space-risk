from django.contrib import admin

from .models import ApiToken


@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "device", "created_at", "last_used_at")
    search_fields = ("user__username", "device")
    readonly_fields = ("key", "created_at", "last_used_at")

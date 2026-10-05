from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Profile

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    verbose_name_plural = "Profil"


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]

    def get_inlines(self, request, obj):
        # On "add user" the post_save signal creates the profile; an inline there would duplicate it.
        return [ProfileInline] if obj else []

    list_display = ("username", "email", "first_name", "last_name", "organization", "prediction_count", "is_staff", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active", "date_joined")

    @admin.display(description="Tashkilot")
    def organization(self, obj):
        return getattr(getattr(obj, "profile", None), "organization", "") or "—"

    @admin.display(description="Prognozlar")
    def prediction_count(self, obj):
        return obj.predictions.count()


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "position", "created_at")
    search_fields = ("user__username", "user__email", "organization")

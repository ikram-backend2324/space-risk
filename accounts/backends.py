from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class UsernameOrEmailBackend(ModelBackend):
    """Lets users sign in with either their username or their email (case-insensitive)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        User = get_user_model()
        field = "email__iexact" if "@" in username else "username__iexact"
        user = User.objects.filter(**{field: username.strip()}).order_by("id").first()
        if user is None:
            User().set_password(password)  # equalise timing with a real check
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

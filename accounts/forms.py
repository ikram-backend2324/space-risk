from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from risk.i18n import t

from .models import Profile

User = get_user_model()

# Django error code → UI key. Field-specific overrides take precedence.
ERROR_KEYS = {
    "required": "err.required",
    "password_mismatch": "err.password_mismatch",
    "password_too_short": "err.password_too_short",
    "password_too_common": "err.password_too_common",
    "password_entirely_numeric": "err.password_entirely_numeric",
    "password_too_similar": "err.password_too_similar",
    "invalid_login": "err.invalid_login",
    "inactive": "err.inactive",
    "max_length": "err.max_length",
    "email_taken": "err.email_taken",
}
FIELD_ERROR_KEYS = {
    ("email", "invalid"): "err.invalid_email",
    ("username", "invalid"): "err.username_invalid",
    ("username", "unique"): "err.username_taken",
}


class LocalizedMixin:
    """Translates labels/placeholders and replaces Django's error messages by error code."""

    labels = {}
    placeholders = {}

    def _localize_fields(self):
        for name, field in self.fields.items():
            if name in self.labels:
                field.label = t(self.labels[name])
            field.help_text = ""
            field.widget.attrs.setdefault("class", "input")
            ph = self.placeholders.get(name, self.labels.get(name))
            if ph:
                field.widget.attrs["placeholder"] = t(ph)

    def full_clean(self):
        super().full_clean()
        if not self._errors:
            return
        for name in list(self._errors):
            localized = []
            for err in self._errors[name].as_data():
                key = FIELD_ERROR_KEYS.get((name, err.code)) or ERROR_KEYS.get(err.code)
                params = err.params if isinstance(err.params, dict) else {}
                localized.append(t(key, **params) if key else t("err.generic"))
            self._errors[name] = self.error_class(localized, renderer=self.renderer)


class LoginForm(LocalizedMixin, AuthenticationForm):
    labels = {"username": "field.username", "password": "field.password"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._localize_fields()


class RegisterForm(LocalizedMixin, UserCreationForm):
    first_name = forms.CharField(max_length=60)
    last_name = forms.CharField(max_length=60, required=False)
    email = forms.EmailField()
    organization = forms.CharField(max_length=160, required=False)

    labels = {
        "first_name": "field.first_name",
        "last_name": "field.last_name",
        "username": "field.username",
        "email": "field.email",
        "organization": "field.organization",
        "password1": "field.password",
        "password2": "field.password_confirm",
    }
    placeholders = {
        "email": "field.email_ph",
        "organization": "field.organization_ph",
        "password1": "field.password_ph",
        "password2": "field.password_repeat_ph",
    }

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._localize_fields()
        self.fields["password1"].widget.attrs["data-pw-meter"] = "#pw-meter"

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("email taken", code="email_taken")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
            Profile.objects.update_or_create(
                user=user, defaults={"organization": self.cleaned_data.get("organization", "")}
            )
        return user


class ProfileForm(LocalizedMixin, forms.ModelForm):
    first_name = forms.CharField(max_length=60)
    last_name = forms.CharField(max_length=60, required=False)
    email = forms.EmailField()

    labels = {
        "first_name": "field.first_name",
        "last_name": "field.last_name",
        "email": "field.email",
        "organization": "field.organization",
        "position": "field.position",
    }

    class Meta:
        model = Profile
        fields = ("organization", "position")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email
        self.order_fields(["first_name", "last_name", "email", "organization", "position"])
        self._localize_fields()

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data.get("last_name", "")
        self.user.email = self.cleaned_data["email"]
        if commit:
            self.user.save()
            profile.save()
        return profile

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Profile

User = get_user_model()


class StyledMixin:
    """Adds the site's input class and placeholders to every field."""

    placeholders = {}

    def _style(self):
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "input")
            field.widget.attrs.setdefault("placeholder", self.placeholders.get(name, field.label or ""))


class LoginForm(StyledMixin, AuthenticationForm):
    placeholders = {"username": "Foydalanuvchi nomi", "password": "Parol"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Foydalanuvchi nomi"
        self.fields["password"].label = "Parol"
        self._style()


class RegisterForm(StyledMixin, UserCreationForm):
    first_name = forms.CharField(label="Ism", max_length=60)
    last_name = forms.CharField(label="Familiya", max_length=60, required=False)
    email = forms.EmailField(label="Email")
    organization = forms.CharField(label="Tashkilot", max_length=160, required=False)

    placeholders = {
        "first_name": "Ism",
        "last_name": "Familiya",
        "username": "Foydalanuvchi nomi",
        "email": "email@misol.uz",
        "organization": "Tashkilot (ixtiyoriy)",
        "password1": "Parol (kamida 8 belgi)",
        "password2": "Parolni takrorlang",
    }

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Foydalanuvchi nomi"
        self.fields["username"].help_text = ""
        self.fields["password1"].label = "Parol"
        self.fields["password1"].help_text = ""
        self.fields["password2"].label = "Parolni tasdiqlang"
        self.fields["password2"].help_text = ""
        self.fields["password1"].widget.attrs["data-pw-meter"] = "#pw-meter"
        self._style()

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Bu email bilan allaqachon ro'yxatdan o'tilgan.")
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


class ProfileForm(StyledMixin, forms.ModelForm):
    first_name = forms.CharField(label="Ism", max_length=60)
    last_name = forms.CharField(label="Familiya", max_length=60, required=False)
    email = forms.EmailField(label="Email")

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
        self._style()

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data.get("last_name", "")
        self.user.email = self.cleaned_data["email"]
        if commit:
            self.user.save()
            profile.save()
        return profile

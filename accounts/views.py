from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from risk.i18n import t

from .forms import LoginForm, ProfileForm, RegisterForm
from .models import Profile


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, t("msg.welcome", name=form.get_user().first_name or form.get_user().username))
        return super().form_valid(form)


class LogoutView(auth_views.LogoutView):
    pass


def register(request):
    if request.user.is_authenticated:
        return redirect("risk:dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, t("msg.registered"))
        return redirect("risk:dashboard")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    prof, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=prof, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, t("msg.profile_saved"))
        return redirect("accounts:profile")
    stats = {
        "total": request.user.predictions.count(),
        "critical": request.user.predictions.filter(level__in=["high", "critical"]).count(),
    }
    return render(request, "accounts/profile.html", {"form": form, "profile": prof, "stats": stats})

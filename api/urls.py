from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("meta/", views.meta, name="meta"),
    path("auth/register/", views.register, name="register"),
    path("auth/login/", views.login, name="login"),
    path("auth/logout/", views.logout, name="logout"),
    path("me/", views.me, name="me"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("forecasts/", views.forecasts, name="forecasts"),
    path("forecasts/<int:pk>/", views.forecast, name="forecast"),
    path("forecasts/<int:pk>/ask/", views.ask, name="ask"),
    path("scenario/", views.public_scenario, name="scenario"),
]

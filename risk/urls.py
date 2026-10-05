from django.urls import path

from . import views

app_name = "risk"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("lang/<str:code>/", views.set_language, name="set_language"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("predict/", views.predict, name="predict"),
    path("predictions/", views.history, name="history"),
    path("predictions/<int:pk>/", views.detail, name="detail"),
    path("predictions/<int:pk>/delete/", views.delete, name="delete"),
    path("predictions/<int:pk>/ask/", views.ask, name="ask"),
    path("api/regions/", views.regions_api, name="regions_api"),
]

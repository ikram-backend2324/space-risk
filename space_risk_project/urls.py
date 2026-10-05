from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "SPACE RISK"
admin.site.site_title = "SPACE RISK Admin"
admin.site.index_title = "Boshqaruv paneli"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("risk.urls")),
]

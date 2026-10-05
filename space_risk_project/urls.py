from django.contrib import admin
from django.templatetags.static import static
from django.urls import include, path
from django.views.generic import RedirectView

admin.site.site_header = "SPACE RISK"
admin.site.site_title = "SPACE RISK Admin"
admin.site.index_title = "Boshqaruv paneli"

urlpatterns = [
    # Resolved per request (not at import): the static manifest doesn't exist yet during `migrate` on Render.
    path("favicon.ico", lambda request: RedirectView.as_view(url=static("img/icons/favicon.ico"))(request)),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("risk.urls")),
]

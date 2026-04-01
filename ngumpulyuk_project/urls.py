from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/api/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/auth/", include("ngumpulyuk_app.authentication.urls")),
    path("api/v1/auth/", include("ngumpulyuk_app.social_accounts.urls")),
    path("api/v1/", include("ngumpulyuk_app.users.urls")),
    path("api/v1/", include("ngumpulyuk_app.events.urls")),
    path("api/v1/", include("ngumpulyuk_app.communities.urls")),
    path("api/v1/", include("ngumpulyuk_app.discussions.urls")),
    path("api/v1/", include("ngumpulyuk_app.notifications.urls")),
    path("api/v1/", include("ngumpulyuk_app.recommendations.urls")),
]

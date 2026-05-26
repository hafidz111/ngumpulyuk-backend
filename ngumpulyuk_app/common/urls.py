from django.urls import path

from ngumpulyuk_app.common.landing import LandingPublicView
from ngumpulyuk_app.common.views import IndonesiaLocationListView, PublicPingView

urlpatterns = [
    path("public/ping/", PublicPingView.as_view(), name="public-ping"),
    path("public/landing/", LandingPublicView.as_view(), name="public-landing"),
    path("locations/", IndonesiaLocationListView.as_view(), name="locations-list"),
]

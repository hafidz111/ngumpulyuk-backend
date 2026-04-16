from django.urls import path

from ngumpulyuk_app.recommendations import views

urlpatterns = [
    path("recommendations/events/", views.RecommendationsEventsView.as_view(), name="recommendations-events"),
    path("recommendations/refresh/", views.RecommendationsRefreshView.as_view(), name="recommendations-refresh"),
    path("recommendations/signals/", views.RecommendationSignalView.as_view(), name="recommendations-signals"),
]

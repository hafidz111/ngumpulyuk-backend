from django.urls import path

from ngumpulyuk_app.users import views

urlpatterns = [
    path("users/me/", views.MeView.as_view(), name="users-me"),
    path(
        "users/me/participation-summary/",
        views.ParticipationSummaryView.as_view(),
        name="users-participation-summary",
    ),
    path("users/me/joined-events/ids", views.JoinedEventIdsView.as_view(), name="users-joined-event-ids"),
    path("users/me/activity-history/", views.ActivityHistoryView.as_view(), name="users-activity"),
    path("users/onboarding/", views.OnboardingView.as_view(), name="users-onboarding"),
    path("users/<str:username>/", views.UserByUsernameView.as_view(), name="users-by-username"),
]

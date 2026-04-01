from django.urls import path

from ngumpulyuk_app.events import views

urlpatterns = [
    path("events/", views.EventListCreateView.as_view(), name="events-list"),
    path("events/<uuid:id>/", views.EventDetailView.as_view(), name="events-detail"),
    path("events/<uuid:id>/join/", views.EventJoinView.as_view(), name="events-join"),
    path("events/<uuid:id>/leave/", views.EventLeaveView.as_view(), name="events-leave"),
    path("events/<uuid:id>/participants/", views.EventParticipantsView.as_view(), name="events-participants"),
]

from django.urls import path

from ngumpulyuk_app.notifications import views

urlpatterns = [
    path("notifications/", views.NotificationsView.as_view(), name="notifications"),
    path("notifications/read-all/", views.NotificationsReadAllView.as_view(), name="notifications-read-all"),
    path("notifications/<uuid:id>/read/", views.NotificationReadView.as_view(), name="notification-read"),
]

from django.urls import path

from ngumpulyuk_app.discussions import views

urlpatterns = [
    path("threads/", views.ThreadCreateView.as_view(), name="thread-create"),
    path("threads/feed/", views.ThreadFeedView.as_view(), name="thread-feed"),
    path("threads/<uuid:id>/", views.ThreadDetailView.as_view(), name="thread-detail"),
    path("threads/<uuid:id>/comments/", views.ThreadCommentsView.as_view(), name="thread-comments"),
    path("threads/<uuid:id>/like/", views.ThreadLikeView.as_view(), name="thread-like"),
    path("comments/<uuid:id>/like/", views.CommentLikeView.as_view(), name="comment-like"),
]

from django.urls import path

from ngumpulyuk_app.discussions import views

urlpatterns = [
    path("threads/<uuid:id>/comments/", views.ThreadCommentsView.as_view(), name="thread-comments"),
    path("threads/<uuid:id>/like/", views.ThreadLikeView.as_view(), name="thread-like"),
    path("comments/<uuid:id>/like/", views.CommentLikeView.as_view(), name="comment-like"),
]

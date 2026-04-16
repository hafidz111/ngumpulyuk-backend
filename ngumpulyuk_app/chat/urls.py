from django.urls import path

from ngumpulyuk_app.chat import views

urlpatterns = [
    path("chat/", views.ChatMessageView.as_view(), name="chat-message"),
    path("chat/feedback/", views.ChatFeedbackView.as_view(), name="chat-feedback"),
    path("admin/chat/logs/", views.AdminChatLogsView.as_view(), name="admin-chat-logs"),
    path("admin/chat/templates/", views.AdminChatTemplatesView.as_view(), name="admin-chat-templates"),
    path("admin/chat/corrections/", views.AdminChatCorrectionsView.as_view(), name="admin-chat-corrections"),
    path(
        "admin/chat/corrections/<uuid:correction_id>/",
        views.AdminChatCorrectionDetailView.as_view(),
        name="admin-chat-corrections-detail",
    ),
]

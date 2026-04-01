from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from ngumpulyuk_app.common.api_response import err, ok
from ngumpulyuk_app.common.presenters import clamp_limit, clamp_offset, pagination_meta
from ngumpulyuk_app.notifications.models import Notification

NOTIFICATIONS_TAG = ["Notifications"]


@extend_schema_view(
    get=extend_schema(tags=NOTIFICATIONS_TAG, summary="Daftar notifikasi"),
)
class NotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = clamp_limit(request.query_params.get("limit"), 20)
        offset = clamp_offset(request.query_params.get("offset"))
        is_read = request.query_params.get("is_read")
        ntype = request.query_params.get("type")
        qs = Notification.objects.filter(user=request.user).order_by("-created_at")
        if is_read is not None:
            if is_read.lower() in ("true", "1"):
                qs = qs.filter(is_read=True)
            elif is_read.lower() in ("false", "0"):
                qs = qs.filter(is_read=False)
        if ntype:
            qs = qs.filter(type=ntype)
        total = qs.count()
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        rows = qs[offset : offset + limit]
        notifications = [
            {
                "id": str(n.id),
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "link_url": n.link_url,
                "related_id": str(n.related_id) if n.related_id else None,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat().replace("+00:00", "Z"),
            }
            for n in rows
        ]
        return ok(
            {
                "notifications": notifications,
                "unread_count": unread_count,
                **pagination_meta(total, limit, offset),
            }
        )


@extend_schema_view(
    put=extend_schema(tags=NOTIFICATIONS_TAG, summary="Tandai notifikasi dibaca"),
)
class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        updated = Notification.objects.filter(pk=id, user=request.user).update(is_read=True)
        if not updated:
            return err("NOT_FOUND", "Notification not found", status.HTTP_404_NOT_FOUND)
        return ok(message="Notification marked as read")


@extend_schema_view(
    put=extend_schema(tags=NOTIFICATIONS_TAG, summary="Tandai semua notifikasi dibaca"),
)
class NotificationsReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        Notification.objects.filter(user=request.user).update(is_read=True)
        return ok(message="All notifications marked as read")

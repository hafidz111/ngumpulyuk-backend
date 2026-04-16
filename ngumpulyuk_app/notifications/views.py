from drf_spectacular.utils import extend_schema, extend_schema_view

from ngumpulyuk_app.common.openapi_params import path_uuid, q_int, q_str
from ngumpulyuk_app.common.openapi_responses import R200
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView

from ngumpulyuk_app.common.api_response import err, ok
from ngumpulyuk_app.common.presenters import clamp_limit, clamp_offset, pagination_meta
from ngumpulyuk_app.notifications.models import Notification, PushDevice
from ngumpulyuk_app.notifications.serializers import (
    BlastNotificationSerializer,
    FCMDeviceDeleteSerializer,
    FCMDeviceRegisterSerializer,
)
from ngumpulyuk_app.notifications.services import blast_admin_notifications

NOTIFICATIONS_TAG = ["Notifications"]
NOTIFICATIONS_ADMIN_TAG = ["Notifications (Admin)"]


@extend_schema_view(
    get=extend_schema(
        tags=NOTIFICATIONS_TAG,
        summary="Daftar notifikasi",
        parameters=[
            q_str("is_read", "true / false"),
            q_str(
                "type",
                "event_reminder | new_event | event_update | community_post | comment_reply | new_member | event_full | admin_broadcast",
            ),
            q_int("limit", "Jumlah item (default 20, max 100)", 20),
            q_int("offset", "Skip N item", 0),
        ],
        responses=R200,
    ),
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
    put=extend_schema(
        tags=NOTIFICATIONS_TAG,
        summary="Tandai notifikasi dibaca",
        parameters=[path_uuid("id", "ID notifikasi")],
        request=None,
        responses=R200,
    ),
)
class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        updated = Notification.objects.filter(pk=id, user=request.user).update(is_read=True)
        if not updated:
            return err("NOT_FOUND", "Notification not found", status.HTTP_404_NOT_FOUND)
        return ok(message="Notification marked as read")


@extend_schema_view(
    put=extend_schema(
        tags=NOTIFICATIONS_TAG,
        summary="Tandai semua notifikasi dibaca",
        request=None,
        responses=R200,
    ),
)
class NotificationsReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        Notification.objects.filter(user=request.user).update(is_read=True)
        return ok(message="All notifications marked as read")


@extend_schema_view(
    post=extend_schema(
        tags=NOTIFICATIONS_TAG,
        summary="Daftarkan token FCM (push)",
        description="Simpan FCM registration token dari aplikasi mobile/web. "
        "Token yang sama akan dipindahkan ke akun ini jika sudah terdaftar di perangkat lain.",
        request=FCMDeviceRegisterSerializer,
        responses=R200,
    ),
    delete=extend_schema(
        tags=NOTIFICATIONS_TAG,
        summary="Hapus token FCM",
        description="Kirim `token` di body JSON untuk logout / uninstall.",
        request=FCMDeviceDeleteSerializer,
        responses=R200,
    ),
)
class PushDeviceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = FCMDeviceRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        token = ser.validated_data["token"]
        platform = ser.validated_data.get("platform")
        PushDevice.objects.update_or_create(
            token=token,
            defaults={"user": request.user, "platform": platform},
        )
        return ok(message="Push device registered")

    def delete(self, request):
        ser = FCMDeviceDeleteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        token = ser.validated_data["token"]
        n, _ = PushDevice.objects.filter(user=request.user, token=token).delete()
        if not n:
            return err("NOT_FOUND", "Device token not found", status.HTTP_404_NOT_FOUND)
        return ok(message="Push device removed")


@extend_schema_view(
    post=extend_schema(
        tags=NOTIFICATIONS_ADMIN_TAG,
        summary="Blast notifikasi + push (staff)",
        description="Hanya **is_staff**. Membuat notifikasi in-app bertipe `admin_broadcast` dan mengirim FCM "
        "ke pengguna yang punya token. `all_users` wajib disertai `confirm`: `BLAST_ALL_USERS`.",
        request=BlastNotificationSerializer,
        responses=R200,
    ),
)
class BlastNotificationView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        ser = BlastNotificationSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        v = ser.validated_data
        sent = blast_admin_notifications(
            title=v["title"],
            message=v["message"],
            link_url=(v.get("link_url") or "").strip() or None,
            user_ids=v.get("user_ids"),
            all_users=v.get("all_users", False),
        )
        return ok(
            data={
                "sent": sent,
                "all_users": v.get("all_users", False),
            },
            message="Blast queued",
        )

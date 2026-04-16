from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view

from ngumpulyuk_app.common.openapi_params import path_uuid, q_int
from ngumpulyuk_app.common.openapi_responses import R200, R201
from ngumpulyuk_app.communities.serializers import ThreadWriteSerializer
from ngumpulyuk_app.discussions.serializers import CommentWriteSerializer
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from ngumpulyuk_app.common.api_response import err, ok
from ngumpulyuk_app.common.presenters import clamp_limit, clamp_offset, mini_user, pagination_meta
from ngumpulyuk_app.users.models import ActivityHistory
from ngumpulyuk_app.discussions.models import Comment, Like, Thread
from ngumpulyuk_app.notifications.notify import notify_thread_new_comment

DISCUSSIONS_TAG = ["Discussions"]


@extend_schema_view(
    get=extend_schema(
        tags=DISCUSSIONS_TAG,
        summary="Komentar thread",
        parameters=[
            path_uuid("id", "ID thread"),
            q_int("limit", "Jumlah item (default 50, max 100)", 50),
            q_int("offset", "Skip N item", 0),
        ],
        responses=R200,
    ),
    post=extend_schema(
        tags=DISCUSSIONS_TAG,
        summary="Tambah komentar",
        parameters=[path_uuid("id", "ID thread")],
        request=CommentWriteSerializer,
        responses=R201,
    ),
)
class ThreadCommentsView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, id):
        try:
            t = Thread.objects.get(pk=id)
        except Thread.DoesNotExist:
            return err("NOT_FOUND", "Thread not found", status.HTTP_404_NOT_FOUND)
        limit = clamp_limit(request.query_params.get("limit"), 50)
        offset = clamp_offset(request.query_params.get("offset"))
        qs = (
            Comment.objects.filter(thread=t)
            .select_related("author")
            .prefetch_related("author__interest_rows")
            .order_by("created_at")
        )
        total = qs.count()
        rows = qs[offset : offset + limit]
        user = request.user if request.user.is_authenticated else None
        comments = []
        for c in rows:
            liked = False
            if user and user.is_authenticated:
                liked = Like.objects.filter(
                    user=user, likeable_type="comment", likeable_id=c.id
                ).exists()
            comments.append(
                {
                    "id": str(c.id),
                    "thread_id": str(t.id),
                    "content": c.content,
                    "like_count": c.like_count,
                    "author": mini_user(c.author),
                    "is_liked": liked,
                    "created_at": c.created_at.isoformat().replace("+00:00", "Z") if c.created_at else None,
                }
            )
        return ok({"comments": comments, **pagination_meta(total, limit, offset)})

    def post(self, request, id):
        try:
            t = Thread.objects.get(pk=id)
        except Thread.DoesNotExist:
            return err("NOT_FOUND", "Thread not found", status.HTTP_404_NOT_FOUND)
        ser = CommentWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        c = Comment.objects.create(thread=t, author=request.user, content=ser.validated_data["content"])
        label = (t.title or "").strip() or str(t.id)[:8]
        ActivityHistory.objects.create(
            user=request.user,
            activity_type="commented",
            description=f"Commented on thread: {label}",
            related_type="thread",
            related_id=t.id,
        )
        notify_thread_new_comment(c, t)
        return ok(
            {
                "id": str(c.id),
                "thread_id": str(t.id),
                "content": c.content,
                "like_count": c.like_count,
                "author": mini_user(c.author),
                "created_at": c.created_at.isoformat().replace("+00:00", "Z"),
            },
            message="Comment added successfully",
            status_code=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    post=extend_schema(
        tags=DISCUSSIONS_TAG,
        summary="Suka thread",
        parameters=[path_uuid("id", "ID thread")],
        request=None,
        responses=R200,
    ),
    delete=extend_schema(
        tags=DISCUSSIONS_TAG,
        summary="Batal suka thread",
        parameters=[path_uuid("id", "ID thread")],
        responses=R200,
    ),
)
class ThreadLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            t = Thread.objects.get(pk=id)
        except Thread.DoesNotExist:
            return err("NOT_FOUND", "Thread not found", status.HTTP_404_NOT_FOUND)
        Like.objects.get_or_create(
            user=request.user, likeable_type="thread", likeable_id=t.id
        )
        return ok(message="Thread liked")

    def delete(self, request, id):
        for like in Like.objects.filter(user=request.user, likeable_type="thread", likeable_id=id):
            like.delete()
        return ok(message="Thread unliked")


@extend_schema_view(
    post=extend_schema(
        tags=DISCUSSIONS_TAG,
        summary="Suka komentar",
        parameters=[path_uuid("id", "ID komentar")],
        request=None,
        responses=R200,
    ),
)
class CommentLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            c = Comment.objects.get(pk=id)
        except Comment.DoesNotExist:
            return err("NOT_FOUND", "Comment not found", status.HTTP_404_NOT_FOUND)
        Like.objects.get_or_create(
            user=request.user, likeable_type="comment", likeable_id=c.id
        )
        return ok(message="Comment liked")

@extend_schema_view(
    get=extend_schema(
        tags=DISCUSSIONS_TAG,
        summary="Global Thread Feed",
        parameters=[
            q_int("limit", "Jumlah item (default 20, max 100)", 20),
            q_int("offset", "Skip N item", 0),
        ],
        responses=R200,
    ),
)
class ThreadFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from ngumpulyuk_app.communities.models import CommunityMember
        from ngumpulyuk_app.communities.views import thread_dict

        limit = clamp_limit(request.query_params.get("limit"), 20)
        offset = clamp_offset(request.query_params.get("offset"))

        user_communities = CommunityMember.objects.filter(user=request.user).values_list("community_id", flat=True)
        qs = (
            Thread.objects.filter(Q(community_id__in=user_communities) | Q(community_id__isnull=True))
            .select_related("author", "community", "related_event")
            .prefetch_related("author__interest_rows")
            .order_by("-created_at")
        )

        total = qs.count()
        rows = qs[offset : offset + limit]

        threads = [thread_dict(t, request.user, include_community_name=True) for t in rows]
        return ok({"threads": threads, **pagination_meta(total, limit, offset)})


@extend_schema_view(
    post=extend_schema(
        tags=DISCUSSIONS_TAG,
        summary="Buat thread global",
        request=ThreadWriteSerializer,
        responses=R201,
    ),
)
class ThreadCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from ngumpulyuk_app.communities.views import thread_dict
        from ngumpulyuk_app.events.models import Event, EventParticipant
        from rest_framework.serializers import ValidationError

        ser = ThreadWriteSerializer(data=request.data)
        try:
            ser.is_valid(raise_exception=True)
        except ValidationError as ex:
            detail = ex.detail
            if isinstance(detail, dict):
                images_error = detail.get("images")
                if isinstance(images_error, dict):
                    return err(
                        images_error.get("code", "VALIDATION_ERROR"),
                        images_error.get("message", "Invalid images payload"),
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                    )
                if isinstance(images_error, list) and images_error and isinstance(images_error[0], dict):
                    return err(
                        images_error[0].get("code", "VALIDATION_ERROR"),
                        images_error[0].get("message", "Invalid images payload"),
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                    )
            raise
        v = ser.validated_data
        related_event_id = v.get("related_event_id")
        related_event = None
        if related_event_id:
            related_event = Event.objects.filter(id=related_event_id).first()
            if not related_event:
                return err("NOT_FOUND", "Related event not found", status.HTTP_404_NOT_FOUND)
            is_participant = EventParticipant.objects.filter(
                event=related_event, user=request.user, status="confirmed"
            ).exists()
            if not is_participant:
                return err("FORBIDDEN", "You must join the related event", status.HTTP_403_FORBIDDEN)
        t = Thread.objects.create(
            community=None,
            author=request.user,
            title=(v.get("title") or "").strip() or "",
            content=v["content"],
            images=v.get("images") or [],
            related_event=related_event,
        )
        ActivityHistory.objects.create(
            user=request.user,
            activity_type="posted_thread",
            description="Posted thread in global feed",
            related_type="thread",
            related_id=t.id,
        )
        return ok(
            thread_dict(t, request.user, include_community_name=True),
            message="Thread created successfully",
            status_code=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        tags=DISCUSSIONS_TAG,
        summary="Detail Thread",
        parameters=[path_uuid("id", "ID thread")],
        responses=R200,
    ),
    delete=extend_schema(
        tags=DISCUSSIONS_TAG,
        summary="Hapus Thread",
        parameters=[path_uuid("id", "ID thread")],
        responses=R200,
    ),
)
class ThreadDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        from ngumpulyuk_app.communities.views import thread_dict

        try:
            t = Thread.objects.select_related("author", "community", "related_event").get(pk=id)
        except Thread.DoesNotExist:
            return err("NOT_FOUND", "Thread not found", status.HTTP_404_NOT_FOUND)
        return ok(thread_dict(t, request.user, include_community_name=True))

    def delete(self, request, id):
        from ngumpulyuk_app.communities.views import thread_dict

        try:
            t = Thread.objects.select_related("author", "community", "related_event").get(pk=id)
        except Thread.DoesNotExist:
            return err("NOT_FOUND", "Thread not found", status.HTTP_404_NOT_FOUND)

        thread_data = thread_dict(t, request.user, include_community_name=True)
        if not thread_data.get("can_delete"):
            return err("FORBIDDEN", "You do not have permission to delete this thread", status.HTTP_403_FORBIDDEN)

        t.delete()
        return ok(message="Thread deleted successfully")

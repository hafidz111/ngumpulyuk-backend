from drf_spectacular.utils import extend_schema, extend_schema_view

from ngumpulyuk_app.common.openapi_params import path_uuid, q_int
from ngumpulyuk_app.common.openapi_responses import R200, R201
from ngumpulyuk_app.discussions.serializers import CommentWriteSerializer
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from ngumpulyuk_app.common.api_response import err, ok
from ngumpulyuk_app.common.presenters import clamp_limit, clamp_offset, mini_user, pagination_meta
from ngumpulyuk_app.users.models import ActivityHistory
from ngumpulyuk_app.discussions.models import Comment, Like, Thread

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
        qs = Comment.objects.filter(thread=t).select_related("author").order_by("created_at")
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

from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView

from ngumpulyuk_app.communities.serializers import CommunityWriteSerializer, ThreadWriteSerializer
from ngumpulyuk_app.common.api_response import err, ok
from ngumpulyuk_app.common.openapi_params import path_uuid, q_int, q_str
from ngumpulyuk_app.common.openapi_responses import R200, R201
from ngumpulyuk_app.common.presenters import (
    clamp_limit,
    clamp_offset,
    mini_user,
    mini_user_creator,
    pagination_meta,
)
from ngumpulyuk_app.communities.models import Community, CommunityMember
from ngumpulyuk_app.events.models import EventParticipant
from ngumpulyuk_app.discussions.models import Thread
from ngumpulyuk_app.notifications.notify import notify_community_new_member, notify_community_new_thread
from ngumpulyuk_app.users.models import ActivityHistory

COMMUNITIES_TAG = ["Communities"]

_COMMUNITY_LIST_PARAMS = [
    q_str("category", "Filter kategori"),
    q_str("search", "Cari nama / deskripsi"),
    q_str("verified", "true / false — komunitas terverifikasi"),
    q_int("limit", "Jumlah item (default 20, max 100)", 20),
    q_int("offset", "Skip N item", 0),
]


def community_dict(c, request_user, detail=False):
    creator = c.creator
    is_member = False
    user_role = None
    if request_user and request_user.is_authenticated:
        m = CommunityMember.objects.filter(community=c, user=request_user).first()
        if m:
            is_member = True
            user_role = m.role
    base = {
        "id": str(c.id),
        "name": c.name,
        "description": c.description,
        "category": c.category,
        "cover_image": c.cover_image,
        "logo": c.logo,
        "member_count": c.member_count,
        "is_verified": c.is_verified,
        "creator": mini_user_creator(creator),
        "is_member": is_member,
        "created_at": c.created_at.isoformat().replace("+00:00", "Z") if c.created_at else None,
    }
    if detail:
        base["creator"] = {
            "id": str(creator.id),
            "username": creator.username,
            "full_name": creator.full_name,
        }
        base["user_role"] = user_role
    return base


def _thread_permissions(t, request_user):
    can_delete = False
    can_edit = False
    can_moderate = False
    if request_user and request_user.is_authenticated:
        is_author = request_user.id == t.author_id
        is_moderator = False
        if t.community_id:
            is_creator = t.community.creator_id == request_user.id if getattr(t, "community", None) else False
            is_admin_or_moderator = CommunityMember.objects.filter(
                community_id=t.community_id, user=request_user, role__in=["admin", "moderator"]
            ).exists()
            is_moderator = is_creator or is_admin_or_moderator
        can_moderate = is_moderator
        can_delete = is_author or is_moderator
        can_edit = is_author
    return {
        "can_delete": can_delete,
        "can_edit": can_edit,
        "can_moderate": can_moderate,
    }


def thread_dict(t, request_user, include_community_name=False):
    from ngumpulyuk_app.discussions.models import Like

    liked = False
    if request_user and request_user.is_authenticated:
        liked = Like.objects.filter(
            user=request_user, likeable_type="thread", likeable_id=t.id
        ).exists()
    permissions = _thread_permissions(t, request_user)
    data = {
        "id": str(t.id),
        "community_id": str(t.community_id) if t.community_id else None,
        "title": t.title,
        "content": t.content,
        "images": t.images or [],
        "like_count": t.like_count,
        "comment_count": t.comment_count,
        "is_pinned": t.is_pinned,
        "related_event_id": str(t.related_event_id) if t.related_event_id else None,
        "related_event": (
            {"id": str(t.related_event_id), "title": t.related_event.title}
            if getattr(t, "related_event", None)
            else None
        ),
        "author": mini_user(t.author),
        "is_liked": liked,
        **permissions,
        "created_at": t.created_at.isoformat().replace("+00:00", "Z") if t.created_at else None,
    }
    if include_community_name:
        data["community_name"] = t.community.name if getattr(t, "community", None) else None
    return data


@extend_schema_view(
    get=extend_schema(
        tags=COMMUNITIES_TAG,
        summary="Daftar komunitas",
        parameters=_COMMUNITY_LIST_PARAMS,
        responses=R200,
    ),
    post=extend_schema(
        tags=COMMUNITIES_TAG,
        summary="Buat komunitas",
        request=CommunityWriteSerializer,
        responses=R201,
    ),
)
class CommunityListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        limit = clamp_limit(request.query_params.get("limit"), 20)
        offset = clamp_offset(request.query_params.get("offset"))
        qs = Community.objects.select_related("creator").all()
        category = request.query_params.get("category")
        search = request.query_params.get("search")
        verified = request.query_params.get("verified")
        if category:
            qs = qs.filter(category=category)
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
        if verified is not None:
            if verified.lower() in ("true", "1"):
                qs = qs.filter(is_verified=True)
            elif verified.lower() in ("false", "0"):
                qs = qs.filter(is_verified=False)
        total = qs.count()
        page = qs.order_by("-created_at")[offset : offset + limit]
        user = request.user if request.user.is_authenticated else None
        communities = [community_dict(c, user, detail=False) for c in page]
        return ok({"communities": communities, **pagination_meta(total, limit, offset)})

    def post(self, request):
        ser = CommunityWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        v = ser.validated_data
        c = Community.objects.create(
            name=v["name"],
            description=v["description"],
            category=v["category"],
            cover_image=v.get("cover_image") or None,
            logo=v.get("logo") or None,
            creator=request.user,
        )
        ActivityHistory.objects.create(
            user=request.user,
            activity_type="created_community",
            description=f"Created community: {c.name}",
            related_type="community",
            related_id=c.id,
        )
        return ok(community_dict(c, request.user, detail=True), message="Community created successfully", status_code=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        tags=COMMUNITIES_TAG,
        summary="Detail komunitas",
        parameters=[path_uuid("id", "ID komunitas")],
        responses=R200,
    ),
)
class CommunityDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        try:
            c = Community.objects.select_related("creator").get(pk=id)
        except Community.DoesNotExist:
            return err("NOT_FOUND", "Community not found", status.HTTP_404_NOT_FOUND)
        user = request.user if request.user.is_authenticated else None
        return ok(community_dict(c, user, detail=True))


@extend_schema_view(
    post=extend_schema(
        tags=COMMUNITIES_TAG,
        summary="Gabung komunitas",
        parameters=[path_uuid("id", "ID komunitas")],
        request=None,
        responses=R200,
    ),
)
class CommunityJoinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            c = Community.objects.get(pk=id)
        except Community.DoesNotExist:
            return err("NOT_FOUND", "Community not found", status.HTTP_404_NOT_FOUND)
        m, created = CommunityMember.objects.get_or_create(
            community=c, user=request.user, defaults={"role": "member"}
        )
        if not created:
            return err("ALREADY_JOINED", "Already a member", status.HTTP_400_BAD_REQUEST)
        ActivityHistory.objects.create(
            user=request.user,
            activity_type="joined_community",
            description=f"Joined community: {c.name}",
            related_type="community",
            related_id=c.id,
        )
        notify_community_new_member(c, new_member=request.user)
        return ok(message="Successfully joined community")


@extend_schema_view(
    delete=extend_schema(
        tags=COMMUNITIES_TAG,
        summary="Keluar komunitas",
        parameters=[path_uuid("id", "ID komunitas")],
        responses=R200,
    ),
)
class CommunityLeaveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        try:
            c = Community.objects.get(pk=id)
        except Community.DoesNotExist:
            return err("NOT_FOUND", "Community not found", status.HTTP_404_NOT_FOUND)
        memberships = CommunityMember.objects.filter(community=c, user=request.user)
        if not memberships.exists():
            return err("VALIDATION_ERROR", "Not a member", status.HTTP_400_BAD_REQUEST)
        for m in memberships:
            m.delete()
        ActivityHistory.objects.create(
            user=request.user,
            activity_type="left_community",
            description=f"Left community: {c.name}",
            related_type="community",
            related_id=c.id,
        )
        return ok(message="Successfully left community")


@extend_schema_view(
    get=extend_schema(
        tags=COMMUNITIES_TAG,
        summary="Daftar anggota komunitas",
        parameters=[
            path_uuid("id", "ID komunitas"),
            q_str("role", "admin | moderator | member"),
            q_int("limit", "Jumlah item (default 50, max 100)", 50),
            q_int("offset", "Skip N item", 0),
        ],
        responses=R200,
    ),
)
class CommunityMembersView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        try:
            c = Community.objects.get(pk=id)
        except Community.DoesNotExist:
            return err("NOT_FOUND", "Community not found", status.HTTP_404_NOT_FOUND)
        role = request.query_params.get("role")
        search = request.query_params.get("search")
        limit = clamp_limit(request.query_params.get("limit"), 50)
        offset = clamp_offset(request.query_params.get("offset"))
        qs = CommunityMember.objects.filter(community=c).select_related("user")
        if role:
            qs = qs.filter(role=role)
        if search:
            qs = qs.filter(Q(user__username__icontains=search) | Q(user__full_name__icontains=search))
        qs = qs.order_by("joined_at")
        total = qs.count()
        rows = qs[offset : offset + limit]
        members = [
            {
                "user_id": str(m.user_id),
                "username": m.user.username,
                "full_name": m.user.full_name,
                "profile_picture": m.user.profile_picture,
                "role": m.role,
                "joined_at": m.joined_at.isoformat().replace("+00:00", "Z"),
            }
            for m in rows
        ]
        return ok({"members": members, **pagination_meta(total, limit, offset)})


@extend_schema_view(
    get=extend_schema(
        tags=COMMUNITIES_TAG,
        summary="Thread di komunitas",
        parameters=[
            path_uuid("id", "ID komunitas"),
            q_str("sort", "latest | popular (default latest)"),
            q_int("limit", "Jumlah item (default 20, max 100)", 20),
            q_int("offset", "Skip N item", 0),
        ],
        responses=R200,
    ),
    post=extend_schema(
        tags=COMMUNITIES_TAG,
        summary="Buat thread di komunitas (anggota)",
        parameters=[path_uuid("id", "ID komunitas")],
        request=ThreadWriteSerializer,
        responses=R201,
    ),
)
class CommunityThreadsView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, id):
        try:
            c = Community.objects.get(pk=id)
        except Community.DoesNotExist:
            return err("NOT_FOUND", "Community not found", status.HTTP_404_NOT_FOUND)
        limit = clamp_limit(request.query_params.get("limit"), 20)
        offset = clamp_offset(request.query_params.get("offset"))
        sort = request.query_params.get("sort") or "latest"
        qs = (
            Thread.objects.filter(community=c)
            .select_related("author", "community", "related_event")
            .prefetch_related("author__interest_rows")
        )
        if sort == "popular":
            qs = qs.order_by("-like_count", "-created_at")
        else:
            qs = qs.order_by("-is_pinned", "-created_at")
        total = qs.count()
        rows = qs[offset : offset + limit]
        user = request.user if request.user.is_authenticated else None
        threads = [thread_dict(t, user) for t in rows]
        return ok({"threads": threads, **pagination_meta(total, limit, offset)})

    def post(self, request, id):
        try:
            c = Community.objects.get(pk=id)
        except Community.DoesNotExist:
            return err("NOT_FOUND", "Community not found", status.HTTP_404_NOT_FOUND)
        if not CommunityMember.objects.filter(community=c, user=request.user).exists():
            return err("FORBIDDEN", "Join the community first", status.HTTP_403_FORBIDDEN)
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
            from ngumpulyuk_app.events.models import Event

            related_event = Event.objects.filter(id=related_event_id).first()
            if not related_event:
                return err("NOT_FOUND", "Related event not found", status.HTTP_404_NOT_FOUND)
            is_participant = EventParticipant.objects.filter(
                event=related_event, user=request.user, status="confirmed"
            ).exists()
            if not is_participant:
                return err("FORBIDDEN", "You must join the related event", status.HTTP_403_FORBIDDEN)
        t = Thread.objects.create(
            community=c,
            author=request.user,
            title=(v.get("title") or "").strip() or "",
            content=v["content"],
            images=v.get("images") or [],
            related_event=related_event,
        )
        ActivityHistory.objects.create(
            user=request.user,
            activity_type="posted_thread",
            description=f"Posted thread in {c.name}",
            related_type="thread",
            related_id=t.id,
        )
        notify_community_new_thread(t, c)
        return ok(thread_dict(t, request.user), message="Thread created successfully", status_code=status.HTTP_201_CREATED)

@extend_schema_view(
    patch=extend_schema(
        tags=COMMUNITIES_TAG,
        summary="Ubah Role Anggota",
        parameters=[
            path_uuid("id", "ID komunitas"),
            path_uuid("user_id", "ID User"),
        ],
        responses=R200,
    ),
)
class CommunityMemberRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id, user_id):
        try:
            c = Community.objects.get(pk=id)
        except Community.DoesNotExist:
            return err("NOT_FOUND", "Community not found", status.HTTP_404_NOT_FOUND)

        is_creator = (c.creator == request.user)
        is_admin = CommunityMember.objects.filter(community=c, user=request.user, role="admin").exists()

        if not (is_creator or is_admin):
            return err("FORBIDDEN", "Only admin or creator can change member roles", status.HTTP_403_FORBIDDEN)
            
        if str(c.creator.id) == str(user_id):
            return err("FORBIDDEN", "Cannot modify the role of the community creator", status.HTTP_403_FORBIDDEN)

        try:
            member = CommunityMember.objects.get(community=c, user_id=user_id)
        except CommunityMember.DoesNotExist:
            return err("NOT_FOUND", "User is not a member of this community", status.HTTP_404_NOT_FOUND)

        new_role = request.data.get("role")
        if new_role not in ["admin", "moderator", "member"]:
            return err("INVALID_DATA", "Role must be admin, moderator, or member", status.HTTP_400_BAD_REQUEST)

        member.role = new_role
        member.save()

        return ok(message=f"Success updated role to {new_role}")

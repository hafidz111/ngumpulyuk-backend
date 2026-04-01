from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from ngumpulyuk_app.common.api_response import err, ok
from ngumpulyuk_app.common.presenters import (
    clamp_limit,
    clamp_offset,
    mini_user,
    mini_user_creator,
    pagination_meta,
)
from ngumpulyuk_app.communities.models import Community, CommunityMember
from ngumpulyuk_app.discussions.models import Thread
from ngumpulyuk_app.users.models import ActivityHistory

COMMUNITIES_TAG = ["Communities"]


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


def thread_dict(t, request_user):
    from ngumpulyuk_app.discussions.models import Like

    liked = False
    if request_user and request_user.is_authenticated:
        liked = Like.objects.filter(
            user=request_user, likeable_type="thread", likeable_id=t.id
        ).exists()
    return {
        "id": str(t.id),
        "community_id": str(t.community_id),
        "title": t.title,
        "content": t.content,
        "images": t.images or [],
        "like_count": t.like_count,
        "comment_count": t.comment_count,
        "is_pinned": t.is_pinned,
        "author": mini_user(t.author),
        "is_liked": liked,
        "created_at": t.created_at.isoformat().replace("+00:00", "Z") if t.created_at else None,
    }


@extend_schema_view(
    get=extend_schema(tags=COMMUNITIES_TAG, summary="Daftar komunitas"),
    post=extend_schema(tags=COMMUNITIES_TAG, summary="Buat komunitas"),
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
        name = request.data.get("name")
        description = request.data.get("description")
        category = request.data.get("category")
        if not name or not description or not category:
            return err("VALIDATION_ERROR", "name, description, category required", status.HTTP_422_UNPROCESSABLE_ENTITY)
        c = Community.objects.create(
            name=name,
            description=description,
            category=category,
            cover_image=request.data.get("cover_image"),
            logo=request.data.get("logo"),
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
    get=extend_schema(tags=COMMUNITIES_TAG, summary="Detail komunitas"),
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
    post=extend_schema(tags=COMMUNITIES_TAG, summary="Gabung komunitas"),
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
        return ok(message="Successfully joined community")


@extend_schema_view(
    delete=extend_schema(tags=COMMUNITIES_TAG, summary="Keluar komunitas"),
)
class CommunityLeaveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        try:
            c = Community.objects.get(pk=id)
        except Community.DoesNotExist:
            return err("NOT_FOUND", "Community not found", status.HTTP_404_NOT_FOUND)
        for m in CommunityMember.objects.filter(community=c, user=request.user):
            m.delete()
        return ok(message="Successfully left community")


@extend_schema_view(
    get=extend_schema(tags=COMMUNITIES_TAG, summary="Daftar anggota komunitas"),
)
class CommunityMembersView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        try:
            c = Community.objects.get(pk=id)
        except Community.DoesNotExist:
            return err("NOT_FOUND", "Community not found", status.HTTP_404_NOT_FOUND)
        role = request.query_params.get("role")
        limit = clamp_limit(request.query_params.get("limit"), 50)
        offset = clamp_offset(request.query_params.get("offset"))
        qs = CommunityMember.objects.filter(community=c).select_related("user")
        if role:
            qs = qs.filter(role=role)
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
    get=extend_schema(tags=COMMUNITIES_TAG, summary="Thread di komunitas"),
    post=extend_schema(tags=COMMUNITIES_TAG, summary="Buat thread di komunitas (anggota)"),
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
        qs = Thread.objects.filter(community=c).select_related("author")
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
        title = request.data.get("title")
        content = request.data.get("content")
        images = request.data.get("images") or []
        if not content:
            return err("VALIDATION_ERROR", "content required", status.HTTP_422_UNPROCESSABLE_ENTITY)
        t = Thread.objects.create(
            community=c,
            author=request.user,
            title=title or "",
            content=content,
            images=images,
        )
        ActivityHistory.objects.create(
            user=request.user,
            activity_type="posted_thread",
            description=f"Posted thread in {c.name}",
            related_type="thread",
            related_id=t.id,
        )
        return ok(thread_dict(t, request.user), message="Thread created successfully", status_code=status.HTTP_201_CREATED)

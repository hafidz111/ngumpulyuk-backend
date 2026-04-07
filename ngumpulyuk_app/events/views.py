from django.db import transaction
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from ngumpulyuk_app.common.api_response import err, ok
from ngumpulyuk_app.common.openapi_params import path_uuid, q_int, q_str
from ngumpulyuk_app.common.openapi_responses import R200, R201
from ngumpulyuk_app.common.presenters import clamp_limit, clamp_offset, pagination_meta
from ngumpulyuk_app.events.models import Event, EventParticipant, EventTag
from ngumpulyuk_app.events.serializers import EventWriteSerializer, event_detail, event_list_item
from ngumpulyuk_app.users.models import ActivityHistory

EVENTS_TAG = ["Events"]

_EVENT_LIST_PARAMS = [
    q_str("category", "Filter kategori"),
    q_str("location", "Filter area lokasi (mencocokkan location_area)"),
    q_str("status", "upcoming | ongoing | completed | cancelled"),
    q_str("search", "Cari di judul / deskripsi"),
    q_str("date_from", "Tanggal mulai filter (YYYY-MM-DD)"),
    q_str("date_to", "Tanggal akhir filter (YYYY-MM-DD)"),
    q_str("sort", "date_asc | date_desc | popular | newest (default: date_asc)"),
    q_int("limit", "Jumlah item (default 20, max 100)", 20),
    q_int("offset", "Skip N item", 0),
]


@extend_schema_view(
    get=extend_schema(
        tags=EVENTS_TAG,
        summary="Daftar event",
        parameters=_EVENT_LIST_PARAMS,
        responses=R200,
    ),
    post=extend_schema(
        tags=EVENTS_TAG,
        summary="Buat event",
        request=EventWriteSerializer,
        responses=R201,
    ),
)
class EventListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        limit = clamp_limit(request.query_params.get("limit"), 20)
        offset = clamp_offset(request.query_params.get("offset"))
        qs = Event.objects.select_related("creator").all()
        category = request.query_params.get("category")
        location = request.query_params.get("location")
        st = request.query_params.get("status")
        search = request.query_params.get("search")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        sort = request.query_params.get("sort") or "date_asc"
        if category:
            qs = qs.filter(category=category)
        if location:
            qs = qs.filter(location_area__icontains=location)
        if st:
            qs = qs.filter(status=st)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
        if date_from:
            qs = qs.filter(event_date__gte=date_from)
        if date_to:
            qs = qs.filter(event_date__lte=date_to)
        if sort == "date_desc":
            qs = qs.order_by("-event_date", "-event_time")
        elif sort == "newest":
            qs = qs.order_by("-created_at")
        elif sort == "popular":
            qs = qs.order_by("-current_participants", "-created_at")
        else:
            qs = qs.order_by("event_date", "event_time")
        total = qs.count()
        page = qs[offset : offset + limit]
        events = [event_list_item(e) for e in page]
        return ok({"events": events, **pagination_meta(total, limit, offset)})

    def post(self, request):
        ser = EventWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        v = ser.validated_data
        t = ser.parse_time(v["event_time"])
        end_t = ser.parse_time(v["end_time"]) if v.get("end_time") else None
        with transaction.atomic():
            ev = Event.objects.create(
                creator=request.user,
                title=v["title"],
                description=v["description"],
                category=v["category"],
                cover_image=v.get("cover_image") or None,
                event_date=v["event_date"],
                event_time=t,
                end_date=v.get("end_date"),
                end_time=end_t,
                location_area=v["location_area"],
                location_address=v["location_address"],
                latitude=v.get("latitude"),
                longitude=v.get("longitude"),
                max_participants=v["max_participants"],
                is_competition=v.get("is_competition", False),
                difficulty_level=v.get("difficulty_level"),
            )
            for tag in v.get("tags") or []:
                EventTag.objects.create(event=ev, tag_name=tag)
            ActivityHistory.objects.create(
                user=request.user,
                activity_type="created_event",
                description=f"Created event: {ev.title}",
                related_type="event",
                related_id=ev.id,
            )
        return ok(event_detail(ev, request.user), message="Event created successfully", status_code=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        tags=EVENTS_TAG,
        summary="Detail event",
        parameters=[path_uuid("id", "ID event")],
        responses=R200,
    ),
    put=extend_schema(
        tags=EVENTS_TAG,
        summary="Update event (pemilik)",
        parameters=[path_uuid("id", "ID event")],
        request=EventWriteSerializer,
        responses=R200,
    ),
    delete=extend_schema(
        tags=EVENTS_TAG,
        summary="Hapus event (pemilik)",
        parameters=[path_uuid("id", "ID event")],
        responses=R200,
    ),
)
class EventDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ("PUT", "DELETE"):
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_object(self, pk):
        try:
            return Event.objects.select_related("creator").get(pk=pk)
        except Event.DoesNotExist:
            return None

    def get(self, request, id):
        ev = self.get_object(id)
        if not ev:
            return err("NOT_FOUND", "Event not found", status.HTTP_404_NOT_FOUND)
        user = request.user if request.user.is_authenticated else None
        return ok(event_detail(ev, user))

    def put(self, request, id):
        ev = self.get_object(id)
        if not ev:
            return err("NOT_FOUND", "Event not found", status.HTTP_404_NOT_FOUND)
        if ev.creator_id != request.user.id:
            return err("FORBIDDEN", "No permission", status.HTTP_403_FORBIDDEN)
        ser = EventWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        v = ser.validated_data
        t = ser.parse_time(v["event_time"])
        end_t = ser.parse_time(v["end_time"]) if v.get("end_time") else None
        with transaction.atomic():
            ev.title = v["title"]
            ev.description = v["description"]
            ev.category = v["category"]
            ev.cover_image = v.get("cover_image") or None
            ev.event_date = v["event_date"]
            ev.event_time = t
            ev.end_date = v.get("end_date")
            ev.end_time = end_t
            ev.location_area = v["location_area"]
            ev.location_address = v["location_address"]
            ev.latitude = v.get("latitude")
            ev.longitude = v.get("longitude")
            ev.max_participants = v["max_participants"]
            ev.is_competition = v.get("is_competition", False)
            ev.difficulty_level = v.get("difficulty_level")
            ev.save()
            ev.tags.all().delete()
            for tag in v.get("tags") or []:
                EventTag.objects.create(event=ev, tag_name=tag)
        return ok(event_detail(ev, request.user), message="Event updated successfully")

    def delete(self, request, id):
        ev = self.get_object(id)
        if not ev:
            return err("NOT_FOUND", "Event not found", status.HTTP_404_NOT_FOUND)
        if ev.creator_id != request.user.id:
            return err("FORBIDDEN", "No permission", status.HTTP_403_FORBIDDEN)
        ev.delete()
        return ok(message="Event deleted successfully")


@extend_schema_view(
    post=extend_schema(
        tags=EVENTS_TAG,
        summary="Gabung event",
        parameters=[path_uuid("id", "ID event")],
        request=None,
        responses=R200,
    ),
)
class EventJoinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            ev = Event.objects.get(pk=id)
        except Event.DoesNotExist:
            return err("NOT_FOUND", "Event not found", status.HTTP_404_NOT_FOUND)
        ep = EventParticipant.objects.filter(event=ev, user=request.user).first()
        if ep and ep.status == "confirmed":
            return err("ALREADY_JOINED", "Already joined", status.HTTP_400_BAD_REQUEST)
        if ev.current_participants >= ev.max_participants:
            return err("EVENT_FULL", "Event has reached maximum participants", status.HTTP_400_BAD_REQUEST)
        if ep:
            ep.status = "confirmed"
            ep.save()
        else:
            ep = EventParticipant.objects.create(event=ev, user=request.user, status="confirmed")
        ep.refresh_from_db()
        return ok(
            {
                "event_id": str(ev.id),
                "user_id": str(request.user.id),
                "status": ep.status,
                "joined_at": ep.joined_at.isoformat().replace("+00:00", "Z"),
            },
            message="Successfully joined event",
        )


@extend_schema_view(
    delete=extend_schema(
        tags=EVENTS_TAG,
        summary="Tinggalkan event",
        parameters=[path_uuid("id", "ID event")],
        responses=R200,
    ),
)
class EventLeaveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        try:
            ev = Event.objects.get(pk=id)
        except Event.DoesNotExist:
            return err("NOT_FOUND", "Event not found", status.HTTP_404_NOT_FOUND)
        qs = EventParticipant.objects.filter(event=ev, user=request.user)
        if not qs.exists():
            return err("VALIDATION_ERROR", "Not a participant", status.HTTP_400_BAD_REQUEST)
        for ep in qs:
            ep.delete()
        return ok(message="Successfully left event")


@extend_schema_view(
    get=extend_schema(
        tags=EVENTS_TAG,
        summary="Daftar peserta event",
        parameters=[
            path_uuid("id", "ID event"),
            q_int("limit", "Jumlah item (default 50, max 100)", 50),
            q_int("offset", "Skip N item", 0),
        ],
        responses=R200,
    ),
)
class EventParticipantsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        try:
            ev = Event.objects.get(pk=id)
        except Event.DoesNotExist:
            return err("NOT_FOUND", "Event not found", status.HTTP_404_NOT_FOUND)
        limit = clamp_limit(request.query_params.get("limit"), 50)
        offset = clamp_offset(request.query_params.get("offset"))
        qs = (
            EventParticipant.objects.filter(event=ev, status="confirmed")
            .select_related("user")
            .order_by("joined_at")
        )
        total = qs.count()
        rows = qs[offset : offset + limit]
        participants = [
            {
                "user_id": str(p.user_id),
                "username": p.user.username,
                "full_name": p.user.full_name,
                "profile_picture": p.user.profile_picture,
                "status": p.status,
                "joined_at": p.joined_at.isoformat().replace("+00:00", "Z"),
            }
            for p in rows
        ]
        return ok({"participants": participants, **pagination_meta(total, limit, offset)})


@extend_schema_view(
    get=extend_schema(
        tags=EVENTS_TAG,
        summary="Daftar saran kategori event",
        parameters=[
            q_str("search", "Pencarian nama kategori"),
        ],
        responses=R200,
    ),
)
class EventCategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        search = request.query_params.get("search", "").strip().lower()

        default_categories = [
            "Olahraga",
            "Seni & Budaya",
            "Teknologi",
            "Pendidikan",
            "Musik",
            "Kuliner",
            "Bisnis",
            "Kesehatan",
            "Sosial",
            "Hiburan",
            "Lainnya"
        ]

        db_categories = list(Event.objects.exclude(category="").values_list("category", flat=True).distinct())

        raw_categories = [c for c in (default_categories + db_categories) if c]

        category_dict = {}
        for c in raw_categories:
            lower_c = c.lower()
            if lower_c not in category_dict:
                category_dict[lower_c] = c

        all_categories = list(category_dict.values())

        if search:
            filtered_categories = [c for c in all_categories if search in c.lower()]
        else:
            filtered_categories = all_categories

        return ok({"categories": filtered_categories})


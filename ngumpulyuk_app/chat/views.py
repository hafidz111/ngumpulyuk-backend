from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from ngumpulyuk_app.chat.models import ChatAnswerCorrection, ChatTurn
from ngumpulyuk_app.chat.serializers import (
    ChatCorrectionUpdateSerializer,
    ChatCorrectionWriteSerializer,
    ChatFeedbackSerializer,
    ChatMessageSerializer,
    correction_item,
)
from ngumpulyuk_app.chat.services.corrections import find_correction, mark_correction_used
from ngumpulyuk_app.chat.services.faq import list_faq_templates
from ngumpulyuk_app.chat.services.pipeline import run_chat
from ngumpulyuk_app.common.api_response import err, ok
from ngumpulyuk_app.common.openapi_params import q_int, q_str
from ngumpulyuk_app.common.openapi_responses import R200
from ngumpulyuk_app.common.presenters import clamp_limit, clamp_offset, pagination_meta

CHAT_TAG = ["Chat"]
CHAT_ADMIN_TAG = ["Chat (Admin)"]


def _dedupe_cards(cards: list) -> list:
    seen = set()
    out = []
    for c in cards:
        payload = c.get("payload") or {}
        pid = payload.get("id") or payload.get("name")
        key = (c.get("type"), str(pid))
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


@extend_schema_view(
    post=extend_schema(
        tags=CHAT_TAG,
        summary="Chat assistant (FAQ + rekomendasi)",
        request=ChatMessageSerializer,
        responses=R200,
    ),
)
class ChatMessageView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "chat"

    def post(self, request):
        ser = ChatMessageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        msg = ser.validated_data["message"]
        session_key = (ser.validated_data.get("session_id") or "").strip()[:64]

        result = run_chat(user=request.user, message=msg, session_key=session_key)
        cards = _dedupe_cards(result["cards"])[:15]
        correction = find_correction(
            redacted_message=result.get("redacted_message", ""),
            intent=result["intent"],
        )
        correction_applied = False
        answer_source = {"type": "rule_or_llm", "ref": ""}
        if correction:
            result["reply"] = correction.corrected_reply
            result["llm_used"] = False
            correction_applied = True
            answer_source = {"type": f"correction:{correction.source_type}", "ref": correction.source_ref or str(correction.id)}
            mark_correction_used(correction)
        elif result.get("llm_used"):
            answer_source = {"type": "llm", "ref": ""}
        elif result.get("sources"):
            s0 = result["sources"][0]
            answer_source = {"type": s0.get("type", "rule"), "ref": s0.get("id", "")}

        ev_c = sum(1 for c in cards if c.get("type") == "event")
        com_c = sum(1 for c in cards if c.get("type") == "community")
        ar_c = sum(1 for c in cards if c.get("type") == "area")

        turn = ChatTurn.objects.create(
            user=request.user,
            session_key=session_key,
            intent=result["intent"],
            prompt_sha256=result["prompt_sha256"],
            prompt_length=result["prompt_length"],
            user_message_redacted=result.get("redacted_message", ""),
            assistant_reply=result["reply"],
            cards_json=cards,
            sources_json=result["sources"],
            llm_used=result["llm_used"],
            correction_applied=correction_applied,
            card_event_count=ev_c,
            card_community_count=com_c,
            card_area_count=ar_c,
        )

        return ok(
            {
                "trace_id": str(turn.id),
                "reply": result["reply"],
                "intent": result["intent"],
                "cards": cards,
                "sources": result["sources"],
                "llm_used": result["llm_used"],
                "correction_applied": correction_applied,
                "answer_source": answer_source,
            }
        )


@extend_schema_view(
    post=extend_schema(
        tags=CHAT_TAG,
        summary="Feedback jawaban chat (evaluasi)",
        request=ChatFeedbackSerializer,
        responses=R200,
    ),
)
class ChatFeedbackView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "chat_feedback"

    def post(self, request):
        ser = ChatFeedbackSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        tid = ser.validated_data["trace_id"]
        helpful = ser.validated_data["helpful"]
        turn = ChatTurn.objects.filter(pk=tid, user=request.user).first()
        if not turn:
            return err("NOT_FOUND", "Turn tidak ditemukan", 404)
        turn.helpful = helpful
        turn.feedback_at = timezone.now()
        turn.save(update_fields=["helpful", "feedback_at"])
        return ok(message="Feedback tersimpan")


@extend_schema_view(
    get=extend_schema(
        tags=CHAT_ADMIN_TAG,
        summary="List log chat untuk monitoring/training",
        parameters=[
            q_str("intent", "Filter intent"),
            q_str("helpful", "true / false"),
            q_str("search", "Cari pada user_message_redacted"),
            q_int("limit", "Jumlah item (default 20, max 100)", 20),
            q_int("offset", "Skip N item", 0),
        ],
        responses=R200,
    ),
)
class AdminChatLogsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        limit = clamp_limit(request.query_params.get("limit"), 20)
        offset = clamp_offset(request.query_params.get("offset"))
        intent = (request.query_params.get("intent") or "").strip().lower()
        helpful = request.query_params.get("helpful")
        search = (request.query_params.get("search") or "").strip()
        qs = ChatTurn.objects.select_related("user").order_by("-created_at")
        if intent:
            qs = qs.filter(intent=intent)
        if helpful is not None:
            if helpful.lower() in ("true", "1"):
                qs = qs.filter(helpful=True)
            elif helpful.lower() in ("false", "0"):
                qs = qs.filter(helpful=False)
        if search:
            qs = qs.filter(user_message_redacted__icontains=search)
        total = qs.count()
        rows = list(qs[offset : offset + limit])
        items = []
        for r in rows:
            items.append(
                {
                    "trace_id": str(r.id),
                    "user": {"id": str(r.user_id), "username": r.user.username},
                    "session_id": r.session_key,
                    "intent": r.intent,
                    "user_message_redacted": r.user_message_redacted,
                    "assistant_reply": r.assistant_reply,
                    "helpful": r.helpful,
                    "llm_used": r.llm_used,
                    "correction_applied": r.correction_applied,
                    "cards": r.cards_json,
                    "sources": r.sources_json,
                    "created_at": r.created_at.isoformat().replace("+00:00", "Z") if r.created_at else None,
                }
            )
        return ok({"items": items, "pagination": pagination_meta(total, limit, offset)})

    def delete(self, request):
        """
        Hapus chat logs.
        - by_ids: {"ids": ["uuid1", "uuid2"]}
        - by filter: query params intent/helpful/search
        - all: {"delete_all": true}
        """
        ids = request.data.get("ids") if isinstance(request.data, dict) else None
        delete_all = bool(request.data.get("delete_all")) if isinstance(request.data, dict) else False
        qs = ChatTurn.objects.all()
        if ids:
            qs = qs.filter(id__in=ids)
        elif not delete_all:
            intent = (request.query_params.get("intent") or "").strip().lower()
            helpful = request.query_params.get("helpful")
            search = (request.query_params.get("search") or "").strip()
            if intent:
                qs = qs.filter(intent=intent)
            if helpful is not None:
                if helpful.lower() in ("true", "1"):
                    qs = qs.filter(helpful=True)
                elif helpful.lower() in ("false", "0"):
                    qs = qs.filter(helpful=False)
            if search:
                qs = qs.filter(user_message_redacted__icontains=search)
        count = qs.count()
        if count == 0:
            return ok({"deleted_count": 0}, message="Tidak ada chat log yang dihapus")
        qs.delete()
        return ok({"deleted_count": count}, message="Chat log berhasil dihapus")


@extend_schema_view(
    get=extend_schema(
        tags=CHAT_ADMIN_TAG,
        summary="List rules jawaban koreksi",
        parameters=[
            q_str("intent", "Filter intent"),
            q_str("active", "true / false"),
            q_int("limit", "Jumlah item (default 20, max 100)", 20),
            q_int("offset", "Skip N item", 0),
        ],
        responses=R200,
    ),
    post=extend_schema(
        tags=CHAT_ADMIN_TAG,
        summary="Tambah/replace rule jawaban koreksi",
        request=ChatCorrectionWriteSerializer,
        responses=R200,
    ),
)
class AdminChatCorrectionsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        limit = clamp_limit(request.query_params.get("limit"), 20)
        offset = clamp_offset(request.query_params.get("offset"))
        intent = (request.query_params.get("intent") or "").strip().lower()
        active = request.query_params.get("active")
        qs = ChatAnswerCorrection.objects.order_by("-updated_at")
        if intent:
            qs = qs.filter(intent=intent)
        if active is not None:
            if active.lower() in ("true", "1"):
                qs = qs.filter(is_active=True)
            elif active.lower() in ("false", "0"):
                qs = qs.filter(is_active=False)
        total = qs.count()
        rows = list(qs[offset : offset + limit])
        return ok({"items": [correction_item(r) for r in rows], "pagination": pagination_meta(total, limit, offset)})

    def post(self, request):
        ser = ChatCorrectionWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        v = ser.validated_data
        obj, _ = ChatAnswerCorrection.objects.update_or_create(
            normalized_query=v["normalized_query"],
            defaults={
                "corrected_reply": v["corrected_reply"],
                "source_type": v.get("source_type", "manual"),
                "source_ref": v.get("source_ref", ""),
                "intent": v.get("intent", ""),
                "is_active": v.get("is_active", True),
                "notes": v.get("notes", ""),
                "updated_by": request.user,
                "created_by": request.user,
            },
        )
        return ok({"correction": correction_item(obj)}, message="Rule koreksi tersimpan")


@extend_schema_view(
    patch=extend_schema(
        tags=CHAT_ADMIN_TAG,
        summary="Update rule jawaban koreksi",
        request=ChatCorrectionUpdateSerializer,
        responses=R200,
    ),
)
class AdminChatCorrectionDetailView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, correction_id: str):
        row = ChatAnswerCorrection.objects.filter(pk=correction_id).first()
        if not row:
            return err("NOT_FOUND", "Rule koreksi tidak ditemukan", 404)
        ser = ChatCorrectionUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        v = ser.validated_data
        for f in ("corrected_reply", "intent", "is_active", "notes"):
            if f in v:
                setattr(row, f, v[f])
        row.updated_by = request.user
        row.save()
        return ok({"correction": correction_item(row)}, message="Rule koreksi diperbarui")


@extend_schema_view(
    get=extend_schema(
        tags=CHAT_ADMIN_TAG,
        summary="Daftar template jawaban FAQ",
        responses=R200,
    ),
)
class AdminChatTemplatesView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        templates = list_faq_templates()
        return ok({"templates": templates, "count": len(templates)})

from rest_framework import serializers

from ngumpulyuk_app.chat.models import ChatAnswerCorrection
from ngumpulyuk_app.chat.services.corrections import normalize_query
from ngumpulyuk_app.chat.services.faq import get_faq_by_id


class ChatMessageSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=4000)
    session_id = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")


class ChatFeedbackSerializer(serializers.Serializer):
    trace_id = serializers.UUIDField()
    helpful = serializers.BooleanField()


class ChatCorrectionWriteSerializer(serializers.Serializer):
    normalized_query = serializers.CharField(max_length=500)
    corrected_reply = serializers.CharField(required=False, allow_blank=False)
    use_faq_id = serializers.CharField(required=False, allow_blank=False)
    intent = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")
    is_active = serializers.BooleanField(required=False, default=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_normalized_query(self, value):
        v = normalize_query(value)
        if not v:
            raise serializers.ValidationError("Query tidak boleh kosong.")
        return v

    def validate_intent(self, value):
        v = (value or "").strip().lower()
        allowed = {"", "faq", "event_reco", "community_reco", "place_reco", "general", "greeting", "empty"}
        if v not in allowed:
            raise serializers.ValidationError("Intent tidak valid.")
        return v

    def validate(self, attrs):
        corrected_reply = (attrs.get("corrected_reply") or "").strip()
        use_faq_id = (attrs.get("use_faq_id") or "").strip()
        if not corrected_reply and not use_faq_id:
            raise serializers.ValidationError({"corrected_reply": "Isi corrected_reply atau use_faq_id."})
        if corrected_reply and use_faq_id:
            raise serializers.ValidationError({"use_faq_id": "Pilih salah satu: corrected_reply atau use_faq_id."})
        if use_faq_id:
            faq = get_faq_by_id(use_faq_id)
            if not faq:
                raise serializers.ValidationError({"use_faq_id": "FAQ id tidak ditemukan."})
            attrs["corrected_reply"] = faq["answer"]
            attrs["source_type"] = "faq"
            attrs["source_ref"] = faq["id"]
        else:
            attrs["source_type"] = "manual"
            attrs["source_ref"] = ""
        return attrs


class ChatCorrectionUpdateSerializer(serializers.Serializer):
    corrected_reply = serializers.CharField(required=False)
    intent = serializers.CharField(max_length=32, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_intent(self, value):
        v = (value or "").strip().lower()
        allowed = {"", "faq", "event_reco", "community_reco", "place_reco", "general", "greeting", "empty"}
        if v not in allowed:
            raise serializers.ValidationError("Intent tidak valid.")
        return v


def correction_item(row: ChatAnswerCorrection):
    return {
        "id": str(row.id),
        "normalized_query": row.normalized_query,
        "corrected_reply": row.corrected_reply,
        "intent": row.intent,
        "is_active": row.is_active,
        "notes": row.notes,
        "source_type": row.source_type,
        "source_ref": row.source_ref,
        "usage_count": row.usage_count,
        "last_used_at": row.last_used_at.isoformat().replace("+00:00", "Z") if row.last_used_at else None,
        "created_at": row.created_at.isoformat().replace("+00:00", "Z") if row.created_at else None,
        "updated_at": row.updated_at.isoformat().replace("+00:00", "Z") if row.updated_at else None,
    }

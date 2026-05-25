"""Intent klasifikasi — delegasi ke query_plan agar selaras dengan UI."""

from ngumpulyuk_app.chat.services.query_plan import plan_chat_query


def classify_intent(message_lower: str) -> str:
    return plan_chat_query(message_lower).intent

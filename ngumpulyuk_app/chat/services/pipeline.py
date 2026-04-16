from __future__ import annotations

import hashlib
import random

from django.conf import settings

from ngumpulyuk_app.chat.services.faq import match_faq
from ngumpulyuk_app.chat.services.intent import classify_intent
from ngumpulyuk_app.chat.services.llm_gemini import generate_reply
from ngumpulyuk_app.chat.services.pii import redact_pii
from ngumpulyuk_app.chat.services.retrieval import (
    context_bundle_for_llm,
    fetch_area_cards,
    fetch_community_cards,
    fetch_event_cards,
    fetch_event_cards_by_query,
)


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _rule_reply(*, intent: str, faq_hits: list, has_events: bool, has_communities: bool, has_areas: bool) -> str:
    if intent == "empty":
        return "Kosong nih pesannya bestie 😭 coba ketik apa yang mau ditanya."

    if intent == "greeting":
        opts = [
            "Halo bestie 👋 siap bantu cari event & komunitas. Mau rekomendasi event atau komunitas dulu?",
            "Haiii ✨ lagi nyari vibe kumpul yang pas? Tanya aja soal event, komunitas, atau FAQ singkat.",
        ]
        return random.choice(opts)

    parts = []
    if faq_hits:
        top = faq_hits[0]
        parts.append(f"{top['title']}: {top['answer']}")

    if intent == "event_reco" and has_events:
        parts.append("Di bawah udah aku siapin beberapa event yang relevan — cek card-nya ya.")
    elif intent == "event_reco" and not has_events:
        parts.append("Belum nemu event yang pas di database buat sekarang. Coba ubah minat/lokasi di profil atau cek tab event.")

    if intent == "community_reco" and has_communities:
        parts.append("Nih komunitas yang lagi rame — lihat card-nya.")
    elif intent == "community_reco" and not has_communities:
        parts.append("Belum ada komunitas yang ke-match dari kata kunci kamu. Coba cari di tab komunitas.")

    if intent == "place_reco":
        if has_areas:
            parts.append(
                "Soal 'tempat' di sini aku cuma bisa kasih area dari event yang ada di platform (bukan review venue POI), "
                "biar gak halusinasi nama tempat ngawur ya."
            )
        else:
            parts.append("Belum ada area event yang ke-detect. Cek lagi nanti atau buka tab event.")

    if intent == "general":
        if faq_hits:
            parts.append("Kalau mau lebih spesifik, tanya 'rekomendasi event' atau 'komunitas' biar aku bisa narik data.")
        else:
            parts.append(
                "Aku bisa bantu FAQ singkat, rekomendasi event, komunitas, atau area event. "
                "Coba tanya salah satu itu biar makin kece."
            )

    if intent == "faq" and not parts:
        parts.append("Coba perjelas pertanyaannya (mis. cara daftar, event, atau privasi).")

    return " ".join(parts).strip() or "Coba tanya dengan lebih spesifik ya — aku bantu dari data di app."


def run_chat(*, user, message: str, session_key: str = "") -> dict:
    raw = (message or "").strip()
    if len(raw) > 4000:
        raw = raw[:4000]

    redacted = redact_pii(raw)
    intent = classify_intent(redacted.lower())

    faq_hits = match_faq(redacted.lower(), limit=3)

    cards: list[dict] = []
    event_summaries: list[str] = []
    community_summaries: list[str] = []
    area_names: list[str] = []

    asks_event = any(k in redacted.lower() for k in ("event", "acara", "kegiatan", "agenda"))
    asks_community = any(k in redacted.lower() for k in ("komunitas", "community", "grup"))

    should_show_event_cards = intent == "event_reco" or asks_event
    if should_show_event_cards:
        ev_cards = fetch_event_cards(user, 5)
        if not ev_cards and intent == "event_reco":
            ev_cards = fetch_event_cards_by_query(user, redacted.lower(), 5)
        cards.extend(ev_cards)
        for c in [x for x in cards if x["type"] == "event"]:
            p = c["payload"]
            event_summaries.append(f"{p['id']} | {p['title']} | {p['category']} | {p.get('location_area') or ''}")

    allow_community = intent == "community_reco" or asks_community
    if allow_community:
        com_cards = fetch_community_cards(user, redacted.lower(), 5)
        cards.extend(com_cards)
        for c in com_cards:
            p = c["payload"]
            community_summaries.append(f"{p['id']} | {p['name']} | {p['category']}")

    if intent == "place_reco" or (intent == "general" and any(k in redacted.lower() for k in ("tempat", "lokasi", "dimana", "area"))):
        area_cards = fetch_area_cards(user, 8)
        cards.extend(area_cards)
        area_names = [c["payload"]["name"] for c in area_cards]

    if intent == "faq" or intent == "general":
        pass  # faq_hits only for context

    faq_snippets = [{"title": x["title"], "answer": x["answer"]} for x in faq_hits]

    ctx = context_bundle_for_llm(
        intent=intent,
        faq_snippets=faq_snippets,
        event_summaries=event_summaries,
        community_summaries=community_summaries,
        areas=area_names,
    )

    llm_used = False
    reply = None
    has_grounded_context = bool(event_summaries or community_summaries or area_names)
    can_use_llm = intent not in ("empty",) and (
        has_grounded_context or (intent in ("faq", "general") and bool(faq_snippets))
    )
    if can_use_llm and getattr(settings, "CHAT_LLM_ENABLED", False) and getattr(settings, "CHAT_GEMINI_API_KEY", None):
        reply = generate_reply(user_prompt_for_model=redacted[:2000], context_text=ctx[:12000])
        llm_used = reply is not None

    if not reply:
        reply = _rule_reply(
            intent=intent,
            faq_hits=faq_hits,
            has_events=bool(event_summaries),
            has_communities=bool(community_summaries),
            has_areas=bool(area_names),
        )

    sources = [{"type": "faq", "id": x["id"], "title": x["title"]} for x in faq_hits]
    for s in event_summaries[:5]:
        eid = s.split("|", 1)[0].strip()
        sources.append({"type": "event", "id": eid})
    for s in community_summaries[:5]:
        cid = s.split("|", 1)[0].strip()
        sources.append({"type": "community", "id": cid})

    return {
        "reply": reply,
        "intent": intent,
        "cards": cards,
        "sources": sources[:20],
        "llm_used": llm_used,
        "prompt_sha256": _sha256_hex(redacted) if redacted else "",
        "prompt_length": len(redacted),
        "redacted_message": redacted,
    }

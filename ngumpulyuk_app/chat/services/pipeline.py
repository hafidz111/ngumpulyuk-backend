from __future__ import annotations

import hashlib
import random

from django.conf import settings

from ngumpulyuk_app.chat.services.faq import match_faq
from ngumpulyuk_app.chat.services.llm_gemini import generate_reply
from ngumpulyuk_app.chat.services.pii import redact_pii
from ngumpulyuk_app.chat.services.query_plan import ChatQueryPlan, plan_chat_query
from ngumpulyuk_app.chat.services.retrieval import (
    context_bundle_for_llm,
    fetch_area_cards,
    fetch_community_cards_for_message,
    fetch_event_cards,
    fetch_event_cards_for_message,
)


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _rule_reply(
    *,
    intent: str,
    message_lower: str,
    plan: ChatQueryPlan,
    faq_hits: list,
    has_events: bool,
    has_communities: bool,
    has_areas: bool,
) -> str:
    if intent == "empty":
        return "Kosong nih pesannya 😭 coba ketik apa yang mau ditanya."

    if intent == "greeting":
        opts = [
            "Halo! 👋 Siap bantu cari event atau komunitas. Mau mulai dari yang mana?",
            "Hai! ✨ Lagi nyari kegiatan atau circle baru? Tanya aja — nanti aku kasih card yang relevan.",
        ]
        return random.choice(opts)

    parts = []
    if faq_hits and intent in ("faq", "general"):
        top = faq_hits[0]
        skip_generic_faq = intent == "general" and (
            has_events or has_communities or has_areas
        )
        if not skip_generic_faq:
            parts.append(f"{top['title']}: {top['answer']}")

    if intent == "faq" and not parts:
        parts.append("Coba tanya lebih spesifik, misalnya cara daftar, bikin event, atau privasi akun.")

    if intent == "place_reco":
        if has_events and has_areas:
            parts.append(
                "Ini area & event yang relevan sama lokasi kamu di platform — bukan review venue luar ya, "
                "biar datanya akurat."
            )
        elif has_events:
            parts.append("Ini event di area yang mirip preferensi lokasi kamu — cek card-nya.")
        elif has_areas:
            parts.append("Ini area yang sering dipakai event aktif — pilih area dulu, terus cari event di situ.")
        else:
            parts.append(
                "Belum ada event/area yang ke-detect deket kamu. Coba update lokasi di profil atau buka tab Peta."
            )

    if intent == "event_reco":
        if plan.prefer_weekend and has_events:
            parts.append("Ini rekomendasi event buat weekend ini — scroll card di bawah ya.")
        elif any(k in message_lower for k in ("olahraga", "futsal", "badminton", "sport")) and has_events:
            parts.append("Ini opsi olahraga yang lagi upcoming — lihat card-nya.")
        elif any(k in message_lower for k in ("kreatif", "tema", "seni", "workshop")) and has_events and has_communities:
            parts.append("Yang vibes-nya kreatif: ada event & komunitas di bawah — pilih yang paling cocok.")
        elif any(k in message_lower for k in ("kreatif", "tema", "seni")) and has_communities and not has_events:
            parts.append("Belum ada event kreatif yang ke-match, tapi komunitasnya ada di card bawah.")
        elif has_events:
            parts.append("Ini event yang relevan sama pertanyaan kamu — cek card di bawah.")
        elif has_communities:
            parts.append("Belum ada event pas, tapi ada komunitas terkait — lihat card komunitasnya.")
        else:
            parts.append(
                "Belum ada event yang cocok buat kamu sekarang. Coba tab Explore atau update minat di profil."
            )

    if intent == "community_reco":
        if any(k in message_lower for k in ("aktif", "rame", "ramai")) and has_communities:
            parts.append("Ini komunitas yang lagi aktif di platform — gabung lewat card-nya.")
        elif has_communities:
            parts.append("Ini komunitas yang cocok dari kata kunci kamu — lihat card di bawah.")
        else:
            parts.append("Belum ada komunitas yang ke-match. Coba tab Community atau ubah kata kunci.")

    if intent == "general":
        if has_events and has_communities:
            parts.append("Ini beberapa event & komunitas populer yang bisa kamu cek dulu.")
        elif has_events:
            parts.append("Ini beberapa event yang bisa kamu lihat — pilih lewat card.")
        elif has_communities:
            parts.append("Ini beberapa komunitas yang lagi ada di platform.")
        elif faq_hits:
            parts.append("Kalau mau rekomendasi, tanya misalnya 'event minggu ini' atau 'komunitas yang aktif'.")
        else:
            parts.append(
                "Belum nemu data yang pas. Coba tanya event (mis. olahraga minggu ini), komunitas, "
                "atau 'ada yang deket aku?'."
            )

    return " ".join(parts).strip() or "Coba tanya lebih spesifik ya — aku bantu dari info di NgumpulYuk."


def run_chat(*, user, message: str, session_key: str = "") -> dict:
    raw = (message or "").strip()
    if len(raw) > 4000:
        raw = raw[:4000]

    redacted = redact_pii(raw)
    message_lower = redacted.lower()
    plan = plan_chat_query(message_lower)
    intent = plan.intent

    faq_hits = match_faq(message_lower, limit=3)

    cards: list[dict] = []
    event_summaries: list[str] = []
    community_summaries: list[str] = []
    area_names: list[str] = []

    if plan.fetch_events:
        ev_cards = fetch_event_cards_for_message(
            user,
            message_lower,
            5,
            prefer_nearby=plan.prefer_nearby,
            prefer_weekend=plan.prefer_weekend,
        )
        cards.extend(ev_cards)
        for c in ev_cards:
            p = c["payload"]
            event_summaries.append(
                f"{p['id']} | {p['title']} | {p['category']} | {p.get('location_area') or ''}"
            )

    if plan.fetch_communities:
        com_cards = fetch_community_cards_for_message(user, message_lower, 5)
        cards.extend(com_cards)
        for c in com_cards:
            p = c["payload"]
            community_summaries.append(f"{p['id']} | {p['name']} | {p['category']}")

    if plan.fetch_areas:
        area_cards = fetch_area_cards(user, 8, prefer_nearby=plan.prefer_nearby)
        cards.extend(area_cards)
        area_names = [c["payload"]["name"] for c in area_cards]

    if intent == "general" and not cards:
        for card in fetch_event_cards(user, 3):
            cards.append(card)
            p = card["payload"]
            event_summaries.append(
                f"{p['id']} | {p['title']} | {p['category']} | {p.get('location_area') or ''}"
            )
        for card in fetch_community_cards_for_message(user, message_lower, 3):
            cards.append(card)
            p = card["payload"]
            community_summaries.append(f"{p['id']} | {p['name']} | {p['category']}")

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
    can_use_llm = intent not in ("empty", "greeting") and (
        has_grounded_context or (intent == "faq" and bool(faq_snippets))
    )
    if can_use_llm and getattr(settings, "CHAT_LLM_ENABLED", False) and getattr(settings, "CHAT_GEMINI_API_KEY", None):
        reply = generate_reply(user_prompt_for_model=redacted[:2000], context_text=ctx[:12000])
        llm_used = reply is not None

    if not reply:
        reply = _rule_reply(
            intent=intent,
            message_lower=message_lower,
            plan=plan,
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

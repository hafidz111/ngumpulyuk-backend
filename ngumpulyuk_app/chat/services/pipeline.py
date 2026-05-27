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


def _faq_reply_text(hit: dict) -> str:
    answer = (hit.get("answer") or "").strip()
    if answer:
        return answer
    return (hit.get("title") or "").strip()


def _join_reply_parts(parts: list[str], *, max_parts: int = 2) -> str:
    cleaned = [p.strip() for p in parts if p and p.strip()]
    if not cleaned:
        return ""
    return " ".join(cleaned[:max_parts]).strip()


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
        return "Kosong nih pesannya. Coba ketik mau cari event, circle, atau tanya cara pakai app."

    if intent == "greeting":
        opts = [
            "Hai! Gue Ngumpsky. Mau cari event, circle, atau tanya cara pakai app? Ketik aja, nanti gue kasih jawaban plus card kalau ada datanya.",
            "Halo! Siap bantu dari data NgumpulYuk. Tanya event, komunitas, atau yang deket lokasi kamu.",
        ]
        return random.choice(opts)

    if intent == "ack":
        opts = [
            "Siapp, kalau mau lanjut tinggal drop detailnya ya. Misal: event olahraga di Bandung weekend ini.",
            "Oke gas. Mau gue cariin event, komunitas, atau yang deket lokasimu?",
        ]
        return random.choice(opts)

    parts: list[str] = []
    if faq_hits and intent in ("faq", "general"):
        skip_generic_faq = intent == "general" and (
            has_events or has_communities or has_areas
        )
        if not skip_generic_faq:
            parts.append(_faq_reply_text(faq_hits[0]))

    if intent == "faq" and not parts:
        parts.append(
            "Coba lebih spesifik ya, misalnya cara daftar, bikin event, join circle, atau privasi akun."
        )

    if intent == "place_reco":
        if has_events and has_areas:
            parts.append(
                "Ini event dan area dari data NgumpulYuk yang relevan sama lokasi kamu. Cek card-nya ya."
            )
        elif has_events:
            parts.append("Ini event yang area-nya mirip preferensi kamu. Lihat card di bawah.")
        elif has_areas:
            parts.append(
                "Ini area yang sering dipakai event aktif. Pilih area dulu, terus cari event di situ."
            )
        else:
            parts.append(
                "Belum nemu event atau area yang pas. Coba update lokasi di profil atau buka tab Peta."
            )

    if intent == "event_reco":
        ask_volleyball = any(k in message_lower for k in ("voli", "volly", "volleyball"))
        if ask_volleyball and not has_events:
            parts.append(
                "Untuk event voli/volly, sekarang belum ada yang match di data. Coba cek kategori olahraga lain dulu ya, bestie."
            )
        elif ask_volleyball and has_events:
            parts.append("Nih event voli/volly yang ke-detect dari judul/deskripsi. Cek card di bawah ya.")
        elif plan.prefer_weekend and has_events:
            parts.append("Ini event yang cocok buat weekend ini. Scroll card di bawah.")
        elif any(k in message_lower for k in ("olahraga", "futsal", "badminton", "sport")) and has_events:
            parts.append("Ini opsi olahraga yang masih upcoming. Cek card-nya.")
        elif any(k in message_lower for k in ("kreatif", "tema", "seni", "workshop")) and has_events:
            parts.append("Ini event yang vibes-nya kreatif. Pilih lewat card di bawah.")
        elif any(k in message_lower for k in ("kreatif", "tema", "seni")) and has_communities and not has_events:
            parts.append("Event kreatif belum ketemu, tapi ada circle terkait di card bawah.")
        elif has_events:
            parts.append("Ini event yang relevan sama pertanyaan kamu. Cek card di bawah.")
        elif has_communities:
            parts.append("Event pas belum ada, tapi ada circle terkait di card komunitas.")
        else:
            parts.append(
                "Belum ada event yang cocok sekarang. Coba tab Explore atau perjelas kata kuncinya."
            )

    if intent == "community_reco":
        if any(k in message_lower for k in ("aktif", "rame", "ramai")) and has_communities:
            parts.append("Ini circle yang lagi aktif. Gabung lewat card di bawah.")
        elif has_communities:
            parts.append("Ini komunitas yang cocok dari kata kunci kamu. Lihat card di bawah.")
        else:
            parts.append("Belum ada circle yang ke-match. Coba tab Komunitas atau ubah kata kuncinya.")

    if intent == "general":
        if has_events and has_communities:
            parts.append("Ini beberapa event dan circle yang bisa kamu cek dulu lewat card.")
        elif has_events:
            parts.append("Ini beberapa event yang bisa kamu lihat lewat card di bawah.")
        elif has_communities:
            parts.append("Ini beberapa komunitas yang ada di platform. Cek card-nya.")
        elif faq_hits:
            parts.append("Kalau mau rekomendasi, coba tanya event minggu ini atau circle yang aktif.")
        else:
            parts.append(
                "Belum nemu data yang pas. Coba tanya event, komunitas, atau ada yang deket lokasi kamu."
            )

    joined = _join_reply_parts(parts, max_parts=2)
    return joined or "Coba tanya lebih spesifik ya. Gue jawab dari data event dan circle di NgumpulYuk."


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
    can_use_llm = intent not in ("empty", "greeting") and not faq_hits
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

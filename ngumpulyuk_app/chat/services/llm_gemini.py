from __future__ import annotations

import json
import logging
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_reply(*, user_prompt_for_model: str, context_text: str) -> Optional[str]:
    """
    Panggilan Gemini (free tier API key dari Google AI Studio).
    Hanya teks yang sudah diredaksi & context terkurasi — jangan kirim email/nama asli user.
    """
    if not getattr(settings, "CHAT_LLM_ENABLED", False):
        return None
    api_key = getattr(settings, "CHAT_GEMINI_API_KEY", None) or None
    if not api_key:
        return None
    model = getattr(settings, "CHAT_GEMINI_MODEL", "gemini-2.0-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    system = (
        "Kamu Ngumpsky, asisten NgumpulYuk. Jawab HANYA dari KONTEKS. Bahasa Indonesia, gaya Gen Z "
        "yang catchy dan hangat (2-4 kalimat, friendly, pakai gue/aku, copywriting ringan). "
        "Jangan sebut data pribadi. Jika ada event/komunitas/area di konteks, arahkan user cek card "
        "di bawah chat — jangan mengarang detail di luar konteks. Kalau user minta lokasi/kota tertentu "
        "dan konteks tidak punya hasil yang pas, bilang jujur bahwa hasil belum ketemu di area itu dan "
        "minta user perjelas area terdekat. Jika konteks tidak cukup, sarankan Explore atau Peta. "
        "Jangan format FAQ seperti 'Judul: jawaban'. Jangan sebut database, server, API, atau istilah teknis. "
        "Jika informasi tidak cukup yakin, prioritaskan klarifikasi singkat daripada memberikan asumsi."
        "Output JSON valid satu objek: {\"reply\": \"...\"} tanpa markdown."
    )
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": "KONTEKS:\n"
                        + context_text
                        + "\n\nPERTANYAAN USER (boleh gaul, isi sudah aman):\n"
                        + user_prompt_for_model
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.35,
            "maxOutputTokens": 512,
            "responseMimeType": "application/json",
        },
    }
    try:
        r = requests.post(
            url,
            params={"key": api_key},
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=25,
        )
        if r.status_code != 200:
            logger.warning("Gemini HTTP %s: %s", r.status_code, r.text[:500])
            return None
        data = r.json()
        parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts") or []
        raw = (parts[0].get("text") or "").strip()
        if not raw:
            return None
        obj = json.loads(raw)
        reply = (obj.get("reply") or "").strip()
        return reply or None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini call failed: %s", exc)
        return None

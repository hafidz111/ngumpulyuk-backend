import re


_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    re.I,
)
# Angka panjang seperti nomor telepon Indonesia / kartu
_PHONEISH_RE = re.compile(r"\b(?:\+62|62|0)\d{9,13}\b|\b\d{10,16}\b")


def redact_pii(text: str) -> str:
    if not text:
        return ""
    out = _EMAIL_RE.sub("[email-diredaksi]", text)
    out = _PHONEISH_RE.sub("[nomor-diredaksi]", out)
    return out

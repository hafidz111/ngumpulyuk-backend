"""
Pengiriman email OTP.

- Development: SMTP (Mailtrap / Gmail lokal).
- Production di Render: port 587/465 sering diblokir (Errno 101) — set RESEND_API_KEY
  atau EMAIL_BACKEND_PROVIDER=resend (HTTPS, tidak diblokir).
"""
from __future__ import annotations

import logging

import requests
from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


class EmailDeliveryError(Exception):
    """Gagal mengirim email."""


def _is_smtp_network_blocked(exc: BaseException) -> bool:
    if getattr(exc, "errno", None) == 101:
        return True
    msg = str(exc).lower()
    return "network is unreachable" in msg or "network unreachable" in msg


def resolve_delivery_backend() -> str:
    """@returns 'resend' | 'smtp'"""
    provider = (getattr(settings, "EMAIL_BACKEND_PROVIDER", None) or "auto").strip().lower()
    has_resend = bool((getattr(settings, "RESEND_API_KEY", None) or "").strip())

    if provider == "resend":
        if not has_resend:
            raise EmailDeliveryError("RESEND_API_KEY belum di-set di environment.")
        return "resend"
    if provider == "smtp":
        return "smtp"

    if getattr(settings, "DJANGO_ENV", "") == "production" and has_resend:
        return "resend"
    return "smtp"


def send_html_email(*, from_email, to_email, subject, plain_body, html_body):
    backend = resolve_delivery_backend()
    if backend == "resend":
        _send_via_resend(
            from_email=from_email,
            to_email=to_email,
            subject=subject,
            plain_body=plain_body,
            html_body=html_body,
        )
        return
    _send_via_smtp(
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        plain_body=plain_body,
        html_body=html_body,
    )


def _send_via_resend(*, from_email, to_email, subject, plain_body, html_body):
    api_key = (settings.RESEND_API_KEY or "").strip()
    if not api_key:
        raise EmailDeliveryError("RESEND_API_KEY tidak dikonfigurasi.")

    try:
        response = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_body,
                "text": plain_body,
            },
            timeout=20,
        )
    except requests.RequestException as exc:
        logger.exception("Resend request gagal ke %s", to_email)
        raise EmailDeliveryError(f"Resend tidak terjangkau: {exc}") from exc

    if response.status_code >= 400:
        logger.error("Resend %s: %s", response.status_code, response.text)
        raise EmailDeliveryError(
            f"Resend menolak pengiriman ({response.status_code}). "
            "Pastikan domain/alamat From sudah diverifikasi di dashboard Resend."
        )

    logger.info("Email terkirim via Resend from=%s to=%s", from_email, to_email)


def _send_via_smtp(*, from_email, to_email, subject, plain_body, html_body):
    if not (getattr(settings, "EMAIL_HOST_USER", None) or "").strip():
        raise EmailDeliveryError("EMAIL_HOST_USER tidak dikonfigurasi.")
    if not (getattr(settings, "EMAIL_HOST_PASSWORD", None) or "").strip():
        raise EmailDeliveryError(
            "EMAIL_HOST_PASSWORD tidak dikonfigurasi (gunakan Gmail App Password)."
        )

    message = EmailMultiAlternatives(
        subject=subject,
        body=plain_body,
        from_email=from_email,
        to=[to_email],
    )
    message.attach_alternative(html_body, "text/html")

    fail_silently = getattr(settings, "DJANGO_ENV", "") != "production"
    try:
        sent = message.send(fail_silently=fail_silently)
    except OSError as exc:
        logger.exception("SMTP gagal from=%s to=%s", from_email, to_email)
        if _is_smtp_network_blocked(exc):
            has_resend = bool((getattr(settings, "RESEND_API_KEY", None) or "").strip())
            if getattr(settings, "DJANGO_ENV", "") == "production" and not has_resend:
                raise EmailDeliveryError(
                    "SMTP diblokir dari server production (Render, Errno 101). "
                    "Bukan salah App Password — tambahkan RESEND_API_KEY di environment, "
                    "atau jalankan backend di host yang mengizinkan port 587."
                ) from exc
        raise EmailDeliveryError(
            f"SMTP gagal: {exc}. Periksa EMAIL_HOST_USER/PASSWORD (App Password) dan EMAIL_PORT."
        ) from exc
    except Exception as exc:
        logger.exception("SMTP gagal from=%s to=%s", from_email, to_email)
        raise EmailDeliveryError(str(exc)) from exc

    if sent == 0 and not fail_silently:
        raise EmailDeliveryError("SMTP tidak mengirim pesan (sent=0).")

    logger.info("Email terkirim via SMTP from=%s to=%s", from_email, to_email)


def send_simple_email(*, from_email, to_email, subject, body):
    backend = resolve_delivery_backend()
    if backend == "resend":
        _send_via_resend(
            from_email=from_email,
            to_email=to_email,
            subject=subject,
            plain_body=body,
            html_body=f"<pre style='font-family:sans-serif'>{body}</pre>",
        )
        return

    msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=[to_email],
    )
    fail_silently = getattr(settings, "DJANGO_ENV", "") != "production"
    try:
        msg.send(fail_silently=fail_silently)
    except OSError as exc:
        if _is_smtp_network_blocked(exc):
            raise EmailDeliveryError(
                "SMTP diblokir dari server production. Set RESEND_API_KEY di Render."
            ) from exc
        raise EmailDeliveryError(str(exc)) from exc

"""
Pengiriman email OTP.

Render (dan banyak PaaS) memblokir outbound SMTP (port 587) → Errno 101 Network unreachable.
Production: set RESEND_API_KEY dan verifikasi domain di https://resend.com
Development: SMTP Mailtrap tetap dipakai jika RESEND_API_KEY kosong.
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


def resolve_delivery_backend():
    """
    @returns {'resend' | 'smtp'}
    """
    provider = (getattr(settings, "EMAIL_BACKEND_PROVIDER", None) or "auto").strip().lower()
    has_resend = bool((getattr(settings, "RESEND_API_KEY", None) or "").strip())

    if provider == "resend":
        if not has_resend:
            raise EmailDeliveryError("RESEND_API_KEY belum di-set di environment.")
        return "resend"
    if provider == "smtp":
        return "smtp"

    if getattr(settings, "DJANGO_ENV", "") == "production":
        if has_resend:
            return "resend"
        logger.warning(
            "Production tanpa RESEND_API_KEY: SMTP Gmail sering gagal di Render (port 587 diblokir)."
        )
    return "resend" if has_resend else "smtp"


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
        raise EmailDeliveryError("EMAIL_HOST_PASSWORD tidak dikonfigurasi.")

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
        if getattr(exc, "errno", None) == 101 or "Network is unreachable" in str(exc):
            raise EmailDeliveryError(
                "SMTP diblokir dari server production (Render). "
                "Tambahkan RESEND_API_KEY di environment backend."
            ) from exc
        logger.exception("SMTP gagal from=%s to=%s", from_email, to_email)
        raise EmailDeliveryError(str(exc)) from exc
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
        if getattr(exc, "errno", None) == 101:
            raise EmailDeliveryError(
                "SMTP diblokir di production. Set RESEND_API_KEY di Render."
            ) from exc
        raise EmailDeliveryError(str(exc)) from exc

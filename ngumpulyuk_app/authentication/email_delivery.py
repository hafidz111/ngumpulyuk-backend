"""
Pengiriman email OTP via Django SMTP.

Production: smtp.gmail.com + App Password (settings EMAIL_HOST_*).
Development: Mailtrap (sandbox.smtp.mailtrap.io).
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    """Gagal mengirim email."""


def send_html_email(*, from_email, to_email, subject, plain_body, html_body):
    _send_via_smtp(
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        plain_body=plain_body,
        html_body=html_body,
    )


def _send_via_smtp(*, from_email, to_email, subject, plain_body, html_body):
    if not (getattr(settings, "EMAIL_HOST_USER", None) or "").strip():
        raise EmailDeliveryError("EMAIL_HOST_USER tidak dikonfigurasi.")
    if not (getattr(settings, "EMAIL_HOST_PASSWORD", None) or "").strip():
        raise EmailDeliveryError("EMAIL_HOST_PASSWORD tidak dikonfigurasi (gunakan Gmail App Password).")

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
        raise EmailDeliveryError(
            f"SMTP gagal: {exc}. Pastikan EMAIL_HOST_USER/PASSWORD (App Password) benar."
        ) from exc
    except Exception as exc:
        logger.exception("SMTP gagal from=%s to=%s", from_email, to_email)
        raise EmailDeliveryError(str(exc)) from exc

    if sent == 0 and not fail_silently:
        raise EmailDeliveryError("SMTP tidak mengirim pesan (sent=0).")

    logger.info("Email terkirim via SMTP from=%s to=%s", from_email, to_email)


def send_simple_email(*, from_email, to_email, subject, body):
    msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=[to_email],
    )
    fail_silently = getattr(settings, "DJANGO_ENV", "") != "production"
    try:
        msg.send(fail_silently=fail_silently)
    except Exception as exc:
        logger.exception("SMTP gagal from=%s to=%s", from_email, to_email)
        raise EmailDeliveryError(str(exc)) from exc

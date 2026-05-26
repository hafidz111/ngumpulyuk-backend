import logging
import random
from email.utils import formataddr, parseaddr

from django.conf import settings
from django.contrib.auth.models import update_last_login
from .email_delivery import EmailDeliveryError, send_html_email, send_simple_email
from .models import OneTimePassword, User

logger = logging.getLogger(__name__)

OTP_EMAIL_SUBJECT = "Kode verifikasi NgumpulYuk"
PASSWORD_RESET_EMAIL_SUBJECT = "Reset kata sandi NgumpulYuk"

# Selaras dengan ngumpulyuk-frontend/src/index.css & auth-split-layout
BRAND_PRIMARY = "#FF8000"
BRAND_PRIMARY_FG = "#FFF9F5"
BRAND_SECONDARY = "#F5C842"
BRAND_BG = "#F5F5F7"
BRAND_SURFACE = "#FFFAF5"
BRAND_CARD = "#FFFFFF"
BRAND_FOREGROUND = "#302A24"
BRAND_MUTED = "#6B6359"
BRAND_BORDER = "#A8A29E"
FONT_BODY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
FONT_DISPLAY = "'Plus Jakarta Sans', Inter, sans-serif"


class OtpEmailDeliveryError(EmailDeliveryError):
    """Gagal mengirim OTP."""


class PasswordResetEmailDeliveryError(EmailDeliveryError):
    """Gagal mengirim email reset password."""


def get_from_email():
    """
    From header: "NgumpulYuk" <info@ngumpulyuk.id>
    Alamat SMTP tetap DEFAULT_FROM_EMAIL; nama dari EMAIL_FROM_NAME.
    """
    raw = (settings.DEFAULT_FROM_EMAIL or "").strip()
    if not raw:
        return ""

    configured_name = (getattr(settings, "EMAIL_FROM_NAME", None) or "").strip()
    parsed_name, addr = parseaddr(raw)
    if not addr:
        addr = raw
        parsed_name = ""

    display_name = configured_name or parsed_name or "NgumpulYuk"
    return formataddr((display_name, addr))


def record_user_login(user, request=None):
    if user is None or not getattr(user, "is_active", True):
        return
    update_last_login(sender=type(user), user=user, request=request)


def generateOtp():
    otp = ""
    for _ in range(6):
        otp += str(random.randint(1, 9))
    return otp


def issue_otp_for_user(email):
    user = User.objects.get(email=email)
    otp_code = generateOtp()
    OneTimePassword.objects.filter(user=user).delete()
    OneTimePassword.objects.create(user=user, code=otp_code)
    return otp_code, user


def _verify_email_url():
    site = getattr(settings, "FRONTEND_URL", "").rstrip("/")
    if not site:
        return ""
    return f"{site}/verify-email"


def _display_name(full_name):
    name = (full_name or "").strip()
    return name if name else "kamu"


def _otp_email_plain(full_name, otp_code, recipient_email):
    verify_url = _verify_email_url()
    lines = [
        "NgumpulYuk — Verifikasi email",
        "",
        f"Halo {_display_name(full_name)},",
        "",
        f"Masukkan kode OTP berikut di halaman verifikasi NgumpulYuk.",
        f"Kode dikirim untuk: {recipient_email}",
        "",
        f"Kode OTP: {otp_code}",
        "",
    ]
    if verify_url:
        lines.append(f"Buka halaman verifikasi: {verify_url}")
    lines.extend(
        [
            "",
            "Kode berlaku sampai kamu meminta kode baru.",
            "Bukan kamu yang mendaftar? Abaikan email ini.",
            "",
            "Chat-first. Event & komunitas lewat Ngumpsky.",
            "— NgumpulYuk",
        ]
    )
    return "\n".join(lines)


def _otp_email_html(full_name, otp_code, recipient_email):
    greeting = _display_name(full_name)
    verify_url = _verify_email_url()
    otp_spaced = " ".join(otp_code)

    cta_block = ""
    if verify_url:
        cta_block = f"""
          <tr>
            <td align="center" style="padding: 4px 32px 28px;">
              <a href="{verify_url}"
                 style="display: inline-block; background: {BRAND_PRIMARY}; color: {BRAND_PRIMARY_FG};
                        text-decoration: none; font-family: {FONT_BODY}; font-weight: 600; font-size: 15px;
                        padding: 14px 32px; border-radius: 999px;
                        box-shadow: 0 10px 28px rgba(255, 128, 0, 0.35);">
                Verifikasi
              </a>
            </td>
          </tr>"""

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Kode verifikasi NgumpulYuk</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Plus+Jakarta+Sans:wght@700;800&display=swap" rel="stylesheet">
</head>
<body style="margin:0; padding:0; background:{BRAND_BG}; font-family: {FONT_BODY}; color: {BRAND_FOREGROUND};">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:{BRAND_BG}; padding: 32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
               style="max-width: 440px; background: {BRAND_CARD}; border-radius: 28px; overflow: hidden;
                      box-shadow: 0 8px 40px -4px rgba(48, 42, 36, 0.12);">
          <tr>
            <td style="background: {BRAND_PRIMARY}; padding: 24px 28px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td style="width: 44px; vertical-align: middle;">
                    <div style="width: 44px; height: 44px; border-radius: 16px; background: rgba(255,255,255,0.2);
                                text-align: center; line-height: 44px; font-size: 20px;">✦</div>
                  </td>
                  <td style="padding-left: 12px; vertical-align: middle;">
                    <p style="margin: 0; font-family: {FONT_DISPLAY}; font-size: 20px; font-weight: 800;
                              letter-spacing: -0.02em; color: #ffffff;">NgumpulYuk</p>
                    <p style="margin: 4px 0 0; font-size: 12px; line-height: 1.4; color: rgba(255,255,255,0.9);">
                      Chat-first · Ngumpsky
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding: 32px 28px 8px; text-align: center;">
              <h1 style="margin: 0; font-family: {FONT_DISPLAY}; font-size: 24px; font-weight: 700;
                         letter-spacing: -0.02em; color: {BRAND_FOREGROUND}; line-height: 1.25;">
                Verifikasi email
              </h1>
              <p style="margin: 12px 0 0; font-size: 14px; line-height: 1.6; color: {BRAND_MUTED};">
                Halo <strong style="color:{BRAND_FOREGROUND};">{greeting}</strong> —
                masukkan kode OTP yang dikirim ke
                <strong style="color:{BRAND_PRIMARY};">{recipient_email}</strong>.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding: 20px 28px 8px; text-align: center;">
              <p style="margin: 0 0 10px; font-size: 13px; font-weight: 600; color: {BRAND_FOREGROUND};">
                Kode OTP
              </p>
              <div style="background: rgba(255, 128, 0, 0.1); border: 1px solid rgba(255, 128, 0, 0.3);
                          border-radius: 999px; padding: 16px 20px; display: inline-block; min-width: 200px;">
                <p style="margin: 0; font-size: 28px; font-weight: 700; letter-spacing: 0.28em;
                          color: {BRAND_FOREGROUND}; font-family: ui-monospace, 'SF Mono', Menlo, monospace;">
                  {otp_spaced}
                </p>
              </div>
            </td>
          </tr>
          {cta_block}
          <tr>
            <td style="padding: 8px 28px 28px; text-align: center;">
              <p style="margin: 0; font-size: 13px; line-height: 1.55; color: {BRAND_MUTED};">
                Tidak dapat kode? Gunakan <strong>Kirim ulang kode</strong> di halaman verifikasi.<br>
                Kode berlaku sampai kamu meminta yang baru.
              </p>
            </td>
          </tr>
          <tr>
            <td style="background: {BRAND_SURFACE}; padding: 16px 28px; text-align: center;
                       border-top: 1px solid rgba(168, 162, 158, 0.35);">
              <p style="margin: 0; font-size: 12px; line-height: 1.5; color: {BRAND_MUTED};">
                Bukan kamu yang mendaftar? Abaikan email ini.<br>
                <span style="color:{BRAND_SECONDARY};">●</span>
                Event &amp; komunitas lewat Ngumpsky
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _password_reset_email_plain(full_name, recipient_email, reset_link):
    lines = [
        "NgumpulYuk — Reset kata sandi",
        "",
        f"Halo {_display_name(full_name)},",
        "",
        "Kamu minta reset password buat akun NgumpulYuk.",
        f"Email: {recipient_email}",
        "",
        "Klik link ini buat bikin password baru:",
        reset_link,
        "",
        "Link cuma buat kamu — jangan share ke siapa pun.",
        "Kalau kamu nggak minta reset, abaikan aja email ini.",
        "",
        "Chat-first. Event & komunitas lewat Ngumpsky.",
        "— NgumpulYuk",
    ]
    return "\n".join(lines)


def _password_reset_email_html(full_name, recipient_email, reset_link):
    greeting = _display_name(full_name)

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Reset kata sandi NgumpulYuk</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Plus+Jakarta+Sans:wght@700;800&display=swap" rel="stylesheet">
</head>
<body style="margin:0; padding:0; background:{BRAND_BG}; font-family: {FONT_BODY}; color: {BRAND_FOREGROUND};">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:{BRAND_BG}; padding: 32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
               style="max-width: 440px; background: {BRAND_CARD}; border-radius: 28px; overflow: hidden;
                      box-shadow: 0 8px 40px -4px rgba(48, 42, 36, 0.12);">
          <tr>
            <td style="background: {BRAND_PRIMARY}; padding: 24px 28px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td style="width: 44px; vertical-align: middle;">
                    <div style="width: 44px; height: 44px; border-radius: 16px; background: rgba(255,255,255,0.2);
                                text-align: center; line-height: 44px; font-size: 20px;">✦</div>
                  </td>
                  <td style="padding-left: 12px; vertical-align: middle;">
                    <p style="margin: 0; font-family: {FONT_DISPLAY}; font-size: 20px; font-weight: 800;
                              letter-spacing: -0.02em; color: #ffffff;">NgumpulYuk</p>
                    <p style="margin: 4px 0 0; font-size: 12px; line-height: 1.4; color: rgba(255,255,255,0.9);">
                      Chat-first · Ngumpsky
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding: 32px 28px 8px; text-align: center;">
              <h1 style="margin: 0; font-family: {FONT_DISPLAY}; font-size: 24px; font-weight: 700;
                         letter-spacing: -0.02em; color: {BRAND_FOREGROUND}; line-height: 1.25;">
                Reset kata sandi
              </h1>
              <p style="margin: 12px 0 0; font-size: 14px; line-height: 1.6; color: {BRAND_MUTED};">
                Halo <strong style="color:{BRAND_FOREGROUND};">{greeting}</strong> —
                kamu minta reset password buat akun
                <strong style="color:{BRAND_PRIMARY};">{recipient_email}</strong>.
                Tap tombol di bawah buat set password baru.
              </p>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding: 20px 28px 8px;">
              <a href="{reset_link}"
                 style="display: inline-block; background: {BRAND_PRIMARY}; color: {BRAND_PRIMARY_FG};
                        text-decoration: none; font-family: {FONT_BODY}; font-weight: 600; font-size: 15px;
                        padding: 14px 32px; border-radius: 999px;
                        box-shadow: 0 10px 28px rgba(255, 128, 0, 0.35);">
                Reset kata sandi
              </a>
            </td>
          </tr>
          <tr>
            <td style="padding: 8px 28px 28px; text-align: center;">
              <p style="margin: 0 0 12px; font-size: 13px; line-height: 1.55; color: {BRAND_MUTED};">
                Tombol nggak jalan? Salin link ini ke browser kamu:
              </p>
              <p style="margin: 0; font-size: 12px; line-height: 1.5; word-break: break-all;
                        color: {BRAND_PRIMARY}; font-weight: 600;">
                {reset_link}
              </p>
            </td>
          </tr>
          <tr>
            <td style="background: {BRAND_SURFACE}; padding: 16px 28px; text-align: center;
                       border-top: 1px solid rgba(168, 162, 158, 0.35);">
              <p style="margin: 0; font-size: 12px; line-height: 1.5; color: {BRAND_MUTED};">
                Bukan kamu yang minta reset? Abaikan email ini.<br>
                <span style="color:{BRAND_SECONDARY};">●</span>
                Event &amp; komunitas lewat Ngumpsky
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def deliver_password_reset_email(user, reset_link):
    """
    Kirim email reset password (HTML + plain) dengan template selaras OTP.
    Raises PasswordResetEmailDeliveryError jika pengiriman gagal.
    """
    email_from = get_from_email()
    if not email_from:
        raise PasswordResetEmailDeliveryError("DEFAULT_FROM_EMAIL tidak dikonfigurasi.")

    to_email = user.email
    full_name = user.full_name or ""

    try:
        send_html_email(
            from_email=email_from,
            to_email=to_email,
            subject=PASSWORD_RESET_EMAIL_SUBJECT,
            plain_body=_password_reset_email_plain(full_name, to_email, reset_link),
            html_body=_password_reset_email_html(full_name, to_email, reset_link),
        )
    except EmailDeliveryError as exc:
        raise PasswordResetEmailDeliveryError(str(exc)) from exc


def deliver_otp_to_user(email):
    """
    Simpan OTP lalu kirim email via SMTP (Gmail di production, Mailtrap di development).
    Raises OtpEmailDeliveryError jika pengiriman gagal.
    """
    email_from = get_from_email()
    if not email_from:
        raise OtpEmailDeliveryError("DEFAULT_FROM_EMAIL tidak dikonfigurasi.")

    otp_code, user = issue_otp_for_user(email)
    full_name = user.full_name or ""

    try:
        send_html_email(
            from_email=email_from,
            to_email=email,
            subject=OTP_EMAIL_SUBJECT,
            plain_body=_otp_email_plain(full_name, otp_code, email),
            html_body=_otp_email_html(full_name, otp_code, email),
        )
    except EmailDeliveryError as exc:
        raise OtpEmailDeliveryError(str(exc)) from exc

    return otp_code


def send_code_to_user(email):
    deliver_otp_to_user(email)


def enqueue_send_code_to_user(email):
    deliver_otp_to_user(email)


def send_normal_email(data):
    email_from = get_from_email()
    try:
        send_simple_email(
            from_email=email_from,
            to_email=data["to_email"],
            subject=data["email_subject"],
            body=data["email_body"],
        )
    except EmailDeliveryError:
        if getattr(settings, "DJANGO_ENV", "") == "production":
            raise
        logger.exception("Gagal kirim email (development)")

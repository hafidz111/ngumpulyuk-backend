import random

from django.conf import settings
from django.contrib.auth.models import update_last_login
from django.core.mail import EmailMessage

from .models import OneTimePassword, User


def record_user_login(user, request=None):
    """
    Perbarui User.last_login setelah autentikasi berhasil.
    Login JWT tidak memanggil django.contrib.auth.login(), jadi field ini
    tidak ter-update otomatis tanpa helper ini.
    """
    if user is None or not getattr(user, "is_active", True):
        return
    update_last_login(sender=type(user), user=user, request=request)


def _outgoing_from_email():
    """
    Production: show brand address (must match send-as / domain policy of SMTP).
    Development: use sandbox SMTP identity (e.g. Mailtrap username).
    """
    if getattr(settings, "DJANGO_ENV", "") == "production":
        return settings.DEFAULT_FROM_EMAIL
    return settings.EMAIL_HOST_USER


def generateOtp():
    otp=''
    for i in range(6):
        otp += str(random.randint(1,9))
    return otp

def send_code_to_user(email):
    Subject='One time passcode for Email Verification'
    otp_code=generateOtp()
    # print(otp_code)
    user=User.objects.get(email=email)
    current_site='myAuth.com'
    email_body=f'Hi {user.full_name} thanks for signing up on {current_site} please verify your email with the \n one time passcode {otp_code}'
    from_email = _outgoing_from_email()

    OneTimePassword.objects.filter(user=user).delete()
    OneTimePassword.objects.create(user=user, code=otp_code)
    d_email=EmailMessage(subject=Subject, body=email_body, from_email=from_email, to=[email])
    d_email.send(fail_silently=True)

def send_normal_email(data):
    email=EmailMessage(
        subject=data['email_subject'],
        body=data['email_body'],
        from_email=_outgoing_from_email(),
        to=[data['to_email']]
    )
    email.send()
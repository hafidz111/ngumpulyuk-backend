from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import smart_str, smart_bytes, force_str
from django.urls import reverse
from .utils import send_normal_email
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.conf import settings
class UserRegisterSerializer(serializers.ModelSerializer):
    password=serializers.CharField(max_length=68, min_length=6, write_only=True)
    password_confirm=serializers.CharField(max_length=68, min_length=6, write_only=True)
    
    class Meta:
        model=User
        fields=['email', 'full_name', 'password', 'password_confirm']

    def validate(self, attrs):
        password=attrs.get('password', '')
        password_confirm=attrs.get('password_confirm', '')
        if password != password_confirm:
            raise serializers.ValidationError('Password tidak sesuai')
        return attrs
    
    def create(self, validated_data):
        user=User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data.get('full_name'),
            password=validated_data.get('password')
        )

        return user
    
class VerifyEmailSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, min_length=4)


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

class LoginSerializer(serializers.ModelSerializer):
    email=serializers.EmailField(max_length=255, min_length=6)
    password=serializers.CharField(max_length=68, write_only=True)
    full_name=serializers.CharField(max_length=255, read_only=True)
    onboarding_completed=serializers.BooleanField(read_only=True)
    access_token=serializers.CharField(max_length=255, read_only=True)
    refresh_token=serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model=User
        fields=['email', 'password', 'full_name', 'onboarding_completed', 'access_token', 'refresh_token']

    def validate(self, attrs):
        email=attrs.get('email')
        password=attrs.get('password')
        request=self.context.get('request')
        user=authenticate(request, email=email, password=password)
        if not user:
            raise AuthenticationFailed('Email atau kata sandi salah.')
    
        if not user.is_verified:
            raise AuthenticationFailed('Email belum diverifikasi. Cek kotak masuk atau kirim ulang kode OTP.')
    
        user_tokens=user.tokens()
        
        return {
            'email': user.email,
            'full_name': user.get_full_name,
            'onboarding_completed': user.onboarding_completed,
            'access_token': str(user_tokens.get('access')),
            'refresh_token': str(user_tokens.get('refresh'))
        }
    
class PasswordResetRequestSerializer(serializers.Serializer):
    email=serializers.EmailField(max_length=255)
    class Meta:
        fields=['email']

    def validate(self, attrs):
        email=attrs.get('email')
        if User.objects.filter(email=email).exists():
            user=User.objects.get(email=email)
            uidb64=urlsafe_base64_encode(smart_bytes(user.id))
            token=PasswordResetTokenGenerator().make_token(user)
            request=self.context.get('request')
            abslink = f"{settings.FRONTEND_URL}/password-reset-confirm/{uidb64}/{token}/"
            # print(abslink)
            email_body=f"Hi {user.full_name} use the link below to reset your password {abslink}"
            data={
                'email_body':email_body, 
                'email_subject':"Reset your Password", 
                'to_email':user.email
                }
            send_normal_email(data)

        return super().validate(attrs)
    
class SetNewPasswordSerializer(serializers.Serializer):
    password=serializers.CharField(max_length=100, min_length=6, write_only=True)
    confirm_password=serializers.CharField(max_length=100, min_length=6, write_only=True)
    uidb64=serializers.CharField(write_only=True)
    token=serializers.CharField(write_only=True)

    class Meta:
        fields = ['password', 'confirm_password', 'uidb64', 'token']

    def validate(self, attrs):
        try:
            token=attrs.get('token')
            uidb64=attrs.get('uidb64')
            password=attrs.get('password')
            confirm_password=attrs.get('confirm_password')

            user_id=force_str(urlsafe_base64_decode(uidb64))
            user=User.objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed("Link reset kata sandi tidak valid atau sudah kedaluwarsa.", 401)
            if password != confirm_password:
                raise AuthenticationFailed("Konfirmasi kata sandi tidak cocok.")
            user.set_password(password)
            user.save()
            return user
        except Exception as e:
            return AuthenticationFailed("Link tidak valid atau sudah kedaluwarsa.")
        
class LogoutUserSerializer(serializers.Serializer):
    refresh_token=serializers.CharField()

    default_error_messages={
        'bad_token': {'Token is invalid or has expired'}
    }

    def validate(self, attrs):
        self.token=attrs.get('refresh_token')
        return attrs
    
    def save(self, **kwargs):
        try:
            token=RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            return self.fail('bad_token')


def user_me_dict(user):
    """Shape for GET/PUT /users/me. date_of_birth & gender null sampai onboarding."""
    dob = getattr(user, "date_of_birth", None)
    raw_gender = getattr(user, "gender", None)
    gender = raw_gender if raw_gender else None
    created = getattr(user, "created_at", None) or getattr(user, "date_joined", None)
    interests = list(user.interest_rows.values_list("interest_name", flat=True))
    pref = getattr(user, "preferences_row", None)
    return {
        "id": str(user.id),
        "email": user.email,
        "username": getattr(user, "username", None),
        "full_name": user.full_name,
        "is_staff": bool(getattr(user, "is_staff", False)),
        "is_superuser": bool(getattr(user, "is_superuser", False)),
        "phone": getattr(user, "phone", None),
        "date_of_birth": dob.isoformat() if dob else None,
        "gender": gender,
        "bio": getattr(user, "bio", None),
        "profile_picture": getattr(user, "profile_picture", None),
        "location": getattr(user, "location", None),
        "interests": interests,
        "preferences": {
            "preferred_days": pref.preferred_days if pref else None,
            "preferred_time": pref.preferred_time if pref else None,
            "preferred_location": pref.preferred_location if pref else None,
            "notification_enabled": pref.notification_enabled if pref else None,
            "email_notification": pref.email_notification if pref else None,
            "push_notification": pref.push_notification if pref else None,
        },
        "onboarding_completed": getattr(user, "onboarding_completed", False),
        "is_verified": user.is_verified,
        "created_at": created.isoformat().replace("+00:00", "Z") if created else None,
    }


def user_public_dict(user):
    """Shape for GET /users/:username (public profile)."""
    created = getattr(user, "created_at", None) or getattr(user, "date_joined", None)
    interests = list(user.interest_rows.values_list("interest_name", flat=True))
    pref = getattr(user, "preferences_row", None)
    return {
        "id": str(user.id),
        "username": getattr(user, "username", None),
        "full_name": user.full_name,
        "is_staff": bool(getattr(user, "is_staff", False)),
        "bio": getattr(user, "bio", None),
        "profile_picture": getattr(user, "profile_picture", None),
        "location": getattr(user, "location", None),
        "interests": interests,
        "preferences": {
            "preferred_days": pref.preferred_days if pref else None,
            "preferred_time": pref.preferred_time if pref else None,
            "preferred_location": pref.preferred_location if pref else None,
            "notification_enabled": pref.notification_enabled if pref else None,
            "email_notification": pref.email_notification if pref else None,
            "push_notification": pref.push_notification if pref else None,
        },
        "created_at": created.isoformat().replace("+00:00", "Z") if created else None,
    }
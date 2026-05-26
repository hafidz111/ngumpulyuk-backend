from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.encoding import DjangoUnicodeDecodeError, smart_str
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.utils import extend_schema, extend_schema_view
from ngumpulyuk_app.common.openapi_params import path_str
from ngumpulyuk_app.common.openapi_responses import R200, R201, R204
from rest_framework import serializers, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from ngumpulyuk_app.common.api_response import err, ok

from .models import OneTimePassword, User
from .serializers import (
    LoginSerializer,
    LogoutUserSerializer,
    PasswordResetRequestSerializer,
    SetNewPasswordSerializer,
    UserRegisterSerializer,
    ResendVerificationSerializer,
    VerifyEmailSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView as SimpleJwtTokenRefreshView

from .utils import OtpEmailDeliveryError, deliver_otp_to_user, record_user_login

AUTH_TAG = ["Authentication"]


class EmptySerializer(serializers.Serializer):
    """Placeholder untuk GenericAPIView yang tidak memakai body (Swagger)."""


def _otp_send_error_response(exc=None):
    default = (
        "Gagal mengirim email OTP. Periksa alamat email atau coba lagi dalam beberapa menit."
    )
    detail = str(exc).strip() if exc else ""
    message = detail if detail and len(detail) < 220 else default
    return err(
        "EMAIL_DELIVERY_FAILED",
        message,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@extend_schema_view(
    post=extend_schema(
        tags=AUTH_TAG,
        summary="Registrasi akun",
        request=UserRegisterSerializer,
        responses=R201,
    ),
)
class RegisterUserView(GenericAPIView):
    serializer_class = UserRegisterSerializer

    def post(self, request):
        user_data = request.data
        serializer = self.serializer_class(data=user_data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            user = serializer.data
            try:
                deliver_otp_to_user(user["email"])
            except OtpEmailDeliveryError as exc:
                return _otp_send_error_response(exc)
            return ok(
                user,
                message="Daftar berhasil, silahkan login dengan email yang telah didaftarkan",
                status_code=status.HTTP_201_CREATED,
            )
        return err("VALIDATION_ERROR", "Validation error", status.HTTP_422_UNPROCESSABLE_ENTITY)


@extend_schema_view(
    post=extend_schema(
        tags=AUTH_TAG,
        summary="Verifikasi email (OTP)",
        request=VerifyEmailSerializer,
        responses=R200,
    ),
)
class VerifyUserEmail(GenericAPIView):
    serializer_class = VerifyEmailSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otpcode = serializer.validated_data["otp"]

        if not otpcode:
            return err("VALIDATION_ERROR", "OTP wajib diisi", status.HTTP_422_UNPROCESSABLE_ENTITY)

        try:
            user_code_obj = OneTimePassword.objects.get(code=otpcode)
            user = user_code_obj.user
            if not user.is_verified:
                user.is_verified = True
                user.save()
                return ok(message="Account email verified successfully")
            return err("CONFLICT", "Email already verified", status.HTTP_409_CONFLICT)
        except OneTimePassword.DoesNotExist:
            return err("NOT_FOUND", "Kode OTP tidak ditemukan atau sudah kedaluwarsa.", status.HTTP_404_NOT_FOUND)


@extend_schema_view(
    post=extend_schema(
        tags=AUTH_TAG,
        summary="Kirim ulang kode verifikasi email",
        request=ResendVerificationSerializer,
        responses=R200,
    ),
)
class ResendVerificationView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ResendVerificationSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return err("NOT_FOUND", "Akun tidak ditemukan.", status.HTTP_404_NOT_FOUND)
        if user.is_verified:
            return err(
                "CONFLICT",
                "Email sudah terverifikasi.",
                status.HTTP_409_CONFLICT,
            )
        try:
            deliver_otp_to_user(email)
        except OtpEmailDeliveryError as exc:
            return _otp_send_error_response(exc)
        return ok(message="Verification code sent")


@extend_schema_view(
    post=extend_schema(
        tags=AUTH_TAG,
        summary="Login",
        request=LoginSerializer,
        responses=R200,
    ),
)
class LoginUserView(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return ok(serializer.data)


@extend_schema_view(
    get=extend_schema(tags=AUTH_TAG, summary="Cek token (profil auth)", responses=R200),
)
class TestAuthenticationView(GenericAPIView):
    serializer_class = EmptySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {"msg": "its works"}
        return ok(data)


@extend_schema_view(
    post=extend_schema(
        tags=AUTH_TAG,
        summary="Permintaan reset password",
        request=PasswordResetRequestSerializer,
        responses=R200,
    ),
)
class PasswordResetRequestView(GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return ok(message="we have sent you a link to reset your password")


@extend_schema_view(
    get=extend_schema(
        tags=AUTH_TAG,
        summary="Validasi token reset password (link email)",
        parameters=[
            path_str("uidb64", "User id (base64) dari link email"),
            path_str("token", "Token dari link email"),
        ],
        responses=R200,
    ),
)
class PasswordResetConfirm(GenericAPIView):
    serializer_class = EmptySerializer

    def get(self, request, uidb64, token):
        try:
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return err("UNAUTHORIZED", "Sesi tidak valid atau sudah berakhir. Silakan masuk lagi.", status.HTTP_401_UNAUTHORIZED)
            return ok(
                {"uidb64": uidb64, "token": token},
                message="credentials is valid",
            )

        except DjangoUnicodeDecodeError as identifier:
            return err("UNAUTHORIZED", "token is invalid or has expired", status.HTTP_401_UNAUTHORIZED)


@extend_schema_view(
    patch=extend_schema(
        tags=AUTH_TAG,
        summary="Set password baru (setelah token valid)",
        request=SetNewPasswordSerializer,
        responses=R200,
    ),
)
class SetNewPassword(GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return ok(message="password reset is succesful")


@extend_schema_view(
    post=extend_schema(
        tags=AUTH_TAG,
        summary="Refresh access token",
        description=(
            "Gunakan refresh token yang valid untuk mendapatkan access token baru. "
            "Kirimkan refresh token untuk memperbarui sesi tanpa login ulang."
        ),
    ),
)
class TokenRefreshView(SimpleJwtTokenRefreshView):
    """
    Refresh access token; perbarui last_login paling lambat setiap 12 jam
    (user yang hanya pakai refresh tidak pernah 'login' ulang).
    """

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code != 200:
            return response
        raw = request.data.get("refresh")
        if not raw:
            return response
        try:
            token = RefreshToken(raw)
            user = get_user_model().objects.filter(pk=token.get("user_id")).first()
            if user and (
                not user.last_login
                or user.last_login < timezone.now() - timedelta(hours=12)
            ):
                record_user_login(user, request)
        except Exception:
            pass
        return response


@extend_schema_view(
    post=extend_schema(
        tags=AUTH_TAG,
        summary="Logout (blacklist refresh token)",
        request=LogoutUserSerializer,
        responses=R204,
    ),
)
class LogoutUserView(GenericAPIView):
    serializer_class = LogoutUserSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok(message="logout successful")

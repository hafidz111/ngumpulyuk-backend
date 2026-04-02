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
from .utils import send_code_to_user

AUTH_TAG = ["Authentication"]


class EmptySerializer(serializers.Serializer):
    """Placeholder untuk GenericAPIView yang tidak memakai body (Swagger)."""


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
            send_code_to_user(user["email"])
            return Response(
                {
                    "data": user,
                    "message": "Daftar berhasil, silahkan login dengan email yang telah didaftarkan",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
            return Response({"message": "OTP wajib diisi"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_code_obj = OneTimePassword.objects.get(code=otpcode)
            user = user_code_obj.user
            if not user.is_verified:
                user.is_verified = True
                user.save()
                return Response({"message": "Account email verified successfully"}, status=status.HTTP_200_OK)
            return Response(
                {"message": "Code is invalid user already verified"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except OneTimePassword.DoesNotExist:
            return Response({"message": "passcode not provided"}, status=status.HTTP_404_NOT_FOUND)


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
            return err("NOT_FOUND", "User not found", status.HTTP_404_NOT_FOUND)
        if user.is_verified:
            return err(
                "BAD_REQUEST",
                "Email already verified",
                status.HTTP_400_BAD_REQUEST,
            )
        send_code_to_user(email)
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
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(tags=AUTH_TAG, summary="Cek token (profil auth)", responses=R200),
)
class TestAuthenticationView(GenericAPIView):
    serializer_class = EmptySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {"msg": "its works"}
        return Response(data, status=status.HTTP_200_OK)


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
        return Response({"message": "we have sent you a link to reset your password"}, status=status.HTTP_200_OK)


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
                return Response(
                    {"message": "token is invalid or has expired"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            return Response(
                {
                    "success": True,
                    "message": "credentials is valid",
                    "uidb64": uidb64,
                    "token": token,
                },
                status=status.HTTP_200_OK,
            )

        except DjangoUnicodeDecodeError as identifier:
            return Response(
                {"message": "token is invalid or has expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


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
        return Response(
            {"success": True, "message": "password reset is succesful"},
            status=status.HTTP_200_OK,
        )


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
        return Response(status=status.HTTP_204_NO_CONTENT)

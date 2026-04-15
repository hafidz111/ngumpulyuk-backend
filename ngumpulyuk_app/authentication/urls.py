from django.urls import path
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterUserView,
    VerifyUserEmail,
    ResendVerificationView,
    LoginUserView,
    PasswordResetRequestView,
    PasswordResetConfirm,
    SetNewPassword,
    LogoutUserView,
    TestAuthenticationView,
)

urlpatterns=[
    path('register/', RegisterUserView.as_view(), name='register'),
    path('verify-email/', VerifyUserEmail.as_view(), name='verify'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    path('login/', LoginUserView.as_view(), name='login'),
    path('refresh/', extend_schema(
        tags=['Authentication'],
        summary='Refresh access token',
        description='Gunakan refresh token yang valid untuk mendapatkan access token baru. '
                    'Access token memiliki masa berlaku pendek (5 menit), '
                    'kirimkan refresh token untuk memperbarui sesi tanpa perlu login ulang.',
    )(TokenRefreshView).as_view(), name='token_refresh'),
    path('profile/', TestAuthenticationView.as_view(), name='granted'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirm.as_view(), name='password-reset-confirm'),
    path('set-new-password/', SetNewPassword.as_view(), name='set-new-password'),
    path('logout/', LogoutUserView.as_view(), name='logout'),
]
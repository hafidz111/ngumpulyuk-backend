from drf_spectacular.utils import extend_schema, extend_schema_view
from ngumpulyuk_app.common.openapi_responses import R200
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from .serializers import GoogleSignInSerializer

AUTH_TAG = ["Authentication"]


@extend_schema_view(
    post=extend_schema(
        tags=AUTH_TAG,
        summary="Google Sign-In (token)",
        request=GoogleSignInSerializer,
        responses=R200,
    ),
)
class GoogleSignInView(GenericAPIView):
    serializer_class = GoogleSignInSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data["access_token"]
        return Response(data, status=status.HTTP_200_OK)
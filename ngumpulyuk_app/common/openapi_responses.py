"""Response schemas untuk drf-spectacular pada APIView (hindari 'unable to guess serializer')."""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse

# JSON umum (envelope success/data atau response bebas)
R200 = {200: OpenApiTypes.OBJECT}
R201 = {201: OpenApiTypes.OBJECT}
R204 = {204: OpenApiResponse(description="Tanpa body")}
R200_201 = {200: OpenApiTypes.OBJECT, 201: OpenApiTypes.OBJECT}

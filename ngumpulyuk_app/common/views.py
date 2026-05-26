from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ngumpulyuk_app.common.indonesia_locations import all_locations, search_locations
from ngumpulyuk_app.common.openapi_params import q_str
from ngumpulyuk_app.common.openapi_responses import R200
from drf_spectacular.utils import extend_schema


@extend_schema(
    tags=["Locations"],
    summary="Daftar kabupaten/kota Indonesia",
    parameters=[
        q_str("search", "Filter nama kab/kota atau provinsi"),
        q_str("limit", "Maksimal hasil (default 50, max 514)"),
    ],
    responses=R200,
)
class IndonesiaLocationListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        search = request.query_params.get("search", "").strip()
        try:
            limit = int(request.query_params.get("limit", 50))
        except (TypeError, ValueError):
            limit = 50
        limit = max(1, min(limit, 514))

        if search:
            rows = search_locations(q=search, limit=limit)
        else:
            rows = all_locations()[:limit]

        return Response(
            {
                "data": [
                    {
                        "id": r["id"],
                        "slug": r["slug"],
                        "label": r["label"],
                        "province": r["province"],
                        "provinceId": r["provinceId"],
                        "latitude": r.get("latitude"),
                        "longitude": r.get("longitude"),
                    }
                    for r in rows
                ],
                "total": len(all_locations()),
            }
        )

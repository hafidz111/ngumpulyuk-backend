"""Query/path parameters bersama untuk dokumentasi drf-spectacular (Swagger)."""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter


def q_int(name: str, description: str, default: int):
    return OpenApiParameter(
        name=name,
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description=description,
        required=False,
        default=default,
    )


def q_str(name: str, description: str, required: bool = False):
    return OpenApiParameter(
        name=name,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description=description,
        required=required,
    )


def path_uuid(name: str, description: str):
    return OpenApiParameter(
        name=name,
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.PATH,
        description=description,
        required=True,
    )


def path_str(name: str, description: str):
    return OpenApiParameter(
        name=name,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.PATH,
        description=description,
        required=True,
    )

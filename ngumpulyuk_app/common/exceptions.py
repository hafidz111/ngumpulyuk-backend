from rest_framework import status
from rest_framework.views import exception_handler

from ngumpulyuk_app.common.api_response import err


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    detail = response.data
    if isinstance(detail, dict):
        if "detail" in detail and len(detail) == 1:
            msg = str(detail["detail"])
        else:
            msg = "Validation error"
    elif isinstance(detail, list):
        msg = "; ".join(str(x) for x in detail)
    else:
        msg = str(detail)
    code = "VALIDATION_ERROR"
    http_status = response.status_code
    if http_status == status.HTTP_401_UNAUTHORIZED:
        code = "UNAUTHORIZED"
    elif http_status == status.HTTP_403_FORBIDDEN:
        code = "FORBIDDEN"
    elif http_status == status.HTTP_404_NOT_FOUND:
        code = "NOT_FOUND"
    elif http_status == status.HTTP_400_BAD_REQUEST:
        code = "VALIDATION_ERROR"
    return err(code, msg, http_status, details=detail if isinstance(detail, (dict, list)) else None)

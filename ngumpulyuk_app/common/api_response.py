from rest_framework import status
from rest_framework.response import Response


def ok(data=None, message=None, status_code=status.HTTP_200_OK, extra=None):
    body = {"success": True}
    if message is not None:
        body["message"] = message
    if data is not None:
        body["data"] = data
    if extra:
        body.update(extra)
    return Response(body, status=status_code)


def err(code, message, http_status, details=None):
    payload = {"success": False, "error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return Response(payload, status=http_status)

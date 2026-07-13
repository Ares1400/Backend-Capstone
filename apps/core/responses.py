"""
Small helper for consistent "success" response envelopes, mirroring the
shape produced by apps.core.exceptions.custom_exception_handler for errors.
"""

from rest_framework.response import Response


def success_response(message="Success", data=None, status=200):
    return Response(
        {"success": True, "message": message, "data": data},
        status=status,
    )

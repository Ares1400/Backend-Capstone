"""
Custom DRF exception handler.

Wraps every error response (validation errors, 404s, permission denials,
throttling, server errors) in a consistent JSON envelope:

    {
        "success": false,
        "message": "<human readable summary>",
        "errors": {... field-level detail or null ...}
    }

This keeps API responses predictable for frontend/Postman consumers and
satisfies the "API response validation" testing requirement in the spec.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        # Unhandled exception (e.g. unexpected server error) -> 500
        return Response(
            {
                "success": False,
                "message": "An unexpected error occurred. Please try again later.",
                "errors": str(exc) if exc else None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    message = "Request failed."
    if isinstance(response.data, dict) and "detail" in response.data:
        message = str(response.data["detail"])
    elif response.status_code == status.HTTP_400_BAD_REQUEST:
        message = "Validation failed."

    response.data = {
        "success": False,
        "message": message,
        "errors": response.data,
    }
    return response

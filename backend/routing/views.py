from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services import tomtom
from .services.http import ExternalServiceError


def error_response(exc):
    return Response({"detail": str(exc)}, status=exc.status_code)


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})


@api_view(["GET"])
def geocode(request):
    query = request.query_params.get("q", "")
    try:
        return Response({"results": tomtom.geocode(query)})
    except ExternalServiceError as exc:
        return error_response(exc)

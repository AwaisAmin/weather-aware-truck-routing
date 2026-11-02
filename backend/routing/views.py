from rest_framework.decorators import api_view
from rest_framework.response import Response

from .heatmap import build_heatmap
from .planner import plan_trip
from .serializers import HeatmapRequestSerializer, PlanRequestSerializer
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


@api_view(["POST"])
def plan(request):
    serializer = PlanRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        return Response(plan_trip(**serializer.validated_data))
    except ExternalServiceError as exc:
        return error_response(exc)


@api_view(["POST"])
def heatmap(request):
    serializer = HeatmapRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        return Response(build_heatmap(**serializer.validated_data))
    except ExternalServiceError as exc:
        return error_response(exc)

from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .checkpoints import SAMPLE_INTERVALS_MILES

# Forecasts beyond a few days are unreliable, and the trip plus the 48 h heatmap must fit
# inside the 8-day forecast window.
MAX_DAYS_AHEAD = 5
# A legal US 80,000 lb gross limit minus a ~35,000 lb tractor-trailer leaves ~45,000 lb of
# cargo; allow overweight/permit loads up to 100,000 lb.
MAX_LOAD_LB = 100_000


class LocationSerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)
    label = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")


class PlanRequestSerializer(serializers.Serializer):
    origin = LocationSerializer()
    destination = LocationSerializer()
    departure = serializers.DateTimeField()
    load_lb = serializers.FloatField(min_value=0, max_value=MAX_LOAD_LB)
    interval_miles = serializers.ChoiceField(choices=SAMPLE_INTERVALS_MILES, default=25)

    def validate_departure(self, value):
        now = timezone.now()
        if value > now + timedelta(days=MAX_DAYS_AHEAD):
            raise serializers.ValidationError(f"Departure must be within {MAX_DAYS_AHEAD} days.")
        # A departure in the past means "leave now".
        return max(value, now).replace(microsecond=0)

    def validate(self, attrs):
        origin, destination = attrs["origin"], attrs["destination"]
        if abs(origin["lat"] - destination["lat"]) < 1e-4 and abs(origin["lon"] - destination["lon"]) < 1e-4:
            raise serializers.ValidationError("Origin and destination must be different places.")
        return attrs

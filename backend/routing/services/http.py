import requests
from django.conf import settings

_session = requests.Session()


class ExternalServiceError(Exception):
    """A third-party API failed or returned something unusable."""

    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


def get_json(url, params=None, service="external service"):
    try:
        response = _session.get(url, params=params, timeout=settings.HTTP_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise ExternalServiceError(f"Could not reach {service}.") from exc
    if response.status_code == 429:
        raise ExternalServiceError(
            f"{service} rate limit reached. Please try again in a minute.", status_code=503
        )
    if response.status_code >= 400:
        raise ExternalServiceError(
            f"{service} returned an error ({response.status_code}).",
            status_code=400 if response.status_code == 400 else 502,
        )
    return response.json()

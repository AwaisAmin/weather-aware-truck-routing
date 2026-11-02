import pytest

from routing.services import http


class FakeResponse:
    def __init__(self, status_code, body=None):
        self.status_code = status_code
        self.body = body

    def json(self):
        return self.body


@pytest.mark.parametrize(
    "status, expected_status, message",
    [(429, 503, "rate limit"), (400, 400, "error (400)"), (500, 502, "error (500)")],
)
def test_upstream_errors_are_mapped(monkeypatch, status, expected_status, message):
    monkeypatch.setattr(http._session, "get", lambda *a, **k: FakeResponse(status))
    with pytest.raises(http.ExternalServiceError) as excinfo:
        http.get_json("https://example.invalid", service="Open-Meteo")
    assert excinfo.value.status_code == expected_status
    assert message in str(excinfo.value)


def test_success_returns_json(monkeypatch):
    monkeypatch.setattr(http._session, "get", lambda *a, **k: FakeResponse(200, {"ok": True}))
    assert http.get_json("https://example.invalid") == {"ok": True}

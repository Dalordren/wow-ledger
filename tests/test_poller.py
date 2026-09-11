from app.poller import is_retryable
import httpx2
import pytest


def status_code_error(code: int) -> httpx2.HTTPStatusError:
    dummy_request = httpx2.Request("GET", "https://localhost")
    dummy_response = httpx2.Response(code, request=dummy_request)
    return httpx2.HTTPStatusError(
        "Humhum", request=dummy_request, response=dummy_response
    )


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (httpx2.ConnectError("Connection Refused"), True),
        (status_code_error(429), True),
        (status_code_error(502), True),
        (status_code_error(503), True),
        (status_code_error(504), True),
        (status_code_error(500), True),
        (status_code_error(400), False),
        (status_code_error(401), False),
        (status_code_error(404), False),
        (ValueError("Server error"), False),
        (RuntimeError("General system failure"), False),
    ],
)
def test_is_retryable(error, expected):
    assert is_retryable(error) is expected

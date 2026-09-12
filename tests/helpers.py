import httpx2


def status_code_error(code: int) -> httpx2.HTTPStatusError:
    dummy_request = httpx2.Request("GET", "https://localhost")
    dummy_response = httpx2.Response(code, request=dummy_request)
    return httpx2.HTTPStatusError(
        "connection refused", request=dummy_request, response=dummy_response
    )

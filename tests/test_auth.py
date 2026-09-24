import pytest
from fastapi import status

from app.routers import auth as auth_patch
from app.security import create_access_token


def test_register_user_returns_created(api_client):
    response = api_client.post(
        "/register", json={"email": "test@example.com", "password": "1234567890"}
    )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["email"] == "test@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


def test_duplicate_user_is_rejected(api_client):
    payload = {"email": "test2@example.com", "password": "1234567890"}
    first = api_client.post("/register", json=payload)
    assert first.status_code == status.HTTP_201_CREATED

    second = api_client.post("/register", json=payload)
    assert second.status_code == status.HTTP_409_CONFLICT


@pytest.mark.parametrize(
    "test_payload",
    [
        {"email": "", "password": "test2test"},
        {"email": "test@example.com", "password": "test123"},
        {"email": "test@example.com"},
    ],
)
def test_invalid_registration_is_rejected(api_client, test_payload):
    response = api_client.post("/register", json=test_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.fixture
def registered_user(api_client):
    credentials = {"email": "registered@example.com", "password": "registeredpassword"}
    response = api_client.post("/register", json=credentials)
    assert response.status_code == status.HTTP_201_CREATED
    return credentials


@pytest.fixture
def auth_header(api_client, registered_user):
    response = api_client.post(
        "/token",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == status.HTTP_200_OK
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_login_returns_token(api_client, registered_user):
    response = api_client.post(
        "/token",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_failures_are_indistinguishable(api_client, registered_user):
    unknown_email = api_client.post(
        "/token",
        data={
            "username": "thisisnotemail@example.com",
            "password": registered_user["password"],
        },
    )
    wrong_password = api_client.post(
        "/token",
        data={
            "username": registered_user["email"],
            "password": "notthesamepassword",
        },
    )
    assert unknown_email.status_code == status.HTTP_401_UNAUTHORIZED
    assert wrong_password.status_code == unknown_email.status_code
    assert wrong_password.json() == unknown_email.json()


def test_me_returns_the_authenticated_user(api_client, registered_user, auth_header):
    response = api_client.get("/users/me", headers=auth_header)
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["email"] == registered_user["email"]
    assert "hashed_password" not in body


def test_me_requires_authentication(api_client):
    response = api_client.get("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_me_with_tampered_token(api_client, auth_header):
    valid_token = auth_header["Authorization"].removeprefix("Bearer ")
    header, payload, signature = valid_token.split(".")
    tampered_token = f"{header}.{payload}.{signature[:-4]}AAAA"
    response = api_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid token."


def test_me_with_malformed_token(api_client):
    tampered = "fadkfjfkKJKJFGSAKGJWEGSDF"
    response = api_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {tampered}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid token."


def test_verify_password_gets_called_per_request(
    api_client, registered_user, monkeypatch
):
    function_calls = []
    verify_password = auth_patch.verify_password

    def record_function_calls(password, hashed):
        function_calls.append(hashed)
        return verify_password(password, hashed)

    monkeypatch.setattr(auth_patch, "verify_password", record_function_calls)

    first_response = api_client.post(
        "/token",
        data={"username": "notregistered@example.com", "password": "notarealpassword"},
    )
    second_response = api_client.post(
        "/token",
        data={"username": registered_user["email"], "password": "notarealpassword"},
    )

    assert first_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert second_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert function_calls[0] == auth_patch.DUMMY_HASHED_PASSWORD
    assert function_calls[1] != auth_patch.DUMMY_HASHED_PASSWORD
    assert len(function_calls) == 2


def test_me_with_invalid_sub(api_client):
    fake_token = create_access_token("test")

    response = api_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {fake_token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid token."

from fastapi import status


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

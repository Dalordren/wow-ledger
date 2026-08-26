from fastapi import status


def test_read_root_returns_welcome_message(client):
    response = client.get("/")
    body = response.json()
    assert "message" in body
    assert response.status_code == status.HTTP_200_OK

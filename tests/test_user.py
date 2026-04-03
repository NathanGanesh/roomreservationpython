def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "firstName": "New",
            "lastName": "User",
            "password": "StrongPass123",
        },
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["user"]["email"] == "newuser@example.com"
    assert body["accessToken"]


def test_login_success(client, registered_user):
    response = client.post(
        "/auth/login",
        json={"email": "seller@example.com", "password": "StrongPass123"},
    )

    assert response.status_code == 200
    assert response.get_json()["accessToken"]


def test_login_fails_with_wrong_password(client, registered_user):
    response = client.post(
        "/auth/login",
        json={"email": "seller@example.com", "password": "WrongPassword"},
    )

    assert response.status_code == 401


def test_update_profile(client, auth_headers):
    response = client.put(
        "/auth/profile",
        json={
            "firstName": "Updated",
            "lastName": "Seller",
            "password": "NewStrongPass456",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.get_json()["user"]["firstName"] == "Updated"


def test_delete_profile(client, auth_headers):
    response = client.delete("/auth/profile", headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json()["message"] == "profile deleted"

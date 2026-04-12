def test_alert_rule_crud(client, auth_headers):
    create_response = client.post(
        "/alert-rules",
        json={
            "keyword": "iphone",
            "category": "electronics",
            "minPrice": 100,
            "maxPrice": 500,
            "location": "amsterdam",
            "active": True,
        },
        headers=auth_headers,
    )

    assert create_response.status_code == 201
    rule_id = create_response.get_json()["id"]

    list_response = client.get("/alert-rules", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.get_json()["items"]) == 1

    update_response = client.put(
        f"/alert-rules/{rule_id}",
        json={"maxPrice": 550},
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["maxPrice"] == 550

    delete_response = client.delete(f"/alert-rules/{rule_id}", headers=auth_headers)
    assert delete_response.status_code == 200


def test_duplicate_alert_rule_is_rejected(client, auth_headers):
    first_response = client.post(
        "/alert-rules",
        json={
            "keyword": " iphone ",
            "category": " Electronics ",
            "minPrice": 100,
            "maxPrice": 500,
            "location": " Amsterdam ",
            "active": True,
        },
        headers=auth_headers,
    )
    assert first_response.status_code == 201

    duplicate_response = client.post(
        "/alert-rules",
        json={
            "keyword": "IPHONE",
            "category": "electronics",
            "minPrice": 100.0,
            "maxPrice": 500,
            "location": "amsterdam",
            "active": True,
        },
        headers=auth_headers,
    )

    assert duplicate_response.status_code == 400
    assert duplicate_response.get_json()["error"] == "alert rule already exists"


def test_duplicate_alert_rule_update_is_rejected(client, auth_headers):
    first_response = client.post(
        "/alert-rules",
        json={
            "keyword": "iphone",
            "category": "electronics",
            "minPrice": 100,
            "maxPrice": 500,
            "location": "amsterdam",
            "active": True,
        },
        headers=auth_headers,
    )
    assert first_response.status_code == 201
    first_rule_id = first_response.get_json()["id"]

    second_response = client.post(
        "/alert-rules",
        json={
            "keyword": "ipad",
            "category": "electronics",
            "minPrice": 50,
            "maxPrice": 300,
            "location": "utrecht",
            "active": True,
        },
        headers=auth_headers,
    )
    assert second_response.status_code == 201
    second_rule_id = second_response.get_json()["id"]

    update_response = client.put(
        f"/alert-rules/{second_rule_id}",
        json={
            "keyword": "iphone",
            "category": "electronics",
            "minPrice": 100,
            "maxPrice": 500,
            "location": "amsterdam",
            "active": True,
        },
        headers=auth_headers,
    )

    assert update_response.status_code == 400
    assert update_response.get_json()["error"] == "alert rule already exists"

    first_rule_response = client.get(f"/alert-rules/{first_rule_id}", headers=auth_headers)
    assert first_rule_response.status_code == 200


def test_same_alert_rule_is_allowed_for_different_users(client, auth_headers):
    first_response = client.post(
        "/alert-rules",
        json={
            "keyword": "iphone",
            "category": "electronics",
            "minPrice": 100,
            "maxPrice": 500,
            "location": "amsterdam",
            "active": True,
        },
        headers=auth_headers,
    )
    assert first_response.status_code == 201

    register_second_user = client.post(
        "/auth/register",
        json={
            "email": "second@example.com",
            "firstName": "Second",
            "lastName": "User",
            "password": "StrongPass123",
        },
    )
    assert register_second_user.status_code == 201

    second_headers = {
        "Authorization": f"Bearer {register_second_user.get_json()['accessToken']}"
    }
    second_response = client.post(
        "/alert-rules",
        json={
            "keyword": "iphone",
            "category": "electronics",
            "minPrice": 100,
            "maxPrice": 500,
            "location": "amsterdam",
            "active": True,
        },
        headers=second_headers,
    )

    assert second_response.status_code == 201


def test_alert_rule_create_rejects_invalid_price_range(client, auth_headers):
    response = client.post(
        "/alert-rules",
        json={
            "keyword": "iphone",
            "category": "electronics",
            "minPrice": 500,
            "maxPrice": 100,
            "location": "amsterdam",
            "active": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "maxPrice must be greater than or equal to minPrice"


def test_alert_rule_update_rejects_invalid_price_range(client, auth_headers):
    create_response = client.post(
        "/alert-rules",
        json={
            "keyword": "iphone",
            "category": "electronics",
            "minPrice": 100,
            "maxPrice": 500,
            "location": "amsterdam",
            "active": True,
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    rule_id = create_response.get_json()["id"]

    update_response = client.put(
        f"/alert-rules/{rule_id}",
        json={
            "minPrice": 600,
            "maxPrice": 200,
        },
        headers=auth_headers,
    )

    assert update_response.status_code == 400
    assert update_response.get_json()["error"] == "maxPrice must be greater than or equal to minPrice"

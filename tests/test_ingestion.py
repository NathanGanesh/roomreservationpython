def test_listing_crud(client, auth_headers):
    create_response = client.post(
        "/listings",
        json={
            "externalId": "mk-1",
            "sourceName": "marktplaats",
            "title": "MacBook Pro 14",
            "description": "Laptop in good state",
            "price": 1299,
            "currency": "EUR",
            "city": "Utrecht",
            "url": "https://example.com/listings/mk-1",
            "postedAt": "2026-04-03T09:00:00",
        },
        headers=auth_headers,
    )

    assert create_response.status_code == 201
    listing_id = create_response.get_json()["id"]

    update_response = client.put(
        f"/listings/{listing_id}",
        json={
            "externalId": "mk-1",
            "sourceName": "marktplaats",
            "title": "MacBook Pro 14",
            "description": "Laptop in good state",
            "price": 1199,
            "currency": "EUR",
            "city": "Utrecht",
            "url": "https://example.com/listings/mk-1",
            "postedAt": "2026-04-03T09:00:00",
        },
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["price"] == 1199

    list_response = client.get("/listings", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.get_json()["items"]) == 1

    delete_response = client.delete(f"/listings/{listing_id}", headers=auth_headers)
    assert delete_response.status_code == 200


def test_ingestion_creates_matches(client, auth_headers):
    rule_response = client.post(
        "/alert-rules",
        json={
            "keyword": "iphone",
            "minPrice": 200,
            "maxPrice": 600,
            "location": "rotterdam",
        },
        headers=auth_headers,
    )
    assert rule_response.status_code == 201

    ingestion_response = client.post(
        "/ingestion/listings",
        json={
            "listings": [
                {
                    "externalId": "mk-iphone-1",
                    "sourceName": "marktplaats",
                    "title": "iPhone 14 128GB",
                    "description": "Used phone with box",
                    "price": 450,
                    "currency": "EUR",
                    "city": "Rotterdam",
                    "url": "https://example.com/listings/mk-iphone-1",
                    "postedAt": "2026-04-03T10:00:00",
                },
                {
                    "externalId": "mk-bike-1",
                    "sourceName": "marktplaats",
                    "title": "City bike",
                    "description": "Daily commuter bike",
                    "price": 150,
                    "currency": "EUR",
                    "city": "Rotterdam",
                    "url": "https://example.com/listings/mk-bike-1",
                    "postedAt": "2026-04-03T10:30:00",
                },
            ]
        },
        headers=auth_headers,
    )

    assert ingestion_response.status_code == 201
    body = ingestion_response.get_json()
    assert body["matchCount"] == 1
    match_id = body["createdMatches"][0]["id"]

    matches_response = client.get("/matches", headers=auth_headers)
    assert matches_response.status_code == 200
    assert len(matches_response.get_json()["items"]) == 1

    update_response = client.put(
        f"/matches/{match_id}",
        json={"status": "reviewed"},
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["status"] == "reviewed"


def test_manual_match_crud(client, auth_headers):
    rule_response = client.post(
        "/alert-rules",
        json={"keyword": "macbook"},
        headers=auth_headers,
    )
    assert rule_response.status_code == 201
    rule_id = rule_response.get_json()["id"]

    listing_response = client.post(
        "/listings",
        json={
            "externalId": "mk-macbook-1",
            "sourceName": "marktplaats",
            "title": "MacBook Air",
            "description": "Laptop in Amsterdam",
            "price": 800,
            "currency": "EUR",
            "city": "Amsterdam",
            "url": "https://example.com/listings/mk-macbook-1",
            "postedAt": "2026-04-03T11:00:00",
        },
        headers=auth_headers,
    )
    assert listing_response.status_code == 201
    listing_id = listing_response.get_json()["id"]

    create_response = client.post(
        "/matches",
        json={"alertRuleId": rule_id, "listingId": listing_id},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    match_id = create_response.get_json()["id"]

    get_response = client.get(f"/matches/{match_id}", headers=auth_headers)
    assert get_response.status_code == 200

    update_response = client.put(
        f"/matches/{match_id}",
        json={"status": "acted_on"},
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["status"] == "acted_on"

    delete_response = client.delete(f"/matches/{match_id}", headers=auth_headers)
    assert delete_response.status_code == 200

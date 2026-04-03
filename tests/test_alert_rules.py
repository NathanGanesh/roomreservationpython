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

import pytest

from website import create_app, db


@pytest.fixture
def app():
    app = create_app(
        {
            "APP_ENV": "testing",
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "JWT_SECRET_KEY": "test-secret",
            "SECRET_KEY": "test-secret",
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def registered_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "seller@example.com",
            "firstName": "Deal",
            "lastName": "Hunter",
            "password": "StrongPass123",
        },
    )
    return response.get_json()


@pytest.fixture
def auth_headers(client, registered_user):
    login = client.post(
        "/auth/login",
        json={"email": "seller@example.com", "password": "StrongPass123"},
    ).get_json()
    return {"Authorization": f"Bearer {login['accessToken']}"}

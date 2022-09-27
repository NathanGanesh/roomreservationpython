from datetime import datetime
from sqlalchemy import func, select

from werkzeug.security import generate_password_hash, check_password_hash
from website.models import UserSchema, Resere, User
from website import db
from flask import url_for

def test_validate_password():
    # given
    schema = UserSchema()
    reservations = Resere(date=datetime(2022, 9, 10))
    reservation2 = Resere(date=datetime(2022, 9, 11))
    password1 = generate_password_hash('Pokemon!23', method='sha256')
    janpeter = User(email='pokemon@gmail.com',
                    firstName='jan', lastName='peter',
                    password=password1, reservations=[reservations, reservation2])
    # when

    # then


def test_create_user(app_with_db):
    # when
    response = app_with_db.post(url_for("auth.sign_up"), data={
        "email": "zuk@gmail.com",
        "firstName": "zuk",
        "lastName": "peter",
        "password": "Pokemon!23"
    })

    assert response.status_code == 200
    count = db.session.execute(select(func.count(User.id)).where(User.firstName == "zuk")).scalar_one()
    assert count == 1

def test_login_succes(app_with_data):
    # given
    response = app_with_data.post(url_for("auth.login"), data={"email": "pokemon@gmail.com", "password": "Pokemon!23"})
    auth_data = response.json
    token = auth_data["access_token"]

    # when
    # response = app_with_data.get(
    #     url_for("users.get_user", username="jan"),
    #     headers={"Authorization": f"Bearer {token}"},
    # )

    # then
    assert response.status_code == 200

def test_login_fails_with_wrong_password(app_with_data):
    response = app_with_data.post(url_for("auth.login"), data={"email": "pokemon@gmail.com", "password": "zuk!23"})
    assert response.status_code == 401

def test_delete_profile(app_with_data):
    response = app_with_data.post(url_for("auth.login"), data={"email": "pokemon@gmail.com", "password": "Pokemon!23"})
    auth_data = response.json
    token = auth_data["access_token"]
    assert response.status_code == 200
    response2 = app_with_data.delete(
        url_for("auth.delete_profile"),
        data={"email": "pokemon@gmail.com"},
        headers={"Authorization": "Bearer " + token}
    )
    assert response.status_code == 200
    assert response2.json == 'succesfully deleted profile'

def test_update_profile(app_with_data):
    response = app_with_data.post(url_for("auth.login"), data={"email": "pokemon@gmail.com", "password": "Pokemon!23"})
    auth_data = response.json
    token = auth_data["access_token"]
    assert response.status_code == 200
    response2 = app_with_data.put(url_for("auth.update_profile"),
        data={"email": "pokemon@gmail.com", "password": "ZukPokemon!23", "firstName":"zuk", "lastName":"cookiemonster"},
        headers={"Authorization": "Bearer " + token})
    print(response2)
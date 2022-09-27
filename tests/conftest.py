from datetime import datetime

import pytest
from sqlalchemy import delete
from werkzeug.security import generate_password_hash
from website import db, create_app
from website.models import User, Resere, Room


@pytest.fixture(scope="session")
def flask_app():
    app = create_app()

    client = app.test_client()

    ctx = app.test_request_context()
    ctx.push()

    yield client

    ctx.pop()


@pytest.fixture(scope="session")
def app_with_db(flask_app):
    db.create_all()

    yield flask_app

    db.session.commit()
    db.drop_all()


@pytest.fixture
def app_with_data(app_with_db):
    reservations = Resere(date=datetime(2022, 9, 10))
    reservation2 = Resere(date=datetime(2022, 9, 11))
    reservation3 = Resere(date=datetime(2022, 9, 12))
    password1 = generate_password_hash('Pokemon!23', method='sha256')
    janpeter = User(email='pokemon@gmail.com',
                    firstName='jan', lastName='peter',
                    password=password1, reservations=[reservations, reservation2])

    dogGoblin = User(email='t1wew@gmail.com',
                     firstName='kek', lastName='blin',
                     password=password1, reservations=[reservation3])

    room1 = Room(name="room1",
                 descriptionBuilding="room1 good building",
                 startDate=datetime(2022, 9, 12),
                 endDate=datetime(2022, 10, 1), reservations=[reservations, reservation2])

    room2 = Room(name="room2", descriptionBuilding="room2 good building",
                 startDate=datetime(2022, 11, 12),
                 endDate=datetime(2022, 12, 1), reservations=[reservation3])

    db.session.add(dogGoblin)
    db.session.add(janpeter)
    db.session.add(room1)
    db.session.add(room2)
    db.session.commit()

    yield app_with_db


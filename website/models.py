from datetime import date, datetime

from . import db, app
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150))
    firstName = db.Column(db.String(150))
    lastName = db.Column(db.String(150))
    password = db.Column(db.String(150))
    active = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    reservations = db.relationship('Resere', backref='user', passive_deletes=True)


class Room(db.Model):
    __tablename__ = 'room'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True)
    descriptionBuilding = db.Column(db.String(150))
    startDate = db.Column(db.Date())
    endDate = db.Column(db.Date())
    reservations = db.relationship('Resere', backref='room', passive_deletes=True)


class Resere(db.Model):
    __tablename__ = 'resere'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date())
    roomi = db.Column(db.Integer, db.ForeignKey('room.id'))
    useri = db.Column(db.Integer, db.ForeignKey('user.id'))


@app.cli.command('db_seed')
def db_seed():
    print("seeding db")
    reservations = Resere(date=datetime(2022,9,10))
    reservation2 = Resere(date=datetime(2022, 9, 11))
    reservation3 = Resere(date=datetime(2022, 9, 12))

    janpeter = User(email='pokemon@gmail.com',
                    firstName='jan', lastName='peter',
                    password='Pokemon!23', reservations = [reservations, reservation2])

    dogGoblin = User(email='t1wew@gmail.com',
                     firstName='kek', lastName='blin',
                     password='Pokemon!23', reservations =[])

    room1 = Room(name="room1",
                 descriptionBuilding="room1 good building",
                 startDate=datetime(2022, 9, 12),
                 endDate=datetime(2022, 10, 1), reservations=[reservations])

    room2 = Room(name="room2", descriptionBuilding="room2 good building",
                 startDate=datetime(2022, 11, 12),
                 endDate=datetime(2022, 12, 1), reservations=[])


    db.session.add(dogGoblin)
    db.session.add(janpeter)
    db.session.add(room1)
    db.session.add(room2)
    db.session.commit()

    print("oek oek seeded!")

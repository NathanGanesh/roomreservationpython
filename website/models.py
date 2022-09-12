from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    firstName = db.Column(db.String(150))
    lastName = db.Column(db.String(150))
    password = db.Column(db.String(150))
    active = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    # reservations = db.relationship('Resere', backref='user', passive_deletes=True)


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    descriptionBuilding = db.Column(db.String(150))
    startDate = db.Column(db.DateTime(timezone=True))
    endDate = db.Column(db.DateTime(timezone=True))
    reservations = db.relationship('Resere', backref='room', passive_deletes=True)


class Resere(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(timezone=True))
    roomi = db.Column(db.Integer, db.ForeignKey('room.id'))
    useri = db.Column(db.Integer, db.ForeignKey('user.id'))

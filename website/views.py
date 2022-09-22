from datetime import datetime
from flask import Blueprint, render_template, jsonify, request

from . import db
from .models import Room, rooms_schema, User, Resere
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from sqlalchemy import text

views = Blueprint("views", __name__)

@views.route("/room/all", methods=["GET"])
def get_free_rooms_date():
    if (request.form.get("date") is not None):
        date = (request.form.get("date"))
        sql = text("""select room.name, room.startDate, room.endDate from room  inner join resere r on room.id = r.roomi where room.startDate 
    > '""" + date + "' and r.date is not " + date)
        result = db.engine.execute(sql)
        names = [row[0] for row in result]
        return jsonify(names)


@views.route("/room/all/date", methods=["GET"])
@jwt_required()
def get_free_rooms_date_with_status():
    startDate = request.args.get('startDate', None)
    endDate = request.args.get('endDate', None)
    if startDate is not None and endDate is not None:
        oekSql = text("""select room.id,room.name, room.descriptionBuilding, room.endDate, room.startDate from room where room.startDate >= '""" + startDate + "'and room.endDate >=" + endDate)
        result = db.engine.execute(oekSql)
        actualResults = []
        for r in result:
            room = dict(r.items())
            roomReservationSql = text("""select u.firstName, u.lastName, r.date from resere r inner join user u on u.id =useri where roomi = '""" + str(room.get('id')) + """'""")
            currentRoomReservation = db.engine.execute(roomReservationSql)
            actualReservations = []
            for g in currentRoomReservation:
                reserve = dict(g.items())
                actualReservations.append(reserve)
            room["reservations"] = actualReservations
            actualResults.append(room)
        print(actualResults)
        return jsonify(rooms=actualResults)
    else:
        return jsonify(message="bad request"), 400


@views.route("reservation/user/all", methods=["GET"])
@jwt_required()
def get_all_user_reservations():
    user = User.query.filter_by(email=get_jwt_identity()).first()
    if request.form.get("email") is not None:
        if user.email == request.form.get("email"):
            reservationsSql = text("""
            select room.name, room.descriptionBuilding, room.endDate,
       room.startDate, r.date, u.firstName, u.lastName,
       u.email, r.id from room  inner join resere r on room.id = r.roomi
            inner join user u on u.id = r.useri
            where u.id = """ + str(user.id))
            result = db.engine.execute(reservationsSql)
            actualResults = []
            for r in result:
                actualResults.append(dict(r.items()))
            return jsonify(reservations=actualResults)
    return jsonify("invalid token please login again"), 401


@views.route("reservation/<string:reservation_id>/delete", methods=["DELETE"])
@jwt_required()
def delete_reservation_by_id(reservation_id: str):
    user = User.query.filter_by(email=get_jwt_identity()).first()
    if request.form.get("email") != None:
        if user.email == request.form.get("email"):
            reservationsSql = text(
                """SELECT resere.id AS resere_id, resere.date AS resere_date, resere.roomi AS resere_roomi, resere.useri AS resere_useri FROM resere WHERE resere.id = """ + str(
                    reservation_id) + " and resere.useri = " + str(user.id))
            result = db.engine.execute(reservationsSql)
            actualResults = []
            for r in result:
                actualResults.append(dict(r.items()))
            if len(actualResults) is not 0:
                for i in range(len(actualResults)):
                    if actualResults[i].get('resere_id') == reservation_id:
                        del actualResults[i]
                        break
                deleteReservationSql = text("""delete from resere where resere.id = """ + str(reservation_id))
                db.engine.execute(deleteReservationSql)
                return jsonify("success")
    return jsonify("invalid token please login again"), 401


@views.route("reservation/<string:room_id>/new", methods=["POST"])
@jwt_required()
def insert_reservation(room_id: str):

    user = User.query.filter_by(email=get_jwt_identity()).first()
    if request.form.get("email") is not None:
        # if user.email == request.form.get("email"):
            # find room
        date = request.form.get("date").split("-")

        reservations = Resere(date=datetime(int(date[0]), int(date[1]), int(date[2])))
        foundRoom = Room.query.filter_by(id=room_id).first()
        if foundRoom:
            checkIfReservationOnDate = text("""SELECT r.name from room r inner join resere r2 on r.id = '""" +  room_id  + """' where r2.date = '""" +request.form.get("date")  + """'""")
            result = db.engine.execute(checkIfReservationOnDate)
            roomReservationDate = result.first()
            if roomReservationDate is None:
                foundRoom.reservations.append(reservations)
                user.reservations.append(reservations)
                db.session.add(foundRoom)
                db.session.add(user)
                db.session.commit()
            # find user
            # add reservation
            # save reservation
                return jsonify("success")
            return jsonify("error room already has a reservation")
        return jsonify("room wasnt found")
    return jsonify("invalid token please login again"), 401

# todo
@views.route("reservation/<string:reservation_id>/update", methods=["PUT"])
@jwt_required()
def update_reservation_by_id(reservation_id: str):
    user = User.query.filter_by(email=get_jwt_identity()).first()
    if request.form.get("email") != None:
        if user.email == request.form.get("email"):
            reservationsSql = text(
                """SELECT resere.id AS resere_id, resere.date AS resere_date, resere.roomi AS resere_roomi, resere.useri AS resere_useri FROM resere WHERE resere.id = """ + str(
                    reservation_id) + " and resere.useri = " + str(user.id))
            result = db.engine.execute(reservationsSql)
            actualResults = []
            for r in result:
                actualResults.append(dict(r.items()))
            if len(actualResults) is not 0:
                for i in range(len(actualResults)):
                    if actualResults[i].get('resere_id') == reservation_id:
                        insertReservationSql = text("""insert into resere ("date", roomi, useri)
values ("""+ ")")
                        break
                return jsonify("success")
            return jsonify("success")
    return jsonify("invalid token please login again"), 401
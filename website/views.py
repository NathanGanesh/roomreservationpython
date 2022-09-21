from flask import Blueprint, render_template, jsonify, request

from . import db
from .models import Room, rooms_schema, User, Resere
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from sqlalchemy import text

# sql = text('select name from penguins')
# result = db.engine.execute(sql)
# names = [row[0] for row in result]
# print names
views = Blueprint("views", __name__)


@views.route("/home")
def home():
    return render_template("home.html")


@views.route("/room/all", methods=["GET"])
def get_free_rooms_date():
    if (request.form.get("date") is not None):
        date = (request.form.get("date"))
        sql = text("""select room.name, room.startDate, room.endDate from room  inner join resere r on room.id = r.roomi where room.startDate 
    > '""" + date + "' and r.date is not " + date)
        result = db.engine.execute(sql)
        names = [row[0] for row in result]
        return jsonify(names)


# <int:planet_id>

@views.route("/room/all/date", methods=["GET"])
@jwt_required()
def get_free_rooms_date_with_status():
    startDate = request.args.get('startDate', None)
    endDate = request.args.get('endDate', None)
    if startDate is not None and endDate is not None:
        oekSql = text("""select room.name, room.descriptionBuilding, room.endDate, room.startDate, r.date, u.firstName, u.lastName, u.email, r.id from room  inner join resere r on room.id = r.roomi
            inner join user u on u.id = r.useri
            where room.startDate >= '""" + startDate + "'and room.endDate >=" + endDate)
        result = db.engine.execute(oekSql)
        actualResults = []
        for r in result:
            actualResults.append(dict(r.items()))

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
    if request.form.get("email") is not None:
        if user.email == request.form.get("email"):

            reservationsSql = text(
                """SELECT resere.id AS resere_id, resere.date AS resere_date, resere.roomi AS resere_roomi, resere.useri AS resere_useri FROM resere WHERE resere.id = """ + str(
                    reservation_id))
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

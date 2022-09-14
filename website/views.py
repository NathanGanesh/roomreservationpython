from flask import Blueprint, render_template, jsonify

import app
from .models import Room, rooms_schema
from flask_jwt_extended import JWTManager, jwt_required, create_access_token

views = Blueprint("views", __name__)

@views.route("/home")
def home():
    return render_template("home.html")

@views.route("/room/all", methods = ["GET"])
def get_todos():
    rooms = Room.query.all()

    result_set = rooms_schema.dump(rooms)

    return jsonify(result_set)


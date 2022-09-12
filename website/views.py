from flask import Blueprint, render_template, jsonify

import app
from .models import Room

views = Blueprint("views", __name__)


@views.route("/")
@views.route("/home")
def home():
    return render_template("home.html")


todolists_schema = Room()

@views.route("/room/all", methods = ["GET"])
def get_todos():
    rooms = Room.query.all()
    result_set = todolists_schema.dump(rooms)
    return jsonify(result_set)

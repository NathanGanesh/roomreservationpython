import flask
from flask import Blueprint, render_template, request, redirect, url_for, make_response, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from flask_mail import Message

from . import db, mail
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required
from .models import User
from datetime import datetime
import datetime

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                access_token = create_access_token(identity=email)
                return jsonify(message="login success", access_token=access_token)
            else:
                return jsonify(message="bad email or password"), 401
        else:
            return jsonify(message="bad email or password"), 401
    return "logged in"


@auth.route("/register", methods=['GET', 'POST'])
def sign_up():
    firstName = request.form.get("firstName")
    lastName = request.form.get("lastName")
    email = request.form.get("email")
    password = request.form.get("password")
    email_exists = User.query.filter_by(email=email).first()
    if email_exists:
        return jsonify({
            'error': 'email already exist'
        }), 400
    elif len(firstName) < 2:
        return jsonify({
            'error': 'email already exist'
        }), 400
    elif len(password) < 6:
        return jsonify({
            'error': 'email already exist'
        }), 400
    elif len(email) < 4:
        return jsonify({
            'error': 'email already exist'
        }), 400
    else:
        new_user = User(email=email, firstName=firstName, lastName=lastName, password=generate_password_hash(
            password, method='sha256'))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        return "successfull created account"


@auth.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message("your reservation API password is " + user.password,
                      sender="admin@reservation-api.com",
                      recipients=[email])
        mail.send(msg)
        return jsonify(message="Password sent to " + email)
    else:
        return jsonify(message="That email doesn't exist"), 401


@auth.route('update_profile', methods=['PUT'])
@jwt_required()
def update_profile():
    # msg = output or "No data returned"
    user = User.query.filter_by(email=get_jwt_identity()).first()
    if request.form.get("email") is not None:
        if check_same_user(email=request.form.get("email"), email2=user.email):
            user.firstName = (request.form.get("firstName")) or user.firstName
            user.lastName = request.form.get("lastName") or user.lastName
            user.password = generate_password_hash(request.form.get("password"), method='sha256') or user.password
            db.session.commit()
            return jsonify("Successfully updated user", username=user.firstName, lastname=user.lastName), 202
    return jsonify("invalid token please login again"), 401

@auth.route('delete_profile', methods=['DELETE'])
@jwt_required()
def delete_profile():
    user = User.query.filter_by(email=get_jwt_identity()).first()
    if request.form.get("email") is not None:
        if check_same_user(email=request.form.get("email"), email2=user.email):
            db.session.delete(user)
            db.session.commit()
            return jsonify("succesfully deleted profile")
    return jsonify("invalid token please login again"), 401

@auth.route("/logout")
def logout():
    return "logout"


def check_same_user(email: str, email2: str):
    if email == email2:
        return True
    return False


def assign_value_if_not_none(value_to_assign: str):
    if value_to_assign is not None:
        return True
    return False

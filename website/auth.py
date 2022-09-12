import flask
from flask import Blueprint, render_template, request, redirect, url_for, make_response, jsonify
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required
from .models import User
from datetime import datetime
import datetime
auth = Blueprint("auth", __name__)

# @app.errorHandler(403)
# def handle_403_error(_error, errMessage):
#     return make_response(jsonify({'error':errMessage}))


@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                return "good"
            else:
                return "bad"
        else:
           return "doesnt exist"

    return render_template("logged in")


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
        new_user = User(email=email, firstName=firstName, lastName=lastName,password=generate_password_hash(
            password, method='sha256'))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        return "successfull created account"
    return "signup"


@auth.route("/logout")
def logout():
    return "logout"
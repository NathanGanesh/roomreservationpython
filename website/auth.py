from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from . import db
from .repositories import UserRepository
from .services import authenticate_user, register_user, update_user

auth_bp = Blueprint("auth", __name__)


def current_user():
    identity = get_jwt_identity()
    return UserRepository.get_by_id(int(identity))


@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    try:
        user = register_user(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    token = create_access_token(identity=str(user.id))
    return jsonify({"user": user.to_dict(), "accessToken": token}), 201


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    user = authenticate_user(payload.get("email"), payload.get("password"))
    if not user:
        return jsonify({"error": "invalid email or password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"accessToken": token, "user": user.to_dict()}), 200


@auth_bp.get("/profile")
@jwt_required()
def get_profile():
    user = current_user()
    if not user:
        return jsonify({"error": "user not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.put("/profile")
@jwt_required()
def put_profile():
    user = current_user()
    if not user:
        return jsonify({"error": "user not found"}), 404

    payload = request.get_json(silent=True) or {}
    try:
        update_user(user, payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"user": user.to_dict()}), 200


@auth_bp.delete("/profile")
@jwt_required()
def delete_profile():
    user = current_user()
    if not user:
        return jsonify({"error": "user not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "profile deleted"}), 200

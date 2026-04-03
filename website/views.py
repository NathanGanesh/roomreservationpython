from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from . import db
from .repositories import AlertRuleRepository, ListingRepository, MatchRepository
from .services import (
    create_match,
    create_alert_rule,
    create_listing,
    ingest_listings,
    update_alert_rule,
    update_listing,
    update_match_status,
)

api_bp = Blueprint("api", __name__)


def current_user_id():
    return int(get_jwt_identity())


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "dealradar-ingestion"}), 200


@api_bp.get("/alert-rules")
@jwt_required()
def list_alert_rules():
    rules = AlertRuleRepository.list_for_user(current_user_id())
    return jsonify({"items": [rule.to_dict() for rule in rules]}), 200


@api_bp.post("/alert-rules")
@jwt_required()
def post_alert_rule():
    payload = request.get_json(silent=True) or {}
    try:
        rule = create_alert_rule(current_user_id(), payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(rule.to_dict()), 201


@api_bp.get("/alert-rules/<int:rule_id>")
@jwt_required()
def get_alert_rule(rule_id: int):
    rule = AlertRuleRepository.get_for_user(rule_id, current_user_id())
    if not rule:
        return jsonify({"error": "alert rule not found"}), 404
    return jsonify(rule.to_dict()), 200


@api_bp.put("/alert-rules/<int:rule_id>")
@jwt_required()
def put_alert_rule(rule_id: int):
    rule = AlertRuleRepository.get_for_user(rule_id, current_user_id())
    if not rule:
        return jsonify({"error": "alert rule not found"}), 404

    payload = request.get_json(silent=True) or {}
    try:
        update_alert_rule(rule, payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(rule.to_dict()), 200


@api_bp.delete("/alert-rules/<int:rule_id>")
@jwt_required()
def delete_alert_rule(rule_id: int):
    rule = AlertRuleRepository.get_for_user(rule_id, current_user_id())
    if not rule:
        return jsonify({"error": "alert rule not found"}), 404

    db.session.delete(rule)
    db.session.commit()
    return jsonify({"message": "alert rule deleted"}), 200


@api_bp.get("/listings")
@jwt_required()
def list_listings():
    listings = ListingRepository.list_all()
    return jsonify({"items": [listing.to_dict() for listing in listings]}), 200


@api_bp.post("/listings")
@jwt_required()
def post_listing():
    payload = request.get_json(silent=True) or {}
    try:
        listing = create_listing(payload)
    except (TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(listing.to_dict()), 201


@api_bp.get("/listings/<int:listing_id>")
@jwt_required()
def get_listing(listing_id: int):
    listing = ListingRepository.get_by_id(listing_id)
    if not listing:
        return jsonify({"error": "listing not found"}), 404
    return jsonify(listing.to_dict()), 200


@api_bp.put("/listings/<int:listing_id>")
@jwt_required()
def put_listing(listing_id: int):
    listing = ListingRepository.get_by_id(listing_id)
    if not listing:
        return jsonify({"error": "listing not found"}), 404

    payload = request.get_json(silent=True) or {}
    try:
        update_listing(listing, payload)
    except (TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(listing.to_dict()), 200


@api_bp.delete("/listings/<int:listing_id>")
@jwt_required()
def delete_listing(listing_id: int):
    listing = ListingRepository.get_by_id(listing_id)
    if not listing:
        return jsonify({"error": "listing not found"}), 404

    db.session.delete(listing)
    db.session.commit()
    return jsonify({"message": "listing deleted"}), 200


@api_bp.post("/ingestion/listings")
@jwt_required()
def post_ingestion_listings():
    payload = request.get_json(silent=True) or {}
    try:
        listings, matches = ingest_listings(payload)
    except (TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    return (
        jsonify(
            {
                "storedListings": [listing.to_dict() for listing in listings],
                "createdMatches": [match.to_dict() for match in matches],
                "matchCount": len(matches),
            }
        ),
        201,
    )


@api_bp.get("/matches")
@jwt_required()
def list_matches():
    matches = MatchRepository.list_for_user(current_user_id())
    return jsonify({"items": [match.to_dict() for match in matches]}), 200


@api_bp.post("/matches")
@jwt_required()
def post_match():
    payload = request.get_json(silent=True) or {}
    try:
        match = create_match(current_user_id(), payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(match.to_dict()), 201


@api_bp.get("/matches/<int:match_id>")
@jwt_required()
def get_match(match_id: int):
    match = MatchRepository.get_for_user(match_id, current_user_id())
    if not match:
        return jsonify({"error": "match not found"}), 404
    return jsonify(match.to_dict()), 200


@api_bp.put("/matches/<int:match_id>")
@jwt_required()
def put_match(match_id: int):
    match = MatchRepository.get_for_user(match_id, current_user_id())
    if not match:
        return jsonify({"error": "match not found"}), 404

    payload = request.get_json(silent=True) or {}
    try:
        update_match_status(match, payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(match.to_dict()), 200


@api_bp.delete("/matches/<int:match_id>")
@jwt_required()
def delete_match(match_id: int):
    match = MatchRepository.get_for_user(match_id, current_user_id())
    if not match:
        return jsonify({"error": "match not found"}), 404

    db.session.delete(match)
    db.session.commit()
    return jsonify({"message": "match deleted"}), 200

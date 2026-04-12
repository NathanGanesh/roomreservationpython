from __future__ import annotations

import json
from decimal import Decimal
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from . import db
from .models import AlertRule, Listing, Match, User
from .repositories import (
    AlertRuleRepository,
    ListingRepository,
    MatchRepository,
    UserRepository,
)


def parse_iso_datetime(value):
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def require_json_object(payload, message: str):
    if not isinstance(payload, dict):
        raise ValueError(message)
    return payload


def normalize_required_text(value, field_name: str) -> str:
    normalized = (value or "").strip().lower()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def normalize_optional_text(value) -> str | None:
    normalized = (value or "").strip().lower()
    return normalized or None


def normalize_optional_price(value) -> float | None:
    if value in (None, ""):
        return None
    return float(Decimal(str(value)))


def price_signature_token(value: float | None) -> str | None:
    if value is None:
        return None
    return format(Decimal(str(value)).normalize(), "f")


def validate_price_range(min_price: float | None, max_price: float | None) -> None:
    if min_price is not None and max_price is not None and max_price < min_price:
        raise ValueError("maxPrice must be greater than or equal to minPrice")


def normalize_active(value, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return bool(value)


def build_alert_rule_signature(
    *,
    keyword: str,
    category: str | None,
    min_price: float | None,
    max_price: float | None,
    location: str | None,
    active: bool,
) -> str:
    return json.dumps(
        {
            "active": active,
            "category": category,
            "keyword": keyword,
            "location": location,
            "maxPrice": price_signature_token(max_price),
            "minPrice": price_signature_token(min_price),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def apply_alert_rule_payload(rule: AlertRule, payload: dict, *, default_active: bool | None = None) -> str:
    keyword = (
        normalize_required_text(payload.get("keyword"), "keyword")
        if "keyword" in payload or rule.id is None
        else rule.keyword
    )
    category = (
        normalize_optional_text(payload.get("category"))
        if "category" in payload or rule.id is None
        else rule.category
    )
    min_price = (
        normalize_optional_price(payload.get("minPrice"))
        if "minPrice" in payload or rule.id is None
        else rule.min_price
    )
    max_price = (
        normalize_optional_price(payload.get("maxPrice"))
        if "maxPrice" in payload or rule.id is None
        else rule.max_price
    )
    location = (
        normalize_optional_text(payload.get("location"))
        if "location" in payload or rule.id is None
        else rule.location
    )
    active = (
        normalize_active(
            payload.get("active"),
            default=default_active if default_active is not None else True,
        )
        if "active" in payload or rule.id is None
        else rule.active
    )

    validate_price_range(min_price, max_price)

    rule.keyword = keyword
    rule.category = category
    rule.min_price = min_price
    rule.max_price = max_price
    rule.location = location
    rule.active = active
    rule.signature = build_alert_rule_signature(
        keyword=keyword,
        category=category,
        min_price=min_price,
        max_price=max_price,
        location=location,
        active=active,
    )
    return rule.signature


def register_user(payload: dict) -> User:
    email = (payload.get("email") or "").strip().lower()
    first_name = (payload.get("firstName") or "").strip()
    last_name = (payload.get("lastName") or "").strip()
    password = payload.get("password") or ""

    if not email or not first_name or not last_name or not password:
        raise ValueError("email, firstName, lastName and password are required")
    if len(password) < 8:
        raise ValueError("password must be at least 8 characters")
    if UserRepository.get_by_email(email):
        raise ValueError("email already exists")

    user = User(email=email, first_name=first_name, last_name=last_name)
    user.set_password(password)
    UserRepository.add(user)
    db.session.commit()
    return user


def authenticate_user(email: str, password: str) -> User | None:
    user = UserRepository.get_by_email((email or "").strip().lower())
    if not user or not user.check_password(password or ""):
        return None
    return user


def update_user(user: User, payload: dict) -> User:
    email = payload.get("email")
    if email:
        email = email.strip().lower()
        existing = UserRepository.get_by_email(email)
        if existing and existing.id != user.id:
            raise ValueError("email already exists")
        user.email = email

    if payload.get("firstName"):
        user.first_name = payload["firstName"].strip()
    if payload.get("lastName"):
        user.last_name = payload["lastName"].strip()
    if payload.get("password"):
        if len(payload["password"]) < 8:
            raise ValueError("password must be at least 8 characters")
        user.set_password(payload["password"])

    db.session.commit()
    return user


def create_alert_rule(user_id: int, payload: dict) -> AlertRule:
    rule = AlertRule(user_id=user_id, signature="")
    signature = apply_alert_rule_payload(rule, payload, default_active=True)
    if AlertRuleRepository.find_duplicate_for_user(user_id, signature):
        raise ValueError("alert rule already exists")
    AlertRuleRepository.add(rule)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ValueError("alert rule already exists") from exc
    return rule


def update_alert_rule(rule: AlertRule, payload: dict) -> AlertRule:
    signature = apply_alert_rule_payload(rule, payload)
    if AlertRuleRepository.find_duplicate_for_user(rule.user_id, signature, exclude_rule_id=rule.id):
        db.session.rollback()
        raise ValueError("alert rule already exists")
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ValueError("alert rule already exists") from exc
    return rule


def build_listing(payload: dict, current: Listing | None = None) -> Listing:
    payload = require_json_object(payload, "listing payload must be a JSON object")
    listing = current or Listing()
    listing.external_id = (payload.get("externalId") or "").strip()
    listing.source_name = (payload.get("sourceName") or "marktplaats").strip()
    listing.title = (payload.get("title") or "").strip()
    listing.description = (payload.get("description") or "").strip() or None
    listing.price = float(payload.get("price"))
    listing.currency = (payload.get("currency") or "EUR").strip()
    listing.city = (payload.get("city") or "").strip() or None
    listing.url = (payload.get("url") or "").strip()
    listing.posted_at = parse_iso_datetime(payload.get("postedAt"))

    if not listing.external_id or not listing.title or not listing.url:
        raise ValueError("externalId, title and url are required")
    return listing


def create_listing(payload: dict) -> Listing:
    payload = require_json_object(payload, "listing payload must be a JSON object")
    existing = ListingRepository.get_by_source_external_id(
        (payload.get("sourceName") or "marktplaats").strip(),
        (payload.get("externalId") or "").strip(),
    )
    if existing:
        raise ValueError("listing already exists")

    listing = build_listing(payload)
    ListingRepository.add(listing)
    db.session.commit()
    return listing


def update_listing(listing: Listing, payload: dict) -> Listing:
    build_listing(payload, current=listing)
    db.session.commit()
    return listing


def listing_matches_rule(listing: Listing, rule: AlertRule) -> bool:
    haystack = f"{listing.title or ''} {listing.description or ''}".lower()
    if rule.keyword.lower() not in haystack:
        return False
    if rule.category and (listing.description or "").lower().find(rule.category.lower()) == -1:
        return False
    if rule.location and (listing.city or "").lower().find(rule.location.lower()) == -1:
        return False
    if rule.min_price is not None and listing.price < rule.min_price:
        return False
    if rule.max_price is not None and listing.price > rule.max_price:
        return False
    return True


def evaluate_listing(listing: Listing):
    created_matches = []
    for rule in AlertRuleRepository.list_active():
        if not listing_matches_rule(listing, rule):
            continue
        existing = MatchRepository.find_existing(rule.id, listing.id)
        if existing:
            continue
        match = Match(alert_rule_id=rule.id, listing_id=listing.id)
        MatchRepository.add(match)
        created_matches.append(match)
    return created_matches


def create_match(user_id: int, payload: dict) -> Match:
    alert_rule_id = payload.get("alertRuleId")
    listing_id = payload.get("listingId")
    if alert_rule_id is None or listing_id is None:
        raise ValueError("alertRuleId and listingId are required")

    rule = AlertRuleRepository.get_for_user(int(alert_rule_id), user_id)
    if not rule:
        raise ValueError("alert rule not found")

    listing = ListingRepository.get_by_id(int(listing_id))
    if not listing:
        raise ValueError("listing not found")

    existing = MatchRepository.find_existing(rule.id, listing.id)
    if existing:
        raise ValueError("match already exists")

    match = Match(alert_rule_id=rule.id, listing_id=listing.id)
    MatchRepository.add(match)
    db.session.commit()
    return match


def ingest_listings(payload: dict):
    payload = require_json_object(payload, "payload must be a JSON object with a listings field")
    listings_payload = payload.get("listings") or []
    if not isinstance(listings_payload, list) or not listings_payload:
        raise ValueError("listings must be a non-empty array")

    stored_listings = []
    created_matches = []
    for item in listings_payload:
        require_json_object(item, "each listing must be a JSON object")
        source_name = (item.get("sourceName") or "marktplaats").strip()
        external_id = (item.get("externalId") or "").strip()
        existing = ListingRepository.get_by_source_external_id(source_name, external_id)
        listing = build_listing(item, current=existing) if existing else build_listing(item)
        if not existing:
            ListingRepository.add(listing)
        stored_listings.append(listing)

    db.session.flush()

    for listing in stored_listings:
        created_matches.extend(evaluate_listing(listing))

    db.session.commit()
    return stored_listings, created_matches


def update_match_status(match: Match, payload: dict) -> Match:
    status = (payload.get("status") or "").strip().lower()
    if status not in {"new", "reviewed", "dismissed", "acted_on"}:
        raise ValueError("status must be one of: new, reviewed, dismissed, acted_on")
    match.status = status
    db.session.commit()
    return match

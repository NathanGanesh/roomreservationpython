from __future__ import annotations

from datetime import UTC, datetime

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
    keyword = (payload.get("keyword") or "").strip()
    if not keyword:
        raise ValueError("keyword is required")

    rule = AlertRule(
        user_id=user_id,
        keyword=keyword,
        category=(payload.get("category") or "").strip() or None,
        min_price=payload.get("minPrice"),
        max_price=payload.get("maxPrice"),
        location=(payload.get("location") or "").strip() or None,
        active=payload.get("active", True),
    )
    AlertRuleRepository.add(rule)
    db.session.commit()
    return rule


def update_alert_rule(rule: AlertRule, payload: dict) -> AlertRule:
    if "keyword" in payload:
        keyword = (payload.get("keyword") or "").strip()
        if not keyword:
            raise ValueError("keyword cannot be blank")
        rule.keyword = keyword

    if "category" in payload:
        rule.category = (payload.get("category") or "").strip() or None
    if "minPrice" in payload:
        rule.min_price = payload.get("minPrice")
    if "maxPrice" in payload:
        rule.max_price = payload.get("maxPrice")
    if "location" in payload:
        rule.location = (payload.get("location") or "").strip() or None
    if "active" in payload:
        rule.active = bool(payload.get("active"))

    db.session.commit()
    return rule


def build_listing(payload: dict, current: Listing | None = None) -> Listing:
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
    listings_payload = payload.get("listings") or []
    if not isinstance(listings_payload, list) or not listings_payload:
        raise ValueError("listings must be a non-empty array")

    stored_listings = []
    created_matches = []
    for item in listings_payload:
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

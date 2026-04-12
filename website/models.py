from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from . import db


class SerializableMixin:
    def _serialize_datetime(self, value):
        return value.isoformat() if value else None


class User(db.Model, SerializableMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    alert_rules = db.relationship(
        "AlertRule", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "active": self.active,
            "createdAt": self._serialize_datetime(self.created_at),
        }


class AlertRule(db.Model, SerializableMixin):
    __table_args__ = (UniqueConstraint("user_id", "signature", name="uq_alert_rule_user_signature"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    keyword = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(120), nullable=True)
    min_price = db.Column(db.Float, nullable=True)
    max_price = db.Column(db.Float, nullable=True)
    location = db.Column(db.String(120), nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    signature = db.Column(db.String(512), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    user = db.relationship("User", back_populates="alert_rules")
    matches = db.relationship(
        "Match", back_populates="alert_rule", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.user_id,
            "keyword": self.keyword,
            "category": self.category,
            "minPrice": self.min_price,
            "maxPrice": self.max_price,
            "location": self.location,
            "active": self.active,
            "createdAt": self._serialize_datetime(self.created_at),
        }


class Listing(db.Model, SerializableMixin):
    __table_args__ = (UniqueConstraint("source_name", "external_id"),)

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(150), nullable=False)
    source_name = db.Column(db.String(120), nullable=False, default="marktplaats")
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="EUR")
    city = db.Column(db.String(120), nullable=True)
    url = db.Column(db.String(512), nullable=False)
    posted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    ingested_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    matches = db.relationship("Match", back_populates="listing", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "externalId": self.external_id,
            "sourceName": self.source_name,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "currency": self.currency,
            "city": self.city,
            "url": self.url,
            "postedAt": self._serialize_datetime(self.posted_at),
            "ingestedAt": self._serialize_datetime(self.ingested_at),
        }


class Match(db.Model, SerializableMixin):
    __table_args__ = (UniqueConstraint("alert_rule_id", "listing_id"),)

    id = db.Column(db.Integer, primary_key=True)
    alert_rule_id = db.Column(db.Integer, db.ForeignKey("alert_rule.id"), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey("listing.id"), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="new")
    matched_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    alert_rule = db.relationship("AlertRule", back_populates="matches")
    listing = db.relationship("Listing", back_populates="matches")

    def to_dict(self):
        return {
            "id": self.id,
            "alertRuleId": self.alert_rule_id,
            "listingId": self.listing_id,
            "status": self.status,
            "matchedAt": self._serialize_datetime(self.matched_at),
            "listing": self.listing.to_dict() if self.listing else None,
        }

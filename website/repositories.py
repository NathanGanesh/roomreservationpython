from sqlalchemy import select

from . import db
from .models import AlertRule, Listing, Match, User


class UserRepository:
    @staticmethod
    def get_by_id(user_id: int):
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_email(email: str):
        return db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()

    @staticmethod
    def add(user: User):
        db.session.add(user)
        return user


class AlertRuleRepository:
    @staticmethod
    def list_for_user(user_id: int):
        statement = select(AlertRule).where(AlertRule.user_id == user_id).order_by(AlertRule.id)
        return list(db.session.execute(statement).scalars())

    @staticmethod
    def get_for_user(rule_id: int, user_id: int):
        statement = select(AlertRule).where(
            AlertRule.id == rule_id,
            AlertRule.user_id == user_id,
        )
        return db.session.execute(statement).scalar_one_or_none()

    @staticmethod
    def find_duplicate_for_user(user_id: int, signature: str, exclude_rule_id: int | None = None):
        statement = select(AlertRule).where(
            AlertRule.user_id == user_id,
            AlertRule.signature == signature,
        )
        if exclude_rule_id is not None:
            statement = statement.where(AlertRule.id != exclude_rule_id)
        with db.session.no_autoflush:
            return db.session.execute(statement).scalar_one_or_none()

    @staticmethod
    def list_active():
        statement = select(AlertRule).where(AlertRule.active.is_(True))
        return list(db.session.execute(statement).scalars())

    @staticmethod
    def add(rule: AlertRule):
        db.session.add(rule)
        return rule


class ListingRepository:
    @staticmethod
    def list_all():
        return list(db.session.execute(select(Listing).order_by(Listing.id)).scalars())

    @staticmethod
    def get_by_id(listing_id: int):
        return db.session.get(Listing, listing_id)

    @staticmethod
    def get_by_source_external_id(source_name: str, external_id: str):
        statement = select(Listing).where(
            Listing.source_name == source_name,
            Listing.external_id == external_id,
        )
        return db.session.execute(statement).scalar_one_or_none()

    @staticmethod
    def add(listing: Listing):
        db.session.add(listing)
        return listing


class MatchRepository:
    @staticmethod
    def list_for_user(user_id: int):
        statement = (
            select(Match)
            .join(Match.alert_rule)
            .where(AlertRule.user_id == user_id)
            .order_by(Match.id)
        )
        return list(db.session.execute(statement).scalars())

    @staticmethod
    def get_for_user(match_id: int, user_id: int):
        statement = (
            select(Match)
            .join(Match.alert_rule)
            .where(Match.id == match_id, AlertRule.user_id == user_id)
        )
        return db.session.execute(statement).scalar_one_or_none()

    @staticmethod
    def find_existing(alert_rule_id: int, listing_id: int):
        statement = select(Match).where(
            Match.alert_rule_id == alert_rule_id, Match.listing_id == listing_id
        )
        return db.session.execute(statement).scalar_one_or_none()

    @staticmethod
    def add(match: Match):
        db.session.add(match)
        return match

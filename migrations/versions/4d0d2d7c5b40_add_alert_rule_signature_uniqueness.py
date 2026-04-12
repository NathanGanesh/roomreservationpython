"""add alert rule signature uniqueness

Revision ID: 4d0d2d7c5b40
Revises: c3c46c0b876a
Create Date: 2026-04-09 14:05:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4d0d2d7c5b40"
down_revision = "c3c46c0b876a"
branch_labels = None
depends_on = None


def price_token_sql(column_name: str) -> str:
    return (
        f"CASE WHEN {column_name} IS NULL THEN '' "
        f"ELSE trim(trailing '.' from trim(trailing '0' from ({column_name}::numeric)::text)) END"
    )


SIGNATURE_SQL = f"""
'{{"active":' || CASE WHEN active THEN 'true' ELSE 'false' END ||
',"category":' || CASE WHEN category IS NULL THEN 'null' ELSE to_jsonb(category)::text END ||
',"keyword":' || to_jsonb(keyword)::text ||
',"location":' || CASE WHEN location IS NULL THEN 'null' ELSE to_jsonb(location)::text END ||
',"maxPrice":' || CASE WHEN max_price IS NULL THEN 'null' ELSE to_jsonb({price_token_sql("max_price")})::text END ||
',"minPrice":' || CASE WHEN min_price IS NULL THEN 'null' ELSE to_jsonb({price_token_sql("min_price")})::text END ||
'}}'
"""


def upgrade():
    op.add_column("alert_rule", sa.Column("signature", sa.String(length=512), nullable=True))

    op.execute(
        f"""
        UPDATE alert_rule
        SET keyword = trim(lower(keyword)),
            category = NULLIF(trim(lower(category)), ''),
            location = NULLIF(trim(lower(location)), ''),
            signature = {SIGNATURE_SQL}
        """
    )

    op.execute(
        """
        DELETE FROM alert_rule duplicate
        USING alert_rule original
        WHERE duplicate.user_id = original.user_id
          AND duplicate.signature = original.signature
          AND duplicate.id > original.id
        """
    )

    op.alter_column("alert_rule", "signature", nullable=False)
    op.create_unique_constraint(
        "uq_alert_rule_user_signature",
        "alert_rule",
        ["user_id", "signature"],
    )


def downgrade():
    op.drop_constraint("uq_alert_rule_user_signature", "alert_rule", type_="unique")
    op.drop_column("alert_rule", "signature")

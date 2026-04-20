"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-19 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision: str | None = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String),
        sa.Column("tz", sa.String),
    )
    op.create_table(
        "providers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, unique=True, nullable=False),
    )
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("address", sa.String, nullable=False),
        sa.Column("latitude", sa.Float),
        sa.Column("longitude", sa.Float),
        sa.Column("nickname", sa.String),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.UniqueConstraint("user_id", "nickname", name="uq_location_nickname_per_user"),
    )
    op.create_table(
        "trips",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("start_location_id", sa.Integer, sa.ForeignKey("locations.id")),
        sa.Column("end_location_id", sa.Integer, sa.ForeignKey("locations.id")),
        sa.Column("duration", sa.Float),
        sa.Column("duration_in_traffic", sa.Float),
        sa.Column("distance", sa.Float),
        sa.Column("steps", sa.Integer),
        sa.Column("fuel_used", sa.Float),
        sa.Column("provider_id", sa.Integer, sa.ForeignKey("providers.id")),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
    )
    op.create_table(
        "trip_api_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider_id", sa.Integer, sa.ForeignKey("providers.id")),
        sa.Column("start_location_id", sa.Integer, sa.ForeignKey("locations.id")),
        sa.Column("end_location_id", sa.Integer, sa.ForeignKey("locations.id")),
        sa.Column("raw_json", sa.JSON, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("trip_api_logs")
    op.drop_table("trips")
    op.drop_table("locations")
    op.drop_table("providers")
    op.drop_table("users")

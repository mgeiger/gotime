"""trip indexes and timestamp server defaults

Adds the idempotency/dedup constraints and the hot-path indexes that
``scripts/merge/seed_canonical.sql`` has always shipped, plus a
``server_default`` of ``CURRENT_TIMESTAMP`` on both timestamp columns so
the ORM schema matches the canonical SQL layout used by the merge
importers. Uses ``batch_alter_table`` so SQLite can replay the migration
via its copy-and-move strategy.

Revision ID: 0002_trip_indexes_and_defaults
Revises: 0001_initial
Create Date: 2026-04-20 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_trip_indexes_and_defaults"
down_revision: str | None = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ``trips`` picks up the dedup unique, the hot-path indexes, and a
    # server-side default on ``timestamp``. Batch mode keeps SQLite happy.
    with op.batch_alter_table("trips") as batch:
        batch.create_unique_constraint(
            "uq_trip_dedup",
            ["provider_id", "timestamp", "start_location_id", "end_location_id"],
        )
        batch.create_index("ix_trip_timestamp", ["timestamp"])
        batch.create_index("ix_trip_provider", ["provider_id"])
        batch.alter_column(
            "timestamp",
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )

    with op.batch_alter_table("trip_api_logs") as batch:
        batch.alter_column(
            "timestamp",
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )


def downgrade() -> None:
    with op.batch_alter_table("trip_api_logs") as batch:
        batch.alter_column(
            "timestamp",
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            server_default=None,
        )

    with op.batch_alter_table("trips") as batch:
        batch.alter_column(
            "timestamp",
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            server_default=None,
        )
        batch.drop_index("ix_trip_provider")
        batch.drop_index("ix_trip_timestamp")
        batch.drop_constraint("uq_trip_dedup", type_="unique")

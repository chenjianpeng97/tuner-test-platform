"""add_features_root_to_project_git_configs

Revision ID: 6a1b2c3d4e5f
Revises: 5e6f708192a3
Create Date: 2026-03-13 17:05:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "6a1b2c3d4e5f"
down_revision = "5e6f708192a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "project_git_configs",
        sa.Column(
            "features_root",
            sa.String(length=255),
            nullable=False,
            server_default="features/",
        ),
    )


def downgrade() -> None:
    op.drop_column("project_git_configs", "features_root")

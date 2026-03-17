"""add_project_behave_configs_and_features

Revision ID: 2b3c4d5e6f70
Revises: 1a2b3c4d5e6f
Create Date: 2026-03-13 12:05:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2b3c4d5e6f70"
down_revision: Union[str, None] = "1a2b3c4d5e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_behave_configs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("behave_work_dir", sa.String(length=1024), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_project_behave_configs_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_behave_configs")),
        sa.UniqueConstraint(
            "project_id", name=op.f("uq_project_behave_configs_project_id")
        ),
    )

    op.create_table(
        "features",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("git_sha", sa.String(length=64), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("feature_name", sa.String(length=255), nullable=False),
        sa.Column("parent_feature_id", sa.UUID(), nullable=True),
        sa.Column("depth", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_features_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_feature_id"],
            ["features.id"],
            name=op.f("fk_features_parent_feature_id_features"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_features")),
        sa.UniqueConstraint(
            "project_id",
            "file_path",
            name=op.f("uq_features_project_id_file_path"),
        ),
    )
    op.create_index(op.f("ix_features_project_id"), "features", ["project_id"])
    op.create_index(
        op.f("ix_features_parent_feature_id"), "features", ["parent_feature_id"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_features_parent_feature_id"), table_name="features")
    op.drop_index(op.f("ix_features_project_id"), table_name="features")
    op.drop_table("features")
    op.drop_table("project_behave_configs")

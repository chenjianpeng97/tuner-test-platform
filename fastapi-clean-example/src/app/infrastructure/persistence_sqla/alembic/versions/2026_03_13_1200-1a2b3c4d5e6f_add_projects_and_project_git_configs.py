"""add_projects_and_project_git_configs

Revision ID: 1a2b3c4d5e6f
Revises: ef74f02cc8ff
Create Date: 2026-03-13 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1a2b3c4d5e6f"
down_revision: Union[str, None] = "ef74f02cc8ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
        sa.UniqueConstraint("name", name=op.f("uq_projects_name")),
    )

    op.create_table(
        "project_git_configs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("git_repo_url", sa.String(length=512), nullable=False),
        sa.Column("git_branch", sa.String(length=128), nullable=False),
        sa.Column("git_access_token_encrypted", sa.LargeBinary(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_project_git_configs_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_git_configs")),
        sa.UniqueConstraint(
            "project_id", name=op.f("uq_project_git_configs_project_id")
        ),
    )


def downgrade() -> None:
    op.drop_table("project_git_configs")
    op.drop_table("projects")

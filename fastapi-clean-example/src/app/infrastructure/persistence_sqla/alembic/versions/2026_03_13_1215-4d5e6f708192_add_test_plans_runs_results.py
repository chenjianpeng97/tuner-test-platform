"""add_test_plans_runs_results

Revision ID: 4d5e6f708192
Revises: 3c4d5e6f7081
Create Date: 2026-03-13 12:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "4d5e6f708192"
down_revision: Union[str, None] = "3c4d5e6f7081"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "test_plans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_test_plans_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_plans")),
    )
    op.create_index(op.f("ix_test_plans_project_id"), "test_plans", ["project_id"])

    op.create_table(
        "test_plan_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("test_plan_id", sa.UUID(), nullable=False),
        sa.Column("scenario_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["scenario_id"],
            ["scenarios.id"],
            name=op.f("fk_test_plan_items_scenario_id_scenarios"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["test_plan_id"],
            ["test_plans.id"],
            name=op.f("fk_test_plan_items_test_plan_id_test_plans"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_plan_items")),
        sa.UniqueConstraint(
            "test_plan_id",
            "scenario_id",
            name=op.f("uq_test_plan_items_test_plan_id_scenario_id"),
        ),
    )

    op.create_table(
        "test_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("test_plan_id", sa.UUID(), nullable=True),
        sa.Column(
            "triggered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("scope_value", sa.String(length=255), nullable=True),
        sa.Column(
            "executor_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("log_path", sa.String(length=1024), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_test_runs_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["test_plan_id"],
            ["test_plans.id"],
            name=op.f("fk_test_runs_test_plan_id_test_plans"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_runs")),
    )
    op.create_index(op.f("ix_test_runs_project_id"), "test_runs", ["project_id"])

    op.create_table(
        "test_run_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("test_run_id", sa.UUID(), nullable=False),
        sa.Column("scenario_id", sa.UUID(), nullable=True),
        sa.Column("feature_name", sa.String(length=255), nullable=False),
        sa.Column("scenario_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("duration_seconds", sa.Numeric(10, 3), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("stack_trace", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["scenario_id"],
            ["scenarios.id"],
            name=op.f("fk_test_run_results_scenario_id_scenarios"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["test_run_id"],
            ["test_runs.id"],
            name=op.f("fk_test_run_results_test_run_id_test_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_run_results")),
    )


def downgrade() -> None:
    op.drop_table("test_run_results")
    op.drop_index(op.f("ix_test_runs_project_id"), table_name="test_runs")
    op.drop_table("test_runs")
    op.drop_table("test_plan_items")
    op.drop_index(op.f("ix_test_plans_project_id"), table_name="test_plans")
    op.drop_table("test_plans")

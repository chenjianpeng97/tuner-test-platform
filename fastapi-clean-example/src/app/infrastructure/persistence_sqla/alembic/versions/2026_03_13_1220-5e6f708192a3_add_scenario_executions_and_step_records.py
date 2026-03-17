"""add_scenario_executions_and_step_records

Revision ID: 5e6f708192a3
Revises: 4d5e6f708192
Create Date: 2026-03-13 12:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5e6f708192a3"
down_revision: Union[str, None] = "4d5e6f708192"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scenario_executions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("scenario_id", sa.UUID(), nullable=False),
        sa.Column("test_plan_item_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_scenario_executions_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["scenario_id"],
            ["scenarios.id"],
            name=op.f("fk_scenario_executions_scenario_id_scenarios"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["test_plan_item_id"],
            ["test_plan_items.id"],
            name=op.f("fk_scenario_executions_test_plan_item_id_test_plan_items"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scenario_executions")),
    )
    op.create_index(
        op.f("ix_scenario_executions_project_id"),
        "scenario_executions",
        ["project_id"],
    )

    op.create_table(
        "step_execution_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("scenario_execution_id", sa.UUID(), nullable=False),
        sa.Column("step_id", sa.UUID(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("execution_mode", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("stage_id", sa.UUID(), nullable=True),
        sa.Column("executor", sa.String(length=120), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["scenario_execution_id"],
            ["scenario_executions.id"],
            name=op.f(
                "fk_step_execution_records_scenario_execution_id_scenario_executions"
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["stage_id"],
            ["behave_stages.id"],
            name=op.f("fk_step_execution_records_stage_id_behave_stages"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["step_id"],
            ["steps.id"],
            name=op.f("fk_step_execution_records_step_id_steps"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_step_execution_records")),
        sa.UniqueConstraint(
            "scenario_execution_id",
            "step_order",
            name=op.f("uq_step_execution_records_scenario_execution_id_step_order"),
        ),
    )


def downgrade() -> None:
    op.drop_table("step_execution_records")
    op.drop_index(
        op.f("ix_scenario_executions_project_id"), table_name="scenario_executions"
    )
    op.drop_table("scenario_executions")

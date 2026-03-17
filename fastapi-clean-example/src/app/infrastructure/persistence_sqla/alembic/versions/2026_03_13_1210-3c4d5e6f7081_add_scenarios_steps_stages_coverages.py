"""add_scenarios_steps_stages_coverages

Revision ID: 3c4d5e6f7081
Revises: 2b3c4d5e6f70
Create Date: 2026-03-13 12:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "3c4d5e6f7081"
down_revision: Union[str, None] = "2b3c4d5e6f70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scenarios",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("feature_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("rule_name", sa.String(length=255), nullable=True),
        sa.Column("scenario_name", sa.String(length=255), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["feature_id"],
            ["features.id"],
            name=op.f("fk_scenarios_feature_id_features"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_scenarios_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scenarios")),
    )
    op.create_index(op.f("ix_scenarios_project_id"), "scenarios", ["project_id"])
    op.create_index(op.f("ix_scenarios_feature_id"), "scenarios", ["feature_id"])

    op.create_table(
        "steps",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("scenario_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("keyword", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_steps_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["scenario_id"],
            ["scenarios.id"],
            name=op.f("fk_steps_scenario_id_scenarios"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_steps")),
    )
    op.create_index(op.f("ix_steps_project_id"), "steps", ["project_id"])
    op.create_index(op.f("ix_steps_scenario_id"), "steps", ["scenario_id"])

    op.create_table(
        "behave_stages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("stage_name", sa.String(length=64), nullable=False),
        sa.Column("steps_dir_path", sa.String(length=1024), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_behave_stages_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_behave_stages")),
        sa.UniqueConstraint(
            "project_id",
            "stage_name",
            name=op.f("uq_behave_stages_project_id_stage_name"),
        ),
    )

    op.create_table(
        "step_coverages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("step_id", sa.UUID(), nullable=False),
        sa.Column("stage_id", sa.UUID(), nullable=False),
        sa.Column("coverage_status", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(
            ["stage_id"],
            ["behave_stages.id"],
            name=op.f("fk_step_coverages_stage_id_behave_stages"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["step_id"],
            ["steps.id"],
            name=op.f("fk_step_coverages_step_id_steps"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_step_coverages")),
        sa.UniqueConstraint(
            "step_id",
            "stage_id",
            name=op.f("uq_step_coverages_step_id_stage_id"),
        ),
    )


def downgrade() -> None:
    op.drop_table("step_coverages")
    op.drop_table("behave_stages")
    op.drop_index(op.f("ix_steps_scenario_id"), table_name="steps")
    op.drop_index(op.f("ix_steps_project_id"), table_name="steps")
    op.drop_table("steps")
    op.drop_index(op.f("ix_scenarios_feature_id"), table_name="scenarios")
    op.drop_index(op.f("ix_scenarios_project_id"), table_name="scenarios")
    op.drop_table("scenarios")

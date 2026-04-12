"""Convert planned_workouts.flexible and .completed from String to Boolean.

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-11
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "planned_workouts",
        sa.Column("flexible_bool", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.add_column(
        "planned_workouts",
        sa.Column("completed_bool", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )

    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE planned_workouts SET flexible_bool = CASE "
            "WHEN lower(flexible) IN ('true', '1', 'yes') THEN true ELSE false END"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE planned_workouts SET completed_bool = CASE "
            "WHEN lower(completed) IN ('true', '1', 'yes') THEN true ELSE false END"
        )
    )

    op.drop_column("planned_workouts", "flexible")
    op.drop_column("planned_workouts", "completed")

    op.alter_column("planned_workouts", "flexible_bool", new_column_name="flexible")
    op.alter_column("planned_workouts", "completed_bool", new_column_name="completed")


def downgrade() -> None:
    op.add_column(
        "planned_workouts",
        sa.Column("flexible_str", sa.String(), server_default="true"),
    )
    op.add_column(
        "planned_workouts",
        sa.Column("completed_str", sa.String(), server_default="false"),
    )

    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE planned_workouts SET flexible_str = CASE "
            "WHEN flexible THEN 'true' ELSE 'false' END"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE planned_workouts SET completed_str = CASE "
            "WHEN completed THEN 'true' ELSE 'false' END"
        )
    )

    op.drop_column("planned_workouts", "flexible")
    op.drop_column("planned_workouts", "completed")

    op.alter_column("planned_workouts", "flexible_str", new_column_name="flexible")
    op.alter_column("planned_workouts", "completed_str", new_column_name="completed")

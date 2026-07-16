import sqlalchemy as sa
from alembic import op

revision = "0002_proposal_moderation"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def _table_columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade():
    columns = _table_columns("proposal")

    if "user_email" not in columns:
        op.add_column("proposal", sa.Column("user_email", sa.String(length=255), nullable=True))
    if "user_name" not in columns:
        op.add_column("proposal", sa.Column("user_name", sa.String(length=255), nullable=True))
    if "validated_at" not in columns:
        op.add_column(
            "proposal",
            sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        )

    op.alter_column(
        "proposal",
        "active",
        existing_type=sa.Boolean(),
        existing_nullable=False,
        server_default=sa.text("false"),
    )


def downgrade():
    op.alter_column(
        "proposal",
        "active",
        existing_type=sa.Boolean(),
        existing_nullable=False,
        server_default=sa.text("true"),
    )

    columns = _table_columns("proposal")
    if "validated_at" in columns:
        op.drop_column("proposal", "validated_at")
    if "user_name" in columns:
        op.drop_column("proposal", "user_name")
    if "user_email" in columns:
        op.drop_column("proposal", "user_email")
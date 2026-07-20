import sqlalchemy as sa
from alembic import op

revision = "0003_image_nullable"
down_revision = "0002_proposal_moderation"
branch_labels = None
depends_on = None


def upgrade():
    # Convert existing empty-string image values to NULL before relaxing the constraint
    op.execute(sa.text("UPDATE proposal SET image = NULL WHERE image = ''"))
    op.alter_column(
        "proposal",
        "image",
        existing_type=sa.String(length=1024),
        nullable=True,
    )


def downgrade():
    # Restore empty string for any NULL images before re-adding NOT NULL constraint
    op.execute(sa.text("UPDATE proposal SET image = '' WHERE image IS NULL"))
    op.alter_column(
        "proposal",
        "image",
        existing_type=sa.String(length=1024),
        nullable=False,
    )

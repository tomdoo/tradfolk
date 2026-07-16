import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

# The enum is created explicitly in upgrade(); avoid implicit re-creation during table DDL.
vote_enum = postgresql.ENUM("trad", "folk", name="vote_value", create_type=False)


def upgrade():
    vote_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "proposal",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("libelle", sa.String(length=255), nullable=False),
        sa.Column("image", sa.String(length=1024), nullable=False),
        sa.Column("user_email", sa.String(length=255), nullable=True),
        sa.Column("user_name", sa.String(length=255), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_table(
        "vote",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "id_proposal",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("proposal.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("value", vote_enum, nullable=False),
        sa.Column("origin", sa.String(length=128), nullable=False),
        sa.Column(
            "voted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_unique_constraint("uq_vote_proposal_origin", "vote", ["id_proposal", "origin"])
    op.create_index("ix_vote_id_proposal", "vote", ["id_proposal"])
    op.create_index("ix_vote_origin", "vote", ["origin"])
    op.create_index("ix_vote_origin_id_proposal", "vote", ["origin", "id_proposal"])


def downgrade():
    op.drop_index("ix_vote_origin_id_proposal", table_name="vote")
    op.drop_index("ix_vote_origin", table_name="vote")
    op.drop_index("ix_vote_id_proposal", table_name="vote")
    op.drop_constraint("uq_vote_proposal_origin", "vote", type_="unique")
    op.drop_table("vote")
    op.drop_table("proposal")
    vote_enum.drop(op.get_bind(), checkfirst=True)

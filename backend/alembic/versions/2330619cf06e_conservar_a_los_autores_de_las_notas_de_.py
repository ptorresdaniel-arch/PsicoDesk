"""conservar a los autores de las notas de las sesiones clínicas

Revision ID: 2330619cf06e
Revises: db966ef4207d
Create Date: 2026-10-02 17:33:12.981818

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2330619cf06e"
down_revision: Union[str, Sequence[str], None] = "db966ef4207d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "clinical_session_notes_created_by_fkey",
        "clinical_session_notes",
        type_="foreignkey",
    )

    op.create_foreign_key(
        "clinical_session_notes_created_by_fkey",
        "clinical_session_notes",
        "users",
        ["created_by"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "clinical_session_notes_created_by_fkey",
        "clinical_session_notes",
        type_="foreignkey",
    )

    op.create_foreign_key(
        "clinical_session_notes_created_by_fkey",
        "clinical_session_notes",
        "users",
        ["created_by"],
        ["id"],
        ondelete="CASCADE",
    )
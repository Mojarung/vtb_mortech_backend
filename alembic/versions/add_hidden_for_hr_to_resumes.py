"""add hidden_for_hr to resumes

Revision ID: add_hidden_for_hr
Revises: edbe5fb67599
Create Date: 2025-09-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_hidden_for_hr'
down_revision: Union[str, Sequence[str], None] = 'edbe5fb67599'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('resumes', sa.Column('hidden_for_hr', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column('resumes', 'hidden_for_hr')



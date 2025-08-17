"""Merge migration heads

Revision ID: 9f49c241529f
Revises: ca54b7cb43e1, ce98fe37e307
Create Date: 2025-08-17 05:31:53.066466

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f49c241529f'
down_revision: Union[str, None] = ('ca54b7cb43e1', 'ce98fe37e307')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

"""add_deleted_status_to_job_status_enum

Revision ID: fe31121f9555
Revises: 411cc655f122
Create Date: 2025-08-17 04:38:32.791030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe31121f9555'
down_revision: Union[str, None] = '411cc655f122'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'deleted' value to job_status enum
    op.execute("ALTER TYPE job_status ADD VALUE 'deleted'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type, which is complex
    # For now, we'll leave the enum value in place
    pass

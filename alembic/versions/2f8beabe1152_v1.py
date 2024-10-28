"""v1

Revision ID: 2f8beabe1152
Revises: 6586c9532005
Create Date: 2024-09-21 23:24:46.376842

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f8beabe1152'
down_revision: Union[str, None] = '6586c9532005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

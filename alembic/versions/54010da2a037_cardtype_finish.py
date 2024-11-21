"""cardtype finish

Revision ID: 54010da2a037
Revises: e6b8c2f7b6fc
Create Date: 2024-11-16 02:26:19.133211

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54010da2a037'
down_revision: Union[str, None] = 'e6b8c2f7b6fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('birthdate', sa.Date(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'birthdate')
    # ### end Alembic commands ###
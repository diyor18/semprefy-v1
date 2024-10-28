"""create services table

Revision ID: 6586c9532005
Revises: 
Create Date: 2024-08-18 11:31:58.027651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6586c9532005'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#watch FASTAPI by Sanjeev at 10:30 - 11:10
def upgrade():
    op.create_table('services', 
                    sa.Column('service_id', sa.Integer(), nullable=False, primary_key=True), 
                    sa.Column('name', sa.Integer(), nullable=False))
    pass


def downgrade():
    op.drop_table('services')
    pass

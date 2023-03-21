"""empty message

Revision ID: c234b27abc6c
Revises: a1e90f2fe69e
Create Date: 2023-03-20 14:29:17.710089

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c234b27abc6c'
down_revision = 'a1e90f2fe69e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('repartidor', schema=None) as batch_op:
        batch_op.add_column(sa.Column('latitud', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('longitud', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('repartidor', schema=None) as batch_op:
        batch_op.drop_column('longitud')
        batch_op.drop_column('latitud')

    # ### end Alembic commands ###
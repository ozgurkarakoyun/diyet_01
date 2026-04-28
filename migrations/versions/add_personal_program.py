"""add personal_program to patients

Revision ID: a1b2c3d4e5f6
Revises: 71863462c9cb
Create Date: 2026-04-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '71863462c9cb'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('patients', schema=None) as batch_op:
        batch_op.add_column(sa.Column('personal_program', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('patients', schema=None) as batch_op:
        batch_op.drop_column('personal_program')

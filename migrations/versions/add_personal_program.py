"""add personal_program to patients

Revision ID: a1b2c3d4e5f6
Revises: 71863462c9cb
Create Date: 2026-04-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = 'a1b2c3d4e5f6'
down_revision = '71863462c9cb'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('patients')]
    if 'personal_program' not in columns:
        op.add_column('patients', sa.Column('personal_program', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('patients', 'personal_program')

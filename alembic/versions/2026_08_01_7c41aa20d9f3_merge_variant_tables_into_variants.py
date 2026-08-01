"""Merge jupiter_models + chassis_models into one generic variants table.

Jupiter rows keep their six-digit SKU in the (now optional) `code` column;
chassis rows carry NULL there and keep their `img`/`bullets` card content.

Revision ID: 7c41aa20d9f3
Revises: 3b53ecace330
Create Date: 2026-08-01
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '7c41aa20d9f3'
down_revision: str | None = '3b53ecace330'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'variants',
        sa.Column('id', sa.String(length=80), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('code', sa.String(length=80), nullable=True),
        sa.Column('family', sa.String(length=80), nullable=False),
        sa.Column('rack_units', sa.String(length=10), nullable=False),
        sa.Column('img', sa.String(length=300), nullable=False),
        sa.Column('bullets', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("status IN ('available', 'roadmap')", name=op.f('ck_variants_status_valid')),
        sa.ForeignKeyConstraint(['family'], ['products.id'], name=op.f('fk_variants_family_products'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_variants')),
    )
    op.create_index(op.f('ix_variants_code'), 'variants', ['code'], unique=True)
    op.create_index(op.f('ix_variants_family'), 'variants', ['family'], unique=False)

    op.execute(
        """
        INSERT INTO variants (id, name, code, family, rack_units, img, bullets, status, created_at, updated_at)
        SELECT id, name, code, family, rack_units, '', '[]'::json, status, created_at, updated_at
        FROM jupiter_models
        """
    )
    op.execute(
        """
        INSERT INTO variants (id, name, code, family, rack_units, img, bullets, status, created_at, updated_at)
        SELECT id, model, NULL, family, ru, img, bullets, status, created_at, updated_at
        FROM chassis_models
        """
    )

    op.drop_index(op.f('ix_jupiter_models_family'), table_name='jupiter_models')
    op.drop_index(op.f('ix_jupiter_models_code'), table_name='jupiter_models')
    op.drop_table('jupiter_models')
    op.drop_index(op.f('ix_chassis_models_family'), table_name='chassis_models')
    op.drop_table('chassis_models')


def downgrade() -> None:
    op.create_table(
        'chassis_models',
        sa.Column('id', sa.String(length=80), nullable=False),
        sa.Column('model', sa.String(length=80), nullable=False),
        sa.Column('ru', sa.String(length=10), nullable=False),
        sa.Column('img', sa.String(length=300), nullable=False),
        sa.Column('bullets', sa.JSON(), nullable=False),
        sa.Column('family', sa.String(length=80), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("status IN ('available', 'roadmap')", name=op.f('ck_chassis_models_status_valid')),
        sa.ForeignKeyConstraint(['family'], ['products.id'], name=op.f('fk_chassis_models_family_products'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_chassis_models')),
    )
    op.create_index(op.f('ix_chassis_models_family'), 'chassis_models', ['family'], unique=False)
    op.create_table(
        'jupiter_models',
        sa.Column('id', sa.String(length=80), nullable=False),
        sa.Column('code', sa.String(length=6), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('family', sa.String(length=80), nullable=False),
        sa.Column('rack_units', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("status IN ('available', 'roadmap')", name=op.f('ck_jupiter_models_status_valid')),
        sa.ForeignKeyConstraint(['family'], ['products.id'], name=op.f('fk_jupiter_models_family_products'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_jupiter_models')),
    )
    op.create_index(op.f('ix_jupiter_models_code'), 'jupiter_models', ['code'], unique=True)
    op.create_index(op.f('ix_jupiter_models_family'), 'jupiter_models', ['family'], unique=False)

    # Coded variants go back to jupiter_models (codes longer than six digits
    # cannot round-trip and will fail loudly rather than silently truncate).
    op.execute(
        """
        INSERT INTO jupiter_models (id, code, name, family, rack_units, status, created_at, updated_at)
        SELECT id, code, name, family, rack_units, status, created_at, updated_at
        FROM variants WHERE code IS NOT NULL
        """
    )
    op.execute(
        """
        INSERT INTO chassis_models (id, model, ru, img, bullets, family, status, created_at, updated_at)
        SELECT id, name, rack_units, img, bullets, family, status, created_at, updated_at
        FROM variants WHERE code IS NULL
        """
    )

    op.drop_index(op.f('ix_variants_family'), table_name='variants')
    op.drop_index(op.f('ix_variants_code'), table_name='variants')
    op.drop_table('variants')

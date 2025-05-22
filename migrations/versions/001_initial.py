"""Initial database schema

Revision ID: 001_initial
Create Date: 2025-05-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create filings table
    op.create_table(
        'filings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(), nullable=False),
        sa.Column('filing_type', sa.String(), nullable=False),
        sa.Column('accession_number', sa.String(), nullable=False),
        sa.Column('filing_date', sa.DateTime(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('full_text', sa.String(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('accession_number'),
        sa.UniqueConstraint('file_path')
    )
    
    # Create indexes for filings table
    op.create_index('ix_filings_ticker', 'filings', ['ticker'])
    op.create_index('ix_filings_filing_type', 'filings', ['filing_type'])
    op.create_index('ix_filings_filing_date', 'filings', ['filing_date'])
    op.create_index('ix_filings_accession_number', 'filings', ['accession_number'])
    
    # Create metrics table
    op.create_table(
        'metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filing_id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(), nullable=True),
        sa.Column('scale', sa.String(), nullable=True),
        sa.Column('raw_value', sa.String(), nullable=True),
        sa.Column('extracted_from', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['filing_id'], ['filings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for metrics table
    op.create_index('ix_metrics_filing_id', 'metrics', ['filing_id'])
    op.create_index('ix_metrics_metric_name', 'metrics', ['metric_name'])

def downgrade():
    op.drop_index('ix_metrics_metric_name', 'metrics')
    op.drop_index('ix_metrics_filing_id', 'metrics')
    op.drop_table('metrics')
    op.drop_index('ix_filings_accession_number', 'filings')
    op.drop_index('ix_filings_filing_date', 'filings')
    op.drop_index('ix_filings_filing_type', 'filings')
    op.drop_index('ix_filings_ticker', 'filings')
    op.drop_table('filings')

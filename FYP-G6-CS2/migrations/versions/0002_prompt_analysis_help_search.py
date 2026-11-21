"""Remove vector KB and legacy helplines; add prompt versions and verified search cache."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_prompt_analysis_help_search"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade():
    op.execute("DROP TABLE IF EXISTS kb_chunks CASCADE")
    op.execute("DROP TABLE IF EXISTS kb_sources CASCADE")
    op.execute("DROP TABLE IF EXISTS helplines CASCADE")
    op.execute("DROP INDEX IF EXISTS ix_kb_chunks_embedding_hnsw")
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("ALTER TABLE message_analysis ADD COLUMN IF NOT EXISTS prompt_versions JSONB NOT NULL DEFAULT '{}'::jsonb")
    op.execute("""CREATE TABLE IF NOT EXISTS help_search_cache (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        query_key VARCHAR(64) NOT NULL UNIQUE,
        results JSONB NOT NULL DEFAULT '[]'::jsonb,
        fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        created_at TIMESTAMPTZ NOT NULL DEFAULT now())""")

def downgrade():
    op.drop_table("help_search_cache")
    op.drop_column("message_analysis", "prompt_versions")

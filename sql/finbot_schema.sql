-- FinBot Database Schema for Supabase
-- Run this in Supabase SQL Editor to create required tables

-- Documents table (main table for GR documents)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gr_no TEXT UNIQUE NOT NULL,
    date TEXT,
    branch TEXT,
    subject_en TEXT,
    subject_gu TEXT,
    pdf_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for documents
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Create policy for anonymous access (adjust as needed)
CREATE POLICY "Enable all access for authenticated users" ON documents
    FOR ALL USING (auth.role() = 'authenticated');

-- Vectors table for embeddings (if using vector search)
CREATE TABLE IF NOT EXISTS vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    embeddingvector VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for vectors
ALTER TABLE vectors ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all access for authenticated users" ON vectors
    FOR ALL USING (auth.role() = 'authenticated');

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL DEFAULT 'default',
    name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for chat_sessions
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all access for authenticated users" ON chat_sessions
    FOR ALL USING (auth.role() = 'authenticated');

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    message_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for chat_messages
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all access for authenticated users" ON chat_messages
    FOR ALL USING (auth.role() = 'authenticated');

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_documents_gr_no ON documents(gr_no);
CREATE INDEX IF NOT EXISTS idx_documents_branch ON documents(branch);
CREATE INDEX IF NOT EXISTS idx_documents_date ON documents(date);
CREATE INDEX IF NOT EXISTS idx_vectors_document_id ON vectors(document_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for documents
DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for chat_sessions
DROP TRIGGER IF EXISTS update_chat_sessions_updated_at ON chat_sessions;
CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function for semantic search (match_documents)
-- This requires the pgvector extension
-- Run: CREATE EXTENSION IF NOT EXISTS vector;

-- Example RPC function for semantic search (when pgvector is enabled)
-- CREATE OR REPLACE FUNCTION match_documents(
--     query_embedding VECTOR(1536),
--     match_threshold FLOAT,
--     match_count INT
-- )
-- RETURNS TABLE (
--     id UUID,
--     gr_no TEXT,
--     date TEXT,
--     branch TEXT,
--     subject_en TEXT,
--     subject_gu TEXT,
--     pdf_url TEXT,
--     similarity FLOAT
-- )
-- AS $$
-- BEGIN
--     RETURN QUERY
--     SELECT
--         documents.id,
--         documents.gr_no,
--         documents.date,
--         documents.branch,
--         documents.subject_en,
--         documents.subject_gu,
--         documents.pdf_url,
--         1 - (vectors.embeddingvector <=> query_embedding) AS similarity
--     FROM documents
--     JOIN vectors ON documents.id = vectors.document_id
--     WHERE 1 - (vectors.embeddingvector <=> query_embedding) > match_threshold
--     ORDER BY vectors.embeddingvector <=> query_embedding
--     LIMIT match_count;
-- END;
-- $$ LANGUAGE plpgsql;

print('Database schema created successfully!');
print('Note: For semantic search, install pgvector extension: CREATE EXTENSION IF NOT EXISTS vector;');


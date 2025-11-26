-- Supabase Vector Extension Setup for India Compliance RAG
-- This migration enables pgvector extension and creates tables for regulatory document embeddings

-- ============================================================================
-- Enable pgvector Extension
-- ============================================================================

-- Enable the pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- India Regulatory Documents Embeddings Table
-- ============================================================================

-- Create table for storing regulatory document embeddings
CREATE TABLE IF NOT EXISTS india_regulatory_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type VARCHAR(100) NOT NULL,  -- 'dpdp_act', 'niti_aayog', 'meity_guidelines', 'digital_india_act'
    section_id VARCHAR(255) NOT NULL,     -- e.g., 'DPDP_Section_6', 'NITI_Principle_1'
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),               -- OpenAI embedding dimension
    metadata JSONB,                       -- Additional metadata like citations, dates, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on document_type for faster filtering
CREATE INDEX IF NOT EXISTS idx_india_regulatory_documents_type 
    ON india_regulatory_documents(document_type);

-- Create index on section_id for direct lookups
CREATE INDEX IF NOT EXISTS idx_india_regulatory_documents_section_id 
    ON india_regulatory_documents(section_id);

-- Create HNSW index for vector similarity search (efficient for high-dimensional vectors)
CREATE INDEX IF NOT EXISTS idx_india_regulatory_documents_embedding 
    ON india_regulatory_documents 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 30, ef_construction = 100);

-- ============================================================================
-- India Compliance RAG Context Table
-- ============================================================================

-- Create table for storing RAG query context and results
CREATE TABLE IF NOT EXISTS india_compliance_rag_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    query_embedding vector(1536),
    retrieved_documents JSONB NOT NULL,  -- Array of retrieved document IDs and relevance scores
    generated_response TEXT NOT NULL,
    response_quality_score FLOAT,        -- 0-1 score for response quality
    feedback VARCHAR(50),                -- 'helpful', 'not_helpful', 'partially_helpful'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on user_id for user-specific query history
CREATE INDEX IF NOT EXISTS idx_india_compliance_rag_context_user_id 
    ON india_compliance_rag_context(user_id);

-- Create index on created_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_india_compliance_rag_context_created_at 
    ON india_compliance_rag_context(created_at DESC);

-- Create index on feedback for quality analysis
CREATE INDEX IF NOT EXISTS idx_india_compliance_rag_context_feedback 
    ON india_compliance_rag_context(feedback);

-- ============================================================================
-- Similarity Search Function
-- ============================================================================

-- Create function for cosine similarity search on regulatory documents
CREATE OR REPLACE FUNCTION search_india_regulatory_documents(
    query_embedding vector(1536),
    similarity_threshold FLOAT DEFAULT 0.5,
    limit_results INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    document_type VARCHAR,
    section_id VARCHAR,
    title VARCHAR,
    content TEXT,
    similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ird.id,
        ird.document_type,
        ird.section_id,
        ird.title,
        ird.content,
        (1 - (ird.embedding <=> query_embedding))::FLOAT as similarity,
        ird.metadata
    FROM india_regulatory_documents ird
    WHERE (1 - (ird.embedding <=> query_embedding)) > similarity_threshold
    ORDER BY ird.embedding <=> query_embedding
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Document Retrieval Function
-- ============================================================================

-- Create function to retrieve documents by type and section
CREATE OR REPLACE FUNCTION get_india_regulatory_document(
    p_document_type VARCHAR,
    p_section_id VARCHAR
)
RETURNS TABLE (
    id UUID,
    document_type VARCHAR,
    section_id VARCHAR,
    title VARCHAR,
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ird.id,
        ird.document_type,
        ird.section_id,
        ird.title,
        ird.content,
        ird.metadata,
        ird.created_at
    FROM india_regulatory_documents ird
    WHERE ird.document_type = p_document_type
    AND ird.section_id = p_section_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Batch Similarity Search Function
-- ============================================================================

-- Create function for batch similarity search (useful for multi-query scenarios)
CREATE OR REPLACE FUNCTION batch_search_india_regulatory_documents(
    query_embeddings vector(1536)[],
    similarity_threshold FLOAT DEFAULT 0.5,
    limit_results INT DEFAULT 5
)
RETURNS TABLE (
    query_index INT,
    id UUID,
    document_type VARCHAR,
    section_id VARCHAR,
    title VARCHAR,
    content TEXT,
    similarity FLOAT
) AS $$
DECLARE
    i INT;
    query_emb vector(1536);
BEGIN
    FOR i IN 1..array_length(query_embeddings, 1) LOOP
        query_emb := query_embeddings[i];
        RETURN QUERY
        SELECT 
            i as query_index,
            ird.id,
            ird.document_type,
            ird.section_id,
            ird.title,
            ird.content,
            (1 - (ird.embedding <=> query_emb))::FLOAT as similarity
        FROM india_regulatory_documents ird
        WHERE (1 - (ird.embedding <=> query_emb)) > similarity_threshold
        ORDER BY ird.embedding <=> query_emb
        LIMIT limit_results;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Document Statistics Function
-- ============================================================================

-- Create function to get statistics about indexed documents
CREATE OR REPLACE FUNCTION get_india_regulatory_documents_stats()
RETURNS TABLE (
    document_type VARCHAR,
    document_count INT,
    last_updated TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ird.document_type,
        COUNT(*)::INT as document_count,
        MAX(ird.updated_at) as last_updated
    FROM india_regulatory_documents ird
    GROUP BY ird.document_type
    ORDER BY ird.document_type;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Indexes for Performance Optimization
-- ============================================================================

-- Create composite index for document type and section lookups
CREATE INDEX IF NOT EXISTS idx_india_regulatory_documents_type_section 
    ON india_regulatory_documents(document_type, section_id);

-- Create index on updated_at for cache invalidation
CREATE INDEX IF NOT EXISTS idx_india_regulatory_documents_updated_at 
    ON india_regulatory_documents(updated_at DESC);

-- ============================================================================
-- Grant Permissions (if using role-based access)
-- ============================================================================

-- Grant select permissions on regulatory documents table
-- GRANT SELECT ON india_regulatory_documents TO authenticated;
-- GRANT SELECT ON india_compliance_rag_context TO authenticated;

-- Grant execute permissions on search functions
-- GRANT EXECUTE ON FUNCTION search_india_regulatory_documents TO authenticated;
-- GRANT EXECUTE ON FUNCTION get_india_regulatory_document TO authenticated;
-- GRANT EXECUTE ON FUNCTION batch_search_india_regulatory_documents TO authenticated;
-- GRANT EXECUTE ON FUNCTION get_india_regulatory_documents_stats TO authenticated;

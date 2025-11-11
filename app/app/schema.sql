-- Simple Database Schema for Paper Collaboration Platform
-- This schema is designed for easy understanding by students
-- No RLS (Row Level Security) - security handled in application code

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (combines authors and companies)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    user_type TEXT NOT NULL CHECK (user_type IN ('author', 'company')),

    -- Author fields (NULL for companies)
    first_name TEXT,
    last_name TEXT,
    university TEXT,

    -- Company fields (NULL for authors)
    company_name TEXT,
    address TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Papers table
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'published')) DEFAULT 'draft',
    file_path TEXT,  -- Path to the PDF file
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Paper collaborators (which authors can edit a paper)
CREATE TABLE paper_collaborators (
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (paper_id, user_id)
);

-- Paper interests (which companies are interested in which papers)
CREATE TABLE paper_interests (
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
    company_id UUID REFERENCES users(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (paper_id, company_id)
);

-- Indexes for better query performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_type ON users(user_type);
CREATE INDEX idx_papers_status ON papers(status);
CREATE INDEX idx_papers_created_by ON papers(created_by);
CREATE INDEX idx_paper_collaborators_user ON paper_collaborators(user_id);
CREATE INDEX idx_paper_collaborators_paper ON paper_collaborators(paper_id);
CREATE INDEX idx_paper_interests_company ON paper_interests(company_id);
CREATE INDEX idx_paper_interests_paper ON paper_interests(paper_id);


-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

------------------------------------------------------
-- USERS (Authors only)
------------------------------------------------------
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,

    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    university TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Additional fields
    field_of_research TEXT,
    years_of_experience INTEGER DEFAULT 0
);

------------------------------------------------------
-- COMPANIES (separate login + information)
------------------------------------------------------
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,

    company_name TEXT NOT NULL,
    address TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Additional field
    research_interests TEXT
);

------------------------------------------------------
-- PAPERS (created by authors only)
------------------------------------------------------
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'published')) DEFAULT 'draft',
    file_path TEXT,

    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

------------------------------------------------------
-- PAPER COLLABORATORS (authors only)
------------------------------------------------------
CREATE TABLE paper_collaborators (
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    PRIMARY KEY (paper_id, user_id)
);

------------------------------------------------------
-- PAPER INTERESTS (companies only)
------------------------------------------------------
CREATE TABLE paper_interests (
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Additional field
    relevance_score FLOAT DEFAULT 0.0,

    PRIMARY KEY (paper_id, company_id)
);

------------------------------------------------------
-- Indexes
------------------------------------------------------
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_companies_email ON companies(email);

CREATE INDEX idx_papers_status ON papers(status);
CREATE INDEX idx_papers_created_by ON papers(created_by);

CREATE INDEX idx_paper_collaborators_user ON paper_collaborators(user_id);
CREATE INDEX idx_paper_collaborators_paper ON paper_collaborators(paper_id);

CREATE INDEX idx_paper_interests_company ON paper_interests(company_id);
CREATE INDEX idx_paper_interests_paper ON paper_interests(paper_id);

-- Additional indexes for performance
CREATE INDEX idx_users_field_research ON users(field_of_research);
CREATE INDEX idx_users_experience ON users(years_of_experience);
CREATE INDEX idx_paper_interests_relevance ON paper_interests(relevance_score);

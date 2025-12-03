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

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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

    PRIMARY KEY (paper_id, company_id)
);

------------------------------------------------------
-- REVIEWS (both authors and companies can review)
------------------------------------------------------
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure either user_id or company_id is set, but not both
    CONSTRAINT review_author_check CHECK (
        (user_id IS NOT NULL AND company_id IS NULL) OR
        (user_id IS NULL AND company_id IS NOT NULL)
    ),
    
    -- Prevent duplicate reviews from same user/company on same paper
    CONSTRAINT unique_user_review UNIQUE (paper_id, user_id),
    CONSTRAINT unique_company_review UNIQUE (paper_id, company_id)
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

CREATE INDEX idx_reviews_paper ON reviews(paper_id);
CREATE INDEX idx_reviews_user ON reviews(user_id);
CREATE INDEX idx_reviews_company ON reviews(company_id);

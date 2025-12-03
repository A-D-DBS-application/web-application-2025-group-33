------------------------------------------------------
-- REVIEWS TABLE
-- Allows both authors and companies to review papers
------------------------------------------------------

CREATE TABLE IF NOT EXISTS reviews (
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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_reviews_paper ON reviews(paper_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user ON reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_company ON reviews(company_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);


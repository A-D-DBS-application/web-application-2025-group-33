-- Migration: Add subject column to papers table
-- Run this SQL in your Supabase SQL Editor

ALTER TABLE papers ADD COLUMN IF NOT EXISTS subject VARCHAR(500);

-- Create index for better search performance
CREATE INDEX IF NOT EXISTS idx_papers_subject ON papers(subject);



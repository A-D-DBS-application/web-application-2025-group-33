-- Migration: Add download_count column to papers table
-- Run this in Supabase SQL Editor

ALTER TABLE papers ADD COLUMN IF NOT EXISTS download_count INTEGER DEFAULT 0;

-- Update existing papers to have 0 downloads
UPDATE papers SET download_count = 0 WHERE download_count IS NULL;


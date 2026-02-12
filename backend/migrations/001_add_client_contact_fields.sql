-- Migration: Add client contact and metadata fields
-- Date: 2026-02-12
-- Description: Adds industry, start_date, address, contact_person, and contact_email to clients table

-- Add new columns to clients table
ALTER TABLE clients 
ADD COLUMN IF NOT EXISTS industry VARCHAR(100),
ADD COLUMN IF NOT EXISTS start_date VARCHAR(10),
ADD COLUMN IF NOT EXISTS address VARCHAR(500),
ADD COLUMN IF NOT EXISTS contact_person VARCHAR(200),
ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255);

-- Create index on industry for filtering
CREATE INDEX IF NOT EXISTS idx_clients_industry ON clients(industry);

-- Update existing clients to have default start_date if needed
UPDATE clients SET start_date = '2026-01-01' WHERE start_date IS NULL AND is_demo = false;

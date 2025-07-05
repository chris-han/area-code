-- Setup script for enabling PostgreSQL realtime changes on foo and bar tables
-- This script follows the Supabase documentation for setting up realtime
-- Run this script after setting up your database tables

-- Enable Row Level Security for the foo table
ALTER TABLE "foo" ENABLE ROW LEVEL SECURITY;

-- Enable Row Level Security for the bar table
ALTER TABLE "bar" ENABLE ROW LEVEL SECURITY;

-- Create policies for foo table
-- Allow authenticated users to read all foo records
CREATE POLICY "Allow authenticated users to read foo"
ON "foo"
FOR SELECT
TO authenticated
USING (true);

-- Allow authenticated users to insert foo records
CREATE POLICY "Allow authenticated users to insert foo"
ON "foo"
FOR INSERT
TO authenticated
WITH CHECK (true);

-- Allow authenticated users to update foo records
CREATE POLICY "Allow authenticated users to update foo"
ON "foo"
FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

-- Allow authenticated users to delete foo records
CREATE POLICY "Allow authenticated users to delete foo"
ON "foo"
FOR DELETE
TO authenticated
USING (true);

-- Create policies for bar table
-- Allow authenticated users to read all bar records
CREATE POLICY "Allow authenticated users to read bar"
ON "bar"
FOR SELECT
TO authenticated
USING (true);

-- Allow authenticated users to insert bar records
CREATE POLICY "Allow authenticated users to insert bar"
ON "bar"
FOR INSERT
TO authenticated
WITH CHECK (true);

-- Allow authenticated users to update bar records
CREATE POLICY "Allow authenticated users to update bar"
ON "bar"
FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

-- Allow authenticated users to delete bar records
CREATE POLICY "Allow authenticated users to delete bar"
ON "bar"
FOR DELETE
TO authenticated
USING (true);

-- For development/testing, you might want to allow anonymous access
-- Uncomment the following policies if you want to allow anonymous access

-- CREATE POLICY "Allow anonymous access to foo"
-- ON "foo"
-- FOR SELECT
-- TO anon
-- USING (true);

-- CREATE POLICY "Allow anonymous access to bar"
-- ON "bar"
-- FOR SELECT
-- TO anon
-- USING (true);

-- Set replica identity to full for both tables to receive old record data
-- This is needed to get the old record values in UPDATE and DELETE events
ALTER TABLE "foo" REPLICA IDENTITY FULL;
ALTER TABLE "bar" REPLICA IDENTITY FULL;

-- Grant necessary permissions for realtime
-- These grants allow the realtime system to access the tables
GRANT SELECT ON "foo" TO authenticated;
GRANT SELECT ON "bar" TO authenticated;

-- If you want to allow service_role access (for testing)
GRANT ALL ON "foo" TO service_role;
GRANT ALL ON "bar" TO service_role;

-- Additional grants for any custom roles you might have
-- GRANT SELECT ON "foo" TO your_custom_role;
-- GRANT SELECT ON "bar" TO your_custom_role;

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at timestamps
CREATE TRIGGER update_foo_updated_at
    BEFORE UPDATE ON "foo"
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bar_updated_at
    BEFORE UPDATE ON "bar"
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create a publication for realtime (if using self-hosted Supabase)
-- This is needed for the realtime server to know which tables to replicate
DROP PUBLICATION IF EXISTS supabase_realtime;
CREATE PUBLICATION supabase_realtime FOR ALL TABLES;

-- Alternative: Create publication for specific tables only
-- DROP PUBLICATION IF EXISTS supabase_realtime;
-- CREATE PUBLICATION supabase_realtime FOR TABLE "foo", "bar";

-- Verify the setup
SELECT 
    schemaname,
    tablename,
    rowsecurity,
    hasrls
FROM pg_tables 
WHERE tablename IN ('foo', 'bar');

-- Check replica identity
SELECT 
    schemaname,
    tablename,
    relreplident
FROM pg_tables t
JOIN pg_class c ON c.relname = t.tablename
WHERE tablename IN ('foo', 'bar');

-- Check publications
SELECT 
    pubname,
    schemaname,
    tablename
FROM pg_publication_tables
WHERE pubname = 'supabase_realtime'
AND tablename IN ('foo', 'bar');

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Realtime setup completed successfully for foo and bar tables!';
    RAISE NOTICE 'Tables now have:';
    RAISE NOTICE '- Row Level Security enabled';
    RAISE NOTICE '- Appropriate access policies';
    RAISE NOTICE '- Replica identity set to FULL';
    RAISE NOTICE '- Publication configured for realtime';
    RAISE NOTICE '- Updated timestamp triggers';
END $$; 
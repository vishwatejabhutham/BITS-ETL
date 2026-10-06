-- ====================================================================
-- Supabase Table Schema: customer_churn
-- Execute this script in Supabase SQL Editor to create/reset the table.
-- ====================================================================

-- 1. Drop existing table if column definitions were incomplete or modified
DROP TABLE IF EXISTS public.customer_churn CASCADE;

-- 2. Create target table with all 26 standardized columns
CREATE TABLE public.customer_churn (
    customer_id TEXT PRIMARY KEY,
    gender TEXT,
    senior_citizen BOOLEAN,
    partner TEXT,
    dependents TEXT,
    tenure INTEGER,
    phone_service TEXT,
    multiple_lines TEXT,
    internet_service TEXT,
    online_security TEXT,
    online_backup TEXT,
    device_protection TEXT,
    tech_support TEXT,
    streaming_tv TEXT,
    streaming_movies TEXT,
    contract TEXT,
    paperless_billing TEXT,
    payment_method TEXT,
    monthly_charges NUMERIC(10, 2),
    total_charges NUMERIC(10, 2),
    churn BOOLEAN,
    churn_numeric INTEGER,
    tenure_group TEXT,
    estimated_clv NUMERIC(10, 2),
    churn_risk_score NUMERIC(3, 2),
    processed_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Performance & Analytical Indexes
CREATE INDEX IF NOT EXISTS idx_customer_churn_status ON public.customer_churn (churn);
CREATE INDEX IF NOT EXISTS idx_customer_churn_contract ON public.customer_churn (contract);
CREATE INDEX IF NOT EXISTS idx_customer_churn_tenure_group ON public.customer_churn (tenure_group);
CREATE INDEX IF NOT EXISTS idx_customer_churn_risk ON public.customer_churn (churn_risk_score DESC);

-- 4. Row Level Security (RLS) & Access Policies
ALTER TABLE public.customer_churn ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow read access to all users" ON public.customer_churn
    FOR SELECT USING (true);

CREATE POLICY "Allow service role full access" ON public.customer_churn
    FOR ALL USING (true);

-- 5. Force Supabase PostgREST API to refresh schema cache immediately
NOTIFY pgrst, 'reload schema';

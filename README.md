# Kaggle to Supabase ETL Pipeline

A modular, production-ready **Extract, Transform, Load (ETL)** pipeline built in Python to extract datasets from **Kaggle**, perform standard data cleaning, type casting, schema validation, and feature enrichment, and load the processed data into **Supabase** via the official `supabase-py` SDK.

---

## 📁 Modular Project Structure

```
BITS-ETL/
├── extract.py          # [Extract] Downloads Kaggle dataset via API (with synthetic mock fallback)
├── transform.py        # [Transform] Standardizes column names, imputes missing values, enriches features
├── load.py             # [Load] Connects to Supabase & loads data in sanitized JSON batches
├── main.py             # [Orchestration] Main entrypoint running end-to-end ETL workflow
├── config.py           # [Config] Centralized environment variable & file path configuration
├── schema.sql          # [Database] Supabase SQL DDL script for table creation & indexing
├── test_pipeline.py    # [Testing] Automated unit and integration test suite
├── requirements.txt    # [Dependencies] Python package dependencies
├── .env.example        # [Environment] Template for Kaggle & Supabase secrets
└── data/               # [Storage] Local raw and processed dataset directory
    ├── raw/
    └── processed/
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- A [Supabase](https://supabase.com/) project
- A [Kaggle](https://www.kaggle.com/) account (optional for testing; fallback synthetic data generator included)

### 2. Environment Setup

Clone/navigate to the project and initialize a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Variables Configuration

Copy `.env.example` to `.env` and fill in your Kaggle & Supabase credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key
KAGGLE_DATASET=blastchar/telco-customer-churn

SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your_supabase_anon_or_service_role_key
SUPABASE_TABLE=customer_churn
BATCH_SIZE=500
```

---

## 🗄️ Database Setup in Supabase

Before running the pipeline into Supabase, create the target database table:

1. Open your **Supabase Dashboard** -> **SQL Editor**.
2. Copy the contents of [`schema.sql`](file:///Users/bhuthamvishwateja/BITS-ETL/schema.sql) and execute the SQL query.
3. This creates the `customer_churn` table along with performance indexes on `churn`, `contract`, and `churn_risk_score`.

---

## ⚙️ Running the ETL Pipeline

### Option A: End-to-End Execution (Orchestrator)

Run the full pipeline (`Extract -> Transform -> Load`):

```bash
python main.py
```

### Option B: Dry Run Mode (Simulation)

Test the pipeline without sending HTTP requests to Supabase:

```bash
python main.py --dry-run
```

### Option C: Run Modular Components Individually

Each component is decoupled and executable standalone:

1. **Extract raw Kaggle data:**
   ```bash
   python extract.py
   ```
2. **Transform & clean raw CSV:**
   ```bash
   python transform.py
   ```
3. **Load processed data into Supabase:**
   ```bash
   python load.py
   ```

---

## 🧪 Automated Testing

Run the test suite to verify extraction, cleaning rules, feature engineering, and JSON serialization:

```bash
python test_pipeline.py
```

---

## 📊 Data Transformation Pipeline Details

| Stage | Operations Performed |
| :--- | :--- |
| **Extract** | Downloads dataset ZIP from Kaggle API, unpacks CSV files into `data/raw/`. Includes auto-mock fallback if credentials are absent. |
| **Cleaning** | Converts column headers to `snake_case`. Standardizes numeric types and imputes missing `total_charges` (`tenure * monthly_charges`). |
| **Enrichment** | Adds `churn_numeric` (0/1), `tenure_group` (0-12 Mo, 12-24 Mo, etc.), `estimated_clv`, `churn_risk_score` (0.00-1.00), and ISO `processed_at` timestamp. |
| **Load** | Sanitizes Pandas/Numpy types into JSON-native primitives (`int`, `float`, `bool`, `None` for NaN), then upserts into Supabase in configurable batch sizes (default: 500). |

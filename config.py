import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Base Paths
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Kaggle Configuration
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME", "")
KAGGLE_KEY = os.getenv("KAGGLE_KEY", "")
# Default dataset: Telco Customer Churn
KAGGLE_DATASET = os.getenv("KAGGLE_DATASET", "blastchar/telco-customer-churn")

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")  # Anon key or Service Role Key
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "customer_churn")

# ETL Pipeline Settings
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))
DEFAULT_CSV_FILENAME = "WA_Fn-UseC_-Telco-Customer-Churn.csv"


def validate_config(require_supabase: bool = True, require_kaggle: bool = False):
    """Validate required environment variables."""
    missing = []
    if require_supabase:
        if not SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not SUPABASE_KEY:
            missing.append("SUPABASE_KEY")

    if require_kaggle:
        if not KAGGLE_USERNAME:
            missing.append("KAGGLE_USERNAME")
        if not KAGGLE_KEY:
            missing.append("KAGGLE_KEY")

    if missing:
        raise ValueError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Please check your .env file or environment configuration."
        )

import os
from pathlib import Path
import pandas as pd
import numpy as np
from config import RAW_DATA_DIR, KAGGLE_DATASET, KAGGLE_USERNAME, KAGGLE_KEY


class KaggleExtractor:
    """Step 1: Extract raw data from Kaggle API (with synthetic data fallback)."""

    def __init__(self, dataset_name: str = KAGGLE_DATASET, output_dir: Path = RAW_DATA_DIR):
        self.dataset_name = dataset_name
        self.output_dir = output_dir

    def authenticate_kaggle(self) -> bool:
        """Check and set Kaggle API credentials."""
        # 1. Environment variables from .env
        username = KAGGLE_USERNAME or os.environ.get("KAGGLE_USERNAME", "")
        key = KAGGLE_KEY or os.environ.get("KAGGLE_KEY", "")

        if username and key:
            os.environ["KAGGLE_USERNAME"] = username
            os.environ["KAGGLE_KEY"] = key
            print(f"  -> Using Kaggle API credentials for user: '{username}'")
            return True

        # 2. System credentials (~/.kaggle/kaggle.json)
        kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
        if kaggle_json.exists():
            print(f"  -> Found Kaggle API key file at '{kaggle_json}'")
            return True

        print("  -> Notice: Kaggle credentials not found. Will generate synthetic demo dataset.")
        return False

    def extract_from_kaggle(self) -> pd.DataFrame:
        """Download dataset from Kaggle and load into Pandas DataFrame."""
        print(f"  -> Downloading dataset '{self.dataset_name}' from Kaggle...")
        self.authenticate_kaggle()

        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
            api = KaggleApi()
            api.authenticate()

            api.dataset_download_files(self.dataset_name, path=str(self.output_dir), unzip=True)

            # Find extracted CSV file (ignore temporary mock files)
            csv_files = [f for f in Path(self.output_dir).glob("*.csv") if not f.name.startswith("mock_")]
            if not csv_files:
                csv_files = list(Path(self.output_dir).glob("*.csv"))
            if not csv_files:
                raise FileNotFoundError(f"No CSV file found in '{self.dataset_name}' after unzipping.")

            selected_csv = csv_files[0]
            print(f"  -> Successfully downloaded: {selected_csv.name}")
            df = pd.read_csv(selected_csv)
            print(f"  -> Extracted {len(df):,} rows and {len(df.columns)} columns.")
            return df

        except Exception as e:
            print(f"  -> Kaggle download failed ({e}). Generating synthetic demo dataset instead.")
            return self.generate_mock_data()

    def generate_mock_data(self, num_records: int = 1500) -> pd.DataFrame:
        """Generate realistic sample dataset matching Kaggle schema."""
        print(f"  -> Generating {num_records:,} sample customer records...")
        np.random.seed(42)

        customer_ids = [f"{np.random.randint(1000, 9999)}-{chr(65+i%26)}{chr(65+(i*3)%26)}{chr(65+(i*7)%26)}" for i in range(num_records)]
        df = pd.DataFrame({
            "customerID": customer_ids,
            "gender": np.random.choice(["Male", "Female"], size=num_records),
            "SeniorCitizen": np.random.choice([0, 1], size=num_records, p=[0.84, 0.16]),
            "Partner": np.random.choice(["Yes", "No"], size=num_records),
            "Dependents": np.random.choice(["Yes", "No"], size=num_records),
            "tenure": np.random.randint(0, 73, size=num_records),
            "PhoneService": np.random.choice(["Yes", "No"], size=num_records, p=[0.90, 0.10]),
            "MultipleLines": np.random.choice(["Yes", "No", "No phone service"], size=num_records),
            "InternetService": np.random.choice(["DSL", "Fiber optic", "No"], size=num_records),
            "OnlineSecurity": np.random.choice(["Yes", "No", "No internet service"], size=num_records),
            "OnlineBackup": np.random.choice(["Yes", "No", "No internet service"], size=num_records),
            "DeviceProtection": np.random.choice(["Yes", "No", "No internet service"], size=num_records),
            "TechSupport": np.random.choice(["Yes", "No", "No internet service"], size=num_records),
            "StreamingTV": np.random.choice(["Yes", "No", "No internet service"], size=num_records),
            "StreamingMovies": np.random.choice(["Yes", "No", "No internet service"], size=num_records),
            "Contract": np.random.choice(["Month-to-month", "One year", "Two year"], size=num_records),
            "PaperlessBilling": np.random.choice(["Yes", "No"], size=num_records),
            "PaymentMethod": np.random.choice(["Electronic check", "Mailed check", "Bank transfer", "Credit card"], size=num_records),
            "MonthlyCharges": np.round(np.random.uniform(18.25, 118.75, size=num_records), 2),
            "TotalCharges": [str(round(t * m, 2)) if t > 0 else " " for t, m in zip(np.random.randint(0, 73, size=num_records), np.random.uniform(18.25, 118.75, size=num_records))],
            "Churn": np.random.choice(["Yes", "No"], size=num_records, p=[0.27, 0.73])
        })

        mock_file = self.output_dir / "mock_customer_churn.csv"
        df.to_csv(mock_file, index=False)
        print(f"  -> Saved mock data to {mock_file}")
        return df

    def extract(self, use_mock_if_missing: bool = True) -> pd.DataFrame:
        """Main Extraction step."""
        print("\n==========================================")
        print("  STEP 1: EXTRACTING DATA FROM KAGGLE    ")
        print("==========================================")
        if self.authenticate_kaggle():
            return self.extract_from_kaggle()
        else:
            if use_mock_if_missing:
                return self.generate_mock_data()
            else:
                raise ValueError("Kaggle credentials not found.")


if __name__ == "__main__":
    extractor = KaggleExtractor()
    data = extractor.extract()
    print("\nPreview of extracted data:")
    print(data.head(3))

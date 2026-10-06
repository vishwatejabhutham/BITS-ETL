import re
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import numpy as np
from config import PROCESSED_DATA_DIR


class CustomerChurnTransformer:
    """Step 2: Transform, clean, and enrich raw dataset."""

    def __init__(self, output_dir: Path = PROCESSED_DATA_DIR):
        self.output_dir = output_dir

    @staticmethod
    def _camel_to_snake(name: str) -> str:
        """Convert CamelCase column name to snake_case."""
        name = name.replace("ID", "_id")
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        snake = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        return re.sub('_+', '_', snake).strip('_')

    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert all column headers to snake_case."""
        df = df.copy()
        rename_map = {col: self._camel_to_snake(col) for col in df.columns}
        df.rename(columns=rename_map, inplace=True)
        print("  -> Standardized column headers to lowercase snake_case.")
        return df

    def clean_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean blank spaces and missing numbers."""
        df = df.copy()
        if "total_charges" in df.columns:
            # Convert blank space strings to NaN and parse as numbers
            df["total_charges"] = pd.to_numeric(
                df["total_charges"].astype(str).str.strip().replace("", np.nan),
                errors="coerce"
            )
            # Impute missing values (tenure * monthly_charges)
            missing_count = df["total_charges"].isna().sum()
            if missing_count > 0:
                df.loc[df["total_charges"].isna(), "total_charges"] = (
                    df["tenure"] * df["monthly_charges"]
                ).round(2)
                print(f"  -> Fixed {missing_count} missing values in 'total_charges'.")
        return df

    def convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enforce standard data types for SQL/JSON compatibility."""
        df = df.copy()
        df["tenure"] = df["tenure"].astype(int)
        df["monthly_charges"] = df["monthly_charges"].astype(float).round(2)
        df["total_charges"] = df["total_charges"].astype(float).round(2)

        if "senior_citizen" in df.columns:
            df["senior_citizen"] = df["senior_citizen"].astype(int) == 1

        if "churn" in df.columns:
            df["churn"] = df["churn"].astype(str).str.strip().str.capitalize() == "Yes"

        print("  -> Converted data types (booleans, integers, rounded floats).")
        return df

    def add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate custom metrics and feature enrichment."""
        df = df.copy()

        # 1. Churn flag as 0 or 1 integer
        df["churn_numeric"] = df["churn"].astype(int)

        # 2. Tenure category groups
        bins = [-1, 12, 24, 48, 72, np.inf]
        labels = ["0-12 Mo", "12-24 Mo", "24-48 Mo", "48-72 Mo", "72+ Mo"]
        df["tenure_group"] = pd.cut(df["tenure"], bins=bins, labels=labels).astype(str)

        # 3. Estimated Customer Lifetime Value (CLV)
        df["estimated_clv"] = (df["monthly_charges"] * df["tenure"]).round(2)

        # 4. Churn Risk Score (0.0 to 1.0)
        risk = np.zeros(len(df))
        risk += np.where(df.get("contract", "") == "Month-to-month", 0.40, 0.05)
        risk += np.where(df.get("internet_service", "") == "Fiber optic", 0.20, 0.05)
        risk += np.where(df["tenure"] <= 12, 0.25, 0.05)
        risk += np.where(df["monthly_charges"] > 70.0, 0.15, 0.05)
        df["churn_risk_score"] = np.clip(np.round(risk, 2), 0.0, 1.0)

        # 5. Timestamp
        df["processed_at"] = datetime.now(timezone.utc).isoformat()

        print("  -> Added 5 new calculated fields: churn_numeric, tenure_group, estimated_clv, churn_risk_score, processed_at.")
        return df

    def transform(self, df_raw: pd.DataFrame, save_processed: bool = True) -> pd.DataFrame:
        """Main Transformation step."""
        print("\n==========================================")
        print("  STEP 2: TRANSFORMING & CLEANING DATA   ")
        print("==========================================")
        print(f"  -> Input data shape: {df_raw.shape[0]:,} rows, {df_raw.shape[1]} columns")

        df = self.clean_column_names(df_raw)
        df = self.clean_missing_values(df)
        df = self.convert_data_types(df)
        df = self.add_derived_features(df)

        if save_processed:
            output_filepath = self.output_dir / "transformed_customer_churn.csv"
            df.to_csv(output_filepath, index=False)
            print(f"  -> Saved clean dataset to '{output_filepath}'")

        print(f"  -> Transformation complete! Final shape: {df.shape[0]:,} rows, {df.shape[1]} columns.")
        return df


if __name__ == "__main__":
    from extract import KaggleExtractor
    raw_data = KaggleExtractor().extract()
    transformer = CustomerChurnTransformer()
    clean_data = transformer.transform(raw_data)
    print("\nPreview of clean data:")
    print(clean_data[["customer_id", "tenure", "monthly_charges", "total_charges", "churn", "churn_risk_score"]].head(3))

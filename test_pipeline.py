import unittest
import pandas as pd
import numpy as np
from extract import KaggleExtractor
from transform import CustomerChurnTransformer
from load import SupabaseLoader


class TestETLPipeline(unittest.TestCase):
    """Unit and Integration Tests for ETL Pipeline components."""

    def setUp(self):
        self.extractor = KaggleExtractor()
        self.transformer = CustomerChurnTransformer()
        self.loader = SupabaseLoader()

    def test_01_extraction_mock_data(self):
        """Test mock data generation in extract.py."""
        df_raw = self.extractor.generate_mock_data(num_records=100)
        self.assertEqual(len(df_raw), 100)
        self.assertIn("customerID", df_raw.columns)
        self.assertIn("TotalCharges", df_raw.columns)
        self.assertIn("Churn", df_raw.columns)

    def test_02_transformation_cleaning(self):
        """Test column renaming, missing value imputation, and derived features in transform.py."""
        raw_df = pd.DataFrame({
            "customerID": ["0001-ABC", "0002-DEF"],
            "gender": ["Male", "Female"],
            "SeniorCitizen": [0, 1],
            "tenure": [12, 0],
            "MonthlyCharges": [50.0, 75.0],
            "TotalCharges": ["600.0", " "],  # Blank total_charges string
            "Churn": ["Yes", "No"],
            "Contract": ["Month-to-month", "Two year"],
            "InternetService": ["Fiber optic", "DSL"]
        })

        df_trans = self.transformer.transform(raw_df, save_processed=False)
        
        # Verify snake_case renaming
        self.assertIn("customer_id", df_trans.columns)
        self.assertIn("monthly_charges", df_trans.columns)
        self.assertIn("total_charges", df_trans.columns)

        # Verify imputation of missing TotalCharges for tenure=0 -> 0.0
        self.assertEqual(df_trans.loc[df_trans["customer_id"] == "0002-DEF", "total_charges"].values[0], 0.0)

        # Verify derived features
        self.assertIn("churn_risk_score", df_trans.columns)
        self.assertIn("tenure_group", df_trans.columns)
        self.assertIn("estimated_clv", df_trans.columns)
        self.assertTrue(df_trans.loc[df_trans["customer_id"] == "0001-ABC", "churn"].values[0])

    def test_03_load_record_sanitization(self):
        """Test record JSON sanitization in load.py."""
        df = pd.DataFrame({
            "customer_id": ["TEST-1"],
            "monthly_charges": [55.5],
            "nan_col": [np.nan],
            "int_col": [np.int64(42)],
            "bool_col": [np.bool_(True)]
        })

        records = self.loader.prepare_records(df)
        self.assertEqual(len(records), 1)
        record = records[0]

        # Verify numpy types converted to JSON primitives and NaN converted to None
        self.assertIsNone(record["nan_col"])
        self.assertIsInstance(record["int_col"], int)
        self.assertIsInstance(record["bool_col"], bool)


if __name__ == "__main__":
    unittest.main()

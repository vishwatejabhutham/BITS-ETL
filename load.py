import math
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE, BATCH_SIZE


class SupabaseLoader:
    """Step 3: Load cleaned data into Supabase database."""

    def __init__(
        self,
        supabase_url: str = SUPABASE_URL,
        supabase_key: str = SUPABASE_KEY,
        table_name: str = SUPABASE_TABLE,
        batch_size: int = BATCH_SIZE
    ):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.table_name = table_name
        self.batch_size = batch_size
        self.client: Optional[Client] = None

    def connect(self) -> bool:
        """Connect to Supabase client."""
        if not self.supabase_url or not self.supabase_key:
            print("  -> Warning: SUPABASE_URL or SUPABASE_KEY is not configured in .env file.")
            return False

        try:
            # Normalize URL format to avoid /rest/v1 duplications
            url = self.supabase_url.rstrip("/")
            if url.endswith("/rest/v1"):
                url = url[:-len("/rest/v1")]

            self.client = create_client(url, self.supabase_key)
            print(f"  -> Connected to Supabase project: {url}")
            return True
        except Exception as e:
            print(f"  -> Connection error: {e}")
            return False

    @staticmethod
    def _clean_value_for_json(val: Any) -> Any:
        """Sanitize values for JSON serialization (convert NaN to None, numpy types to Python primitives)."""
        if pd.isna(val) or val is None:
            return None
        if isinstance(val, (np.bool_, bool)):
            return bool(val)
        if isinstance(val, (np.integer, int)) and not isinstance(val, (np.bool_, bool)):
            return int(val)
        if isinstance(val, (np.floating, float)):
            if math.isnan(val) or math.isinf(val):
                return None
            return float(val)
        return str(val)

    def prepare_records(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert DataFrame rows into JSON records."""
        records = []
        for row in df.to_dict(orient="records"):
            clean_row = {col: self._clean_value_for_json(val) for col, val in row.items()}
            records.append(clean_row)
        print(f"  -> Prepared {len(records):,} records for database load.")
        return records

    def load_batch(self, records: List[Dict[str, Any]], upsert: bool = True) -> Dict[str, Any]:
        """Upload records in batch chunks."""
        if not self.client:
            raise RuntimeError("Supabase client is not connected.")

        total_records = len(records)
        total_batches = math.ceil(total_records / self.batch_size)
        inserted_count = 0
        error_count = 0

        print(f"  -> Uploading {total_records:,} records to table '{self.table_name}' in {total_batches} batches...")

        for i in range(0, total_records, self.batch_size):
            batch = records[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1

            try:
                if upsert:
                    self.client.table(self.table_name).upsert(batch, on_conflict="customer_id").execute()
                else:
                    self.client.table(self.table_name).insert(batch).execute()

                inserted_count += len(batch)
                print(f"     ✅ Batch {batch_num}/{total_batches}: Successfully uploaded {len(batch)} records.")

            except Exception as e:
                error_count += len(batch)
                err_msg = str(e)
                print(f"     ❌ Batch {batch_num}/{total_batches} failed!")

                if "PGRST205" in err_msg or "Could not find the table" in err_msg:
                    print(f"\n     ⚠️ TABLE MISSING ERROR: Table '{self.table_name}' does not exist in Supabase yet.")
                    print(f"     👉 Please open Supabase SQL Editor and run schema.sql to create the table.")
                    break
                elif "PGRST204" in err_msg or "schema cache" in err_msg:
                    print(f"\n     ⚠️ SCHEMA MISMATCH ERROR: Table '{self.table_name}' is missing some columns in Supabase.")
                    print(f"     👉 Please open Supabase SQL Editor and run schema.sql to reset table columns.")
                    break
                else:
                    print(f"     Error detail: {err_msg}")

        summary = {
            "total": total_records,
            "inserted": inserted_count,
            "failed": error_count,
            "table": self.table_name
        }
        return summary

    def load(self, df: pd.DataFrame, dry_run: bool = False, upsert: bool = True) -> Dict[str, Any]:
        """Main Load step."""
        print("\n==========================================")
        print("  STEP 3: LOADING DATA INTO SUPABASE     ")
        print("==========================================")
        records = self.prepare_records(df)

        if dry_run:
            print("  -> [DRY-RUN MODE] Simulation mode enabled. Skipping actual database write.")
            print("  -> Preview of 1st record payload:")
            if records:
                print("     ", records[0])
            return {"total": len(records), "inserted": len(records), "failed": 0, "table": self.table_name, "mode": "dry_run"}

        connected = self.connect()
        if not connected:
            print("  -> Could not connect to Supabase. Switching to dry-run verification mode.")
            return self.load(df, dry_run=True, upsert=upsert)

        return self.load_batch(records, upsert=upsert)


if __name__ == "__main__":
    from extract import KaggleExtractor
    from transform import CustomerChurnTransformer

    raw_data = KaggleExtractor().extract()
    clean_data = CustomerChurnTransformer().transform(raw_data)
    loader = SupabaseLoader()
    stats = loader.load(clean_data, dry_run=True)
    print("\nLoad Summary Stats:")
    print(stats)

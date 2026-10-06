import sys
import time
import argparse
from typing import Dict, Any

from config import KAGGLE_DATASET, SUPABASE_TABLE, BATCH_SIZE
from extract import KaggleExtractor
from transform import CustomerChurnTransformer
from load import SupabaseLoader


def ask_user_to_proceed(step_name: str, auto_yes: bool = False) -> bool:
    """Prompt the user with a simple yes/no question to proceed to the next step."""
    if auto_yes:
        print(f"\n[AUTO] Auto-confirming next step: '{step_name}'")
        return True

    print("\n--------------------------------------------------")
    while True:
        try:
            response = input(f"❓ Do you want to proceed to {step_name}? (yes/no) [yes]: ").strip().lower()
            if response in ["y", "yes", ""]:
                return True
            elif response in ["n", "no"]:
                print(f"🛑 Pipeline stopped by user before '{step_name}'.")
                return False
            else:
                print("   Please type 'yes' or 'no'.")
        except (EOFError, KeyboardInterrupt):
            print("\n🛑 Pipeline interrupted.")
            return False


def run_pipeline(
    dataset_name: str = KAGGLE_DATASET,
    dry_run: bool = False,
    use_mock: bool = False,
    batch_size: int = BATCH_SIZE,
    table_name: str = SUPABASE_TABLE,
    interactive: bool = True
) -> Dict[str, Any]:
    """Execute the interactive 3-step Kaggle to Supabase ETL pipeline."""
    start_time = time.time()

    print("\n" + "=" * 55)
    print("      🚀 KAGGLE TO SUPABASE ETL PIPELINE           ")
    print("=" * 55)
    print(f"  Target Dataset : {dataset_name}")
    print(f"  Target Table   : {table_name}")
    print(f"  Execution Mode : {'DRY RUN (Simulation)' if dry_run else 'PRODUCTION LOAD (Live Database)'}")
    print("=" * 55)

    # ----------------------------------------------------
    # STEP 1: EXTRACT FROM KAGGLE
    # ----------------------------------------------------
    extractor = KaggleExtractor(dataset_name=dataset_name)
    df_raw = extractor.extract(use_mock_if_missing=(use_mock or dry_run or True))

    print(f"\n  ✅ STEP 1 COMPLETED: Extracted {len(df_raw):,} records from Kaggle.")
    print("  Preview of raw data:")
    print(df_raw.iloc[:2, :5].to_string(index=False))

    # Ask user before proceeding to Step 2
    if interactive and not ask_user_to_proceed("STEP 2: Transform & Clean Data"):
        return {"status": "STOPPED_AFTER_EXTRACT", "extracted_rows": len(df_raw)}

    # ----------------------------------------------------
    # STEP 2: TRANSFORM DATA
    # ----------------------------------------------------
    transformer = CustomerChurnTransformer()
    df_clean = transformer.transform(df_raw)

    print(f"\n  ✅ STEP 2 COMPLETED: Transformed {len(df_clean):,} records.")
    print("  Preview of clean data:")
    print(df_clean[["customer_id", "tenure", "monthly_charges", "total_charges", "churn", "churn_risk_score"]].head(2).to_string(index=False))

    # Ask user before proceeding to Step 3
    if interactive and not ask_user_to_proceed("STEP 3: Load Data into Supabase"):
        return {"status": "STOPPED_AFTER_TRANSFORM", "transformed_rows": len(df_clean)}

    # ----------------------------------------------------
    # STEP 3: LOAD INTO SUPABASE
    # ----------------------------------------------------
    loader = SupabaseLoader(table_name=table_name, batch_size=batch_size)
    load_stats = loader.load(df_clean, dry_run=dry_run)

    total_time = time.time() - start_time

    # ----------------------------------------------------
    # FINAL SUMMARY REPORT
    # ----------------------------------------------------
    print("\n" + "=" * 55)
    print("             🎉 PIPELINE SUMMARY REPORT           ")
    print("=" * 55)
    print(f"  Status            : {'SUCCESS' if load_stats.get('inserted', 0) > 0 or dry_run else 'FAILED / INCOMPLETE'}")
    print(f"  Total Time        : {total_time:.2f} seconds")
    print(f"  Extracted Rows    : {len(df_raw):,} rows (from Kaggle)")
    print(f"  Transformed Rows  : {len(df_clean):,} rows (cleaned & enriched)")
    print(f"  Loaded Rows       : {load_stats.get('inserted', 0):,} rows (in Supabase table '{table_name}')")
    print(f"  Failed Rows       : {load_stats.get('failed', 0):,} rows")
    print("=" * 55 + "\n")

    return {
        "status": "SUCCESS",
        "extracted": len(df_raw),
        "transformed": len(df_clean),
        "loaded": load_stats.get("inserted", 0),
        "total_time_seconds": round(total_time, 2)
    }


def main():
    parser = argparse.ArgumentParser(description="Simple Interactive Kaggle to Supabase ETL Pipeline")
    parser.add_argument("--auto", "-y", action="store_true", help="Run automatically without interactive yes/no prompts")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without writing to Supabase")
    parser.add_argument("--use-mock", action="store_true", help="Force synthetic demo dataset generation")
    parser.add_argument("--dataset", type=str, default=KAGGLE_DATASET, help="Kaggle dataset ID (e.g. blastchar/telco-customer-churn)")
    parser.add_argument("--table", type=str, default=SUPABASE_TABLE, help="Target Supabase table name")

    args = parser.parse_args()

    run_pipeline(
        dataset_name=args.dataset,
        dry_run=args.dry_run,
        use_mock=args.use_mock,
        table_name=args.table,
        interactive=not args.auto
    )


if __name__ == "__main__":
    main()

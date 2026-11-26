
import subprocess
import sys
import time

from pathlib import Path


# ============================================================
# PROJECT PROOF | MASTER EXECUTION PIPELINE
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PYTHON = sys.executable


# ============================================================
# PIPELINE CONFIGURATION
# ============================================================

PIPELINE_STEPS = [

    {
        "name": "Generate Financial Data",
        "command": [
            "src/ingestion/generate_financial_data.py"
        ]
    },

    {
        "name": "Inspect Dataset Quality",
        "command": [
            "src/validation/inspect_generated_data.py"
        ]
    },

    {
        "name": "Reconcile Supplier Invoices",
        "command": [
            "src/reconciliation/reconcile_invoices.py"
        ]
    },

    {
        "name": "Evaluate Invoice Reconciliation",
        "command": [
            "src/validation/evaluate_invoice_reconciliation.py"
        ]
    },

    {
        "name": "Reconcile Supplier Payments",
        "command": [
            "src/reconciliation/reconcile_payments.py"
        ]
    },

    {
        "name": "Evaluate Payment Reconciliation",
        "command": [
            "src/validation/evaluate_payment_reconciliation.py"
        ]
    },

    {
        "name": "Detect High-Value Orders",
        "command": [
            "src/detection/detect_high_value_orders.py"
        ]
    },

    {
        "name": "Evaluate High-Value Detection",
        "command": [
            "src/validation/evaluate_high_value_orders.py"
        ]
    },

    {
        "name": "Detect Unusual Orders",
        "command": [
            "src/detection/detect_unusual_orders.py"
        ]
    },

    {
        "name": "Evaluate Unusual Order Detection",
        "command": [
            "src/validation/evaluate_unusual_orders.py"
        ]
    },

    {
        "name": "Build Investigation Cases",
        "command": [
            "src/investigation/build_investigation_cases.py"
        ]
    },

    {
        "name": "Prioritise Investigations",
        "command": [
            "src/investigation/prioritise_investigations.py"
        ]
    },

    {
        "name": "Generate Management Report",
        "command": [
            "src/reporting/generate_investigation_report.py"
        ]
    },

    {
        "name": "Generate Individual Case Summaries",
        "command": [
            "src/reporting/generate_case_summaries.py"
        ]
    },

    {
        "name": "Validate Investigation Outputs",
        "command": [
            "src/validation/validate_investigation_outputs.py"
        ]
    },

    {
        "name": "Export Investigation Workbook",
        "command": [
            "src/reporting/export_investigation_reports.py"
        ]
    },

    {
        "name": "Load Investigation Database",
        "command": [
            "src/database/load_investigation_database.py"
        ]
    },

    {
        "name": "Verify Investigation Database",
        "command": [
            "src/database/verify_investigation_database.py"
        ]
    },

    {
        "name": "Generate SQL Investigation Analytics",
        "command": [
            "src/database/generate_sql_analytics.py"
        ]
    },

    {
        "name": "Run Automated Tests",
        "command": [
            "-m",
            "pytest",
            "tests",
            "-v"
        ]
    }

]


# ============================================================
# EXECUTE PIPELINE STEP
# ============================================================

def execute_step(step_number, total_steps, step):

    name = step["name"]

    command = [
        PYTHON,
        *step["command"]
    ]

    print("\n" + "=" * 75)
    print(
        f"STEP {step_number}/{total_steps}: {name.upper()}"
    )
    print("=" * 75)

    start_time = time.perf_counter()

    subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=True
    )

    duration = time.perf_counter() - start_time

    print("\n" + "-" * 75)
    print(f"COMPLETED: {name}")
    print(f"Execution Time: {duration:.2f} seconds")
    print("-" * 75)

    return duration


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    total_steps = len(PIPELINE_STEPS)

    successful_steps = 0
    total_duration = 0

    print("=" * 75)
    print("PROJECT PROOF | COMPLETE EXECUTION PIPELINE")
    print("=" * 75)

    print(f"Total Pipeline Steps: {total_steps}")
    print(f"Python Executable: {PYTHON}")

    pipeline_start = time.perf_counter()

    try:

        for step_number, step in enumerate(
            PIPELINE_STEPS,
            start=1
        ):

            duration = execute_step(
                step_number,
                total_steps,
                step
            )

            successful_steps += 1
            total_duration += duration

    except subprocess.CalledProcessError as error:

        print("\n" + "=" * 75)
        print("PIPELINE EXECUTION FAILED")
        print("=" * 75)

        print(f"Failed Command: {error.cmd}")
        print(f"Exit Code: {error.returncode}")

        print(
            f"Successful Steps: "
            f"{successful_steps}/{total_steps}"
        )

        sys.exit(error.returncode)

    pipeline_duration = (
        time.perf_counter() - pipeline_start
    )

    print("\n" + "=" * 75)
    print("PROJECT PROOF | PIPELINE EXECUTION SUMMARY")
    print("=" * 75)

    print(f"Total Steps: {total_steps}")
    print(f"Successful Steps: {successful_steps}")
    print(f"Failed Steps: {total_steps - successful_steps}")

    print(
        f"Total Step Execution Time: "
        f"{total_duration:.2f} seconds"
    )

    print(
        f"Total Pipeline Runtime: "
        f"{pipeline_duration:.2f} seconds"
    )

    print("\nPROJECT PROOF PIPELINE: SUCCESSFUL")

    print("=" * 75)


if __name__ == "__main__":
    main()

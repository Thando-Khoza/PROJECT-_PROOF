
from pathlib import Path
import sqlite3


# ============================================================
# PROJECT PROOF | DATABASE INTEGRITY CHECKER
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_FILE = (
    PROJECT_ROOT / "database" / "project_proof.db"
)

EXPECTED_RECORD_COUNTS = {
    "purchase_orders": 100,
    "supplier_invoices": 115,
    "payment_records": 105,
    "investigation_cases": 60,
    "investigation_evidence": 70,
    "investigation_priority_queue": 60,
    "validation_results": 10,
}

EXPECTED_VIEWS = [
    "high_risk_investigations",
    "investigation_evidence_summary",
]

EXPECTED_INDEXES = [
    "idx_cases_case_id",
    "idx_cases_risk_level",
    "idx_evidence_case_id",
    "idx_priority_case_id",
    "idx_orders_po_number",
    "idx_invoices_invoice_number",
    "idx_payments_invoice_number",
]


# ============================================================
# CHECK TRACKING
# ============================================================

results = []


def record_check(check_name, passed, details):
    """Record the result of an individual database check."""

    results.append({
        "check": check_name,
        "passed": passed,
        "details": details
    })

    status = "PASS" if passed else "FAIL"

    print(
        f"{status}: {check_name} | {details}"
    )


# ============================================================
# DATABASE CONNECTION
# ============================================================

def connect_to_database():
    """Connect to the existing SQLite database."""

    if not DATABASE_FILE.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_FILE}"
        )

    return sqlite3.connect(DATABASE_FILE)


# ============================================================
# DATABASE INTEGRITY
# ============================================================

def check_database_integrity(connection):
    """Run SQLite's built-in integrity check."""

    result = connection.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

    passed = result.lower() == "ok"

    record_check(
        "DATABASE INTEGRITY",
        passed,
        result
    )


# ============================================================
# TABLE VALIDATION
# ============================================================

def check_table_counts(connection):
    """Verify that all expected tables have correct record counts."""

    existing_tables = {
        row[0]
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()
    }

    for table_name, expected_count in EXPECTED_RECORD_COUNTS.items():

        if table_name not in existing_tables:
            record_check(
                f"TABLE: {table_name}",
                False,
                "Table does not exist"
            )
            continue

        actual_count = connection.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()[0]

        passed = actual_count == expected_count

        record_check(
            f"TABLE: {table_name}",
            passed,
            f"Expected {expected_count}, found {actual_count}"
        )


# ============================================================
# PRIMARY KEY VALIDATION
# ============================================================

def check_duplicate_case_ids(connection):
    """Check that investigation case IDs are unique."""

    duplicate_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT case_id
            FROM investigation_cases
            GROUP BY case_id
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    record_check(
        "UNIQUE INVESTIGATION CASE IDS",
        duplicate_count == 0,
        f"Duplicate case IDs: {duplicate_count}"
    )


# ============================================================
# EVIDENCE RELATIONSHIP VALIDATION
# ============================================================

def check_evidence_relationships(connection):
    """Check that every evidence record references an existing case."""

    orphan_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM investigation_evidence AS evidence
        LEFT JOIN investigation_cases AS cases
            ON evidence.case_id = cases.case_id
        WHERE cases.case_id IS NULL
        """
    ).fetchone()[0]

    record_check(
        "EVIDENCE CASE RELATIONSHIPS",
        orphan_count == 0,
        f"Evidence records without a matching case: {orphan_count}"
    )


# ============================================================
# PRIORITY QUEUE VALIDATION
# ============================================================

def check_priority_relationships(connection):
    """Check that priority queue records reference valid cases."""

    orphan_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM investigation_priority_queue AS priority
        LEFT JOIN investigation_cases AS cases
            ON priority.case_id = cases.case_id
        WHERE cases.case_id IS NULL
        """
    ).fetchone()[0]

    record_check(
        "PRIORITY QUEUE CASE RELATIONSHIPS",
        orphan_count == 0,
        f"Priority records without a matching case: {orphan_count}"
    )


# ============================================================
# RISK SCORE VALIDATION
# ============================================================

def check_risk_scores(connection):
    """Verify that all investigation risk scores are between 0 and 100."""

    invalid_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM investigation_cases
        WHERE risk_score IS NULL
           OR risk_score < 0
           OR risk_score > 100
        """
    ).fetchone()[0]

    record_check(
        "RISK SCORE VALIDATION",
        invalid_count == 0,
        f"Invalid risk scores: {invalid_count}"
    )


# ============================================================
# VIEW VALIDATION
# ============================================================

def check_database_views(connection):
    """Verify that expected SQL views exist and can be queried."""

    existing_views = {
        row[0]
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'view'
            """
        ).fetchall()
    }

    for view_name in EXPECTED_VIEWS:

        if view_name not in existing_views:
            record_check(
                f"SQL VIEW: {view_name}",
                False,
                "View does not exist"
            )
            continue

        try:
            connection.execute(
                f'SELECT * FROM "{view_name}" LIMIT 1'
            ).fetchall()

            record_check(
                f"SQL VIEW: {view_name}",
                True,
                "View exists and query executed"
            )

        except sqlite3.DatabaseError as error:
            record_check(
                f"SQL VIEW: {view_name}",
                False,
                str(error)
            )


# ============================================================
# INDEX VALIDATION
# ============================================================

def check_database_indexes(connection):
    """Verify that expected database indexes exist."""

    existing_indexes = {
        row[0]
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'index'
            """
        ).fetchall()
    }

    for index_name in EXPECTED_INDEXES:

        passed = index_name in existing_indexes

        record_check(
            f"SQL INDEX: {index_name}",
            passed,
            "Index exists" if passed else "Index missing"
        )


# ============================================================
# IMPORT HISTORY VALIDATION
# ============================================================

def check_import_history(connection):
    """Verify that all seven source tables have import history."""

    history_exists = connection.execute(
        """
        SELECT COUNT(*)
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'database_import_history'
        """
    ).fetchone()[0]

    if not history_exists:
        record_check(
            "DATABASE IMPORT HISTORY",
            False,
            "Import history table does not exist"
        )
        return

    imported_tables = connection.execute(
        """
        SELECT COUNT(DISTINCT source_table)
        FROM database_import_history
        """
    ).fetchone()[0]

    passed = imported_tables == len(EXPECTED_RECORD_COUNTS)

    record_check(
        "DATABASE IMPORT HISTORY",
        passed,
        f"Expected 7 source tables, found {imported_tables}"
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

def display_summary():
    """Display overall database integrity results."""

    passed_checks = sum(
        1 for result in results
        if result["passed"]
    )

    failed_checks = len(results) - passed_checks

    print("\nDATABASE INTEGRITY SUMMARY")
    print("=" * 75)

    print(f"Total checks: {len(results)}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {failed_checks}")

    if failed_checks == 0:
        print("\nDATABASE INTEGRITY: ALL CHECKS PASSED")
    else:
        print("\nDATABASE INTEGRITY: CHECKS FAILED")

        print("\nFAILED CHECKS")
        print("-" * 75)

        for result in results:
            if not result["passed"]:
                print(
                    f"{result['check']}: {result['details']}"
                )

    print("=" * 75)


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():

    print("=" * 75)
    print("PROJECT PROOF | DATABASE INTEGRITY CHECKER")
    print("=" * 75)

    connection = connect_to_database()

    try:
        print("\nRUNNING DATABASE CHECKS")
        print("-" * 75)

        check_database_integrity(connection)
        check_table_counts(connection)
        check_duplicate_case_ids(connection)
        check_evidence_relationships(connection)
        check_priority_relationships(connection)
        check_risk_scores(connection)
        check_database_views(connection)
        check_database_indexes(connection)
        check_import_history(connection)

        display_summary()

    finally:
        connection.close()

    if any(not result["passed"] for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

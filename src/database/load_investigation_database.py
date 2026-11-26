
from pathlib import Path
import sqlite3
from datetime import datetime

import pandas as pd


# ============================================================
# PROJECT PROOF | INVESTIGATION DATABASE LOADER
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_FILE = DATABASE_DIR / "project_proof.db"

DATA_SOURCES = {
    "purchase_orders": PROJECT_ROOT / "data/raw/purchase_orders.csv",
    "supplier_invoices": PROJECT_ROOT / "data/raw/supplier_invoices.csv",
    "payment_records": PROJECT_ROOT / "data/raw/payment_records.csv",
    "investigation_cases": PROJECT_ROOT / "data/processed/investigation_cases.csv",
    "investigation_evidence": PROJECT_ROOT / "data/processed/investigation_evidence.csv",
    "investigation_priority_queue": PROJECT_ROOT / "data/processed/investigation_priority_queue.csv",
    "validation_results": PROJECT_ROOT / "data/processed/investigation_validation_results.csv",
}


# ============================================================
# DATABASE SETUP
# ============================================================

def create_database_directory():
    """Create the database directory if it does not exist."""

    DATABASE_DIR.mkdir(parents=True, exist_ok=True)


def connect_to_database():
    """Open a connection to the Project Proof SQLite database."""

    return sqlite3.connect(DATABASE_FILE)


# ============================================================
# SOURCE VALIDATION
# ============================================================

def validate_source_files():
    """Check that all required CSV files are available."""

    missing_files = [
        str(path)
        for path in DATA_SOURCES.values()
        if not path.exists()
    ]

    if missing_files:
        raise FileNotFoundError(
            "The following source files are missing:\n"
            + "\n".join(missing_files)
        )


# ============================================================
# CSV IMPORT
# ============================================================

def import_csv_files(connection):
    """Import operational and investigation CSV files into SQLite."""

    print("\nDATABASE IMPORT SUMMARY")
    print("-" * 70)

    import_summary = {}

    for table_name, file_path in DATA_SOURCES.items():

        dataframe = pd.read_csv(file_path)

        if dataframe.empty:
            print(f"WARNING: {table_name} contains no records.")

        dataframe.to_sql(
            name=table_name,
            con=connection,
            if_exists="replace",
            index=False
        )

        record_count = len(dataframe)

        import_summary[table_name] = record_count

        print(
            f"IMPORTED: {table_name:<32} "
            f"{record_count:>5} records"
        )

    return import_summary


# ============================================================
# DATABASE METADATA
# ============================================================

def create_metadata_table(connection):
    """Create a table that tracks database import history."""

    connection.execute("""
        CREATE TABLE IF NOT EXISTS database_import_history (
            import_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_table TEXT NOT NULL,
            record_count INTEGER NOT NULL,
            imported_at TEXT NOT NULL
        )
    """)


def record_import_history(connection, import_summary):
    """Record the latest import details for each source table."""

    imported_at = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    for table_name, record_count in import_summary.items():

        connection.execute(
            """
            INSERT INTO database_import_history (
                source_table,
                record_count,
                imported_at
            )
            VALUES (?, ?, ?)
            """,
            (table_name, record_count, imported_at)
        )


# ============================================================
# DATABASE INDEXES
# ============================================================

def create_database_indexes(connection):
    """Create indexes to improve common investigation queries."""

    indexes = [
        """
        CREATE INDEX IF NOT EXISTS idx_cases_case_id
        ON investigation_cases(case_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_cases_risk_level
        ON investigation_cases(risk_level)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_evidence_case_id
        ON investigation_evidence(case_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_priority_case_id
        ON investigation_priority_queue(case_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_orders_po_number
        ON purchase_orders(po_number)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_invoices_invoice_number
        ON supplier_invoices(invoice_number)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_payments_invoice_number
        ON payment_records(invoice_number)
        """
    ]

    available_tables = {
        row[0]
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()
    }

    for statement in indexes:

        table_name = statement.split("ON ")[1].split("(")[0].strip()

        if table_name in available_tables:
            connection.execute(statement)


# ============================================================
# DATABASE VIEWS
# ============================================================

def create_database_views(connection):
    """Create reusable SQL views for investigation reporting."""

    connection.execute("""
        DROP VIEW IF EXISTS high_risk_investigations
    """)

    connection.execute("""
        CREATE VIEW high_risk_investigations AS
        SELECT *
        FROM investigation_cases
        WHERE UPPER(risk_level) = 'HIGH'
    """)

    connection.execute("""
        DROP VIEW IF EXISTS investigation_evidence_summary
    """)

    connection.execute("""
        CREATE VIEW investigation_evidence_summary AS
        SELECT
            case_id,
            COUNT(*) AS evidence_count
        FROM investigation_evidence
        GROUP BY case_id
    """)


# ============================================================
# DATABASE VERIFICATION
# ============================================================

def verify_database(connection):
    """Check that imported database tables contain the expected data."""

    print("\nDATABASE VERIFICATION")
    print("-" * 70)

    tables = [
        "purchase_orders",
        "supplier_invoices",
        "payment_records",
        "investigation_cases",
        "investigation_evidence",
        "investigation_priority_queue",
        "validation_results"
    ]

    total_records = 0

    for table_name in tables:

        result = connection.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()

        record_count = result[0]
        total_records += record_count

        print(
            f"PASS: {table_name:<32} "
            f"{record_count:>5} records"
        )

    high_risk_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM high_risk_investigations
        """
    ).fetchone()[0]

    print("\nDATABASE SUMMARY")
    print("-" * 70)
    print(f"Tables imported: {len(tables)}")
    print(f"Total imported records: {total_records}")
    print(f"High-risk investigations: {high_risk_count}")

    return total_records


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():

    print("=" * 75)
    print("PROJECT PROOF | SQLITE INVESTIGATION DATABASE")
    print("=" * 75)

    create_database_directory()
    validate_source_files()

    connection = connect_to_database()

    try:
        create_metadata_table(connection)

        import_summary = import_csv_files(connection)

        create_database_indexes(connection)
        create_database_views(connection)

        record_import_history(
            connection,
            import_summary
        )

        connection.commit()

        total_records = verify_database(connection)

        connection.execute("PRAGMA optimize")
        connection.commit()

        print("\nDATABASE CREATED SUCCESSFULLY")
        print("-" * 70)
        print(f"Database location: {DATABASE_FILE}")
        print(f"Total records stored: {total_records}")
        print("SQL indexes: CREATED")
        print("SQL views: CREATED")
        print("Import history: RECORDED")

        print("=" * 75)
        print("DATABASE IMPORT: COMPLETED")
        print("=" * 75)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()

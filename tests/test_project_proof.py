
import sqlite3
import pandas as pd
import pytest

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ============================================================
# TEST 1: DATABASE EXISTS
# ============================================================

def test_database_exists():

    database = PROJECT_ROOT / "database" / "project_proof.db"

    assert database.exists()


# ============================================================
# TEST 2: DATABASE CONNECTION
# ============================================================

def test_database_connection():

    database = PROJECT_ROOT / "database" / "project_proof.db"

    connection = sqlite3.connect(database)

    result = connection.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

    connection.close()

    assert result == "ok"


# ============================================================
# TEST 3: REQUIRED DATABASE TABLES
# ============================================================

def test_required_tables_exist():

    database = PROJECT_ROOT / "database" / "project_proof.db"

    connection = sqlite3.connect(database)

    tables = {
        row[0]
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        )
    }

    connection.close()

    required_tables = {
        "purchase_orders",
        "supplier_invoices",
        "payment_records",
        "investigation_cases",
        "investigation_evidence",
        "investigation_priority_queue",
        "validation_results"
    }

    assert required_tables.issubset(tables)


# ============================================================
# TEST 4: INVESTIGATION CASE IDENTIFIERS
# ============================================================

def test_case_ids_are_unique():

    file_path = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "investigation_cases.csv"
    )

    data = pd.read_csv(file_path)

    assert data["case_id"].is_unique
    assert data["case_id"].notna().all()


# ============================================================
# TEST 5: RISK SCORES ARE VALID
# ============================================================

def test_risk_scores_are_valid():

    file_path = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "investigation_cases.csv"
    )

    data = pd.read_csv(file_path)

    assert data["risk_score"].notna().all()
    assert data["risk_score"].between(0, 100).all()


# ============================================================
# TEST 6: RISK LEVELS MATCH RISK SCORES
# ============================================================

def test_risk_levels_match_scores():

    file_path = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "investigation_cases.csv"
    )

    data = pd.read_csv(file_path)

    for _, case in data.iterrows():

        score = case["risk_score"]
        risk = case["risk_level"]

        if score >= 70:
            assert risk == "HIGH"

        elif score >= 35:
            assert risk == "MEDIUM"

        else:
            assert risk == "LOW"


# ============================================================
# TEST 7: INVESTIGATION EVIDENCE LINKS
# ============================================================

def test_evidence_links_to_existing_cases():

    cases_file = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "investigation_cases.csv"
    )

    evidence_file = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "investigation_evidence.csv"
    )

    cases = pd.read_csv(cases_file)
    evidence = pd.read_csv(evidence_file)

    case_ids = set(cases["case_id"])

    assert evidence["case_id"].notna().all()
    assert set(evidence["case_id"]).issubset(case_ids)


# ============================================================
# TEST 8: PRIORITY QUEUE IS COMPLETE
# ============================================================

def test_priority_queue_is_complete():

    cases_file = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "investigation_cases.csv"
    )

    priority_file = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "investigation_priority_queue.csv"
    )

    cases = pd.read_csv(cases_file)
    priority = pd.read_csv(priority_file)

    assert len(priority) == len(cases)
    assert set(priority["case_id"]) == set(cases["case_id"])


# ============================================================
# TEST 9: PRIORITY RANKS ARE UNIQUE
# ============================================================

def test_priority_ranks_are_unique():

    file_path = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "investigation_priority_queue.csv"
    )

    data = pd.read_csv(file_path)

    assert data["priority_rank"].is_unique
    assert data["priority_rank"].notna().all()


# ============================================================
# TEST 10: OPERATIONAL DATA EXISTS
# ============================================================

@pytest.mark.parametrize(
    "filename, expected_count",
    [
        ("purchase_orders.csv", 100),
        ("supplier_invoices.csv", 115),
        ("payment_records.csv", 105)
    ]
)
def test_operational_dataset_counts(filename, expected_count):

    file_path = (
        PROJECT_ROOT
        / "data"
        / "raw"
        / filename
    )

    data = pd.read_csv(file_path)

    assert len(data) == expected_count


# ============================================================
# TEST 11: INVESTIGATION FINDINGS EXIST
# ============================================================

def test_investigation_findings_exist():

    file_path = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "investigation_evidence.csv"
    )

    data = pd.read_csv(file_path)

    assert len(data) == 70
    assert data["issue_type"].notna().all()


# ============================================================
# TEST 12: MANAGEMENT REPORT EXISTS
# ============================================================

def test_management_report_exists():

    report = (
        PROJECT_ROOT
        / "reports"
        / "investigation_management_report.txt"
    )

    assert report.exists()
    assert report.stat().st_size > 0

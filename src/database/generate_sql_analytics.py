
from pathlib import Path
import sqlite3


# ============================================================
# PROJECT PROOF | SQL INVESTIGATION ANALYTICS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_FILE = PROJECT_ROOT / "database" / "project_proof.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def connect_to_database():
    """Connect to the Project Proof SQLite database."""

    if not DATABASE_FILE.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_FILE}"
        )

    return sqlite3.connect(DATABASE_FILE)


# ============================================================
# ANALYTICS 1: RISK DISTRIBUTION
# ============================================================

def analyse_risk_distribution(connection):

    print("\n1. INVESTIGATION RISK DISTRIBUTION")
    print("-" * 75)

    query = """
        SELECT
            UPPER(risk_level),
            COUNT(*),
            ROUND(AVG(risk_score), 2)
        FROM investigation_cases
        GROUP BY UPPER(risk_level)
        ORDER BY
            CASE UPPER(risk_level)
                WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM' THEN 2
                WHEN 'LOW' THEN 3
                ELSE 4
            END
    """

    for risk, count, score in connection.execute(query):

        print(
            f"{risk:<10} "
            f"Cases: {count:<5} "
            f"Average Score: {score}"
        )


# ============================================================
# ANALYTICS 2: SUPPLIER INVESTIGATION ACTIVITY
# ============================================================

def analyse_supplier_activity(connection):

    print("\n2. SUPPLIER INVESTIGATION ACTIVITY")
    print("-" * 75)

    query = """
        SELECT
            TRIM(supplier_id) AS supplier_id,
            COUNT(*) AS investigation_cases,
            ROUND(AVG(risk_score), 2) AS average_risk_score
        FROM (
            SELECT
                TRIM(value) AS supplier_id,
                risk_score
            FROM investigation_cases,
            json_each(
                '["' ||
                REPLACE(
                    REPLACE(COALESCE(supplier_ids, ''), ', ', '","'),
                    ',', '","'
                ) ||
                '"]'
            )
            WHERE TRIM(value) <> ''
        )
        GROUP BY supplier_id
        ORDER BY
            investigation_cases DESC,
            average_risk_score DESC
        LIMIT 10
    """

    rows = connection.execute(query).fetchall()

    for supplier_id, count, score in rows:

        print(
            f"{supplier_id:<15} "
            f"Cases: {count:<5} "
            f"Average Risk: {score}"
        )


# ============================================================
# ANALYTICS 3: MOST COMMON FINDINGS
# ============================================================

def analyse_finding_frequency(connection):

    print("\n3. MOST COMMON INVESTIGATION FINDINGS")
    print("-" * 75)

    query = """
        SELECT
            issue_type,
            COUNT(*) AS finding_count
        FROM investigation_evidence
        GROUP BY issue_type
        ORDER BY finding_count DESC, issue_type
    """

    for issue_type, count in connection.execute(query):

        print(
            f"{issue_type:<30} Findings: {count}"
        )


# ============================================================
# ANALYTICS 4: HIGHEST VALUE INVESTIGATIONS
# ============================================================

def analyse_high_value_cases(connection):

    print("\n4. HIGHEST VALUE INVESTIGATION CASES")
    print("-" * 75)

    query = """
        SELECT
            case_id,
            record_id,
            risk_level,
            risk_score,
            financial_difference,
            order_value_exposure
        FROM investigation_cases
        ORDER BY
            COALESCE(financial_difference, 0) DESC,
            COALESCE(order_value_exposure, 0) DESC
        LIMIT 10
    """

    rows = connection.execute(query).fetchall()

    for row in rows:

        (
            case_id,
            record_id,
            risk_level,
            risk_score,
            financial_difference,
            order_value
        ) = row

        print(f"\nCase: {case_id}")
        print(f"Record: {record_id}")
        print(f"Risk: {risk_level} ({risk_score})")

        print(
            f"Financial Difference: "
            f"R{float(financial_difference or 0):,.2f}"
        )

        print(
            f"Order Value Exposure: "
            f"R{float(order_value or 0):,.2f}"
        )


# ============================================================
# ANALYTICS 5: INVESTIGATION PRIORITIES
# ============================================================

def analyse_priority_queue(connection):

    print("\n5. TOP PRIORITY INVESTIGATIONS")
    print("-" * 75)

    query = """
        SELECT
            case_id,
            priority_rank,
            risk_level,
            risk_score,
            recommended_action
        FROM investigation_priority_queue
        ORDER BY priority_rank ASC
        LIMIT 10
    """

    rows = connection.execute(query).fetchall()

    for case_id, rank, risk, score, action in rows:

        print(f"\nPriority Rank: {rank}")
        print(f"Case: {case_id}")
        print(f"Risk: {risk}")
        print(f"Risk Score: {score}")
        print(f"Recommended Action: {action}")


# ============================================================
# ANALYTICS 6: INVESTIGATION EVIDENCE COVERAGE
# ============================================================

def analyse_evidence_coverage(connection):

    print("\n6. INVESTIGATION EVIDENCE COVERAGE")
    print("-" * 75)

    query = """
        SELECT
            cases.case_id,
            cases.risk_level,
            COUNT(evidence.case_id) AS evidence_count
        FROM investigation_cases AS cases
        LEFT JOIN investigation_evidence AS evidence
            ON cases.case_id = evidence.case_id
        GROUP BY
            cases.case_id,
            cases.risk_level
        ORDER BY
            evidence_count DESC,
            cases.case_id
        LIMIT 10
    """

    for case_id, risk, count in connection.execute(query):

        print(
            f"{case_id:<15} "
            f"Risk: {risk:<10} "
            f"Evidence Records: {count}"
        )


# ============================================================
# ANALYTICS 7: SUPPLIER INVESTIGATION RISK
# ============================================================

def analyse_supplier_risk(connection):

    print("\n7. SUPPLIER INVESTIGATION RISK")
    print("-" * 75)

    query = """
        SELECT
            TRIM(value) AS supplier_id,
            COUNT(*) AS investigation_cases,
            SUM(
                CASE
                    WHEN UPPER(risk_level) = 'HIGH' THEN 1
                    ELSE 0
                END
            ) AS high_risk_cases,
            ROUND(AVG(risk_score), 2) AS average_risk_score
        FROM investigation_cases,
        json_each(
            '["' ||
            REPLACE(
                REPLACE(COALESCE(supplier_ids, ''), ', ', '","'),
                ',', '","'
            ) ||
            '"]'
        )
        WHERE TRIM(value) <> ''
        GROUP BY TRIM(value)
        ORDER BY
            high_risk_cases DESC,
            average_risk_score DESC
    """

    rows = connection.execute(query).fetchall()

    for supplier_id, total, high_risk, average_score in rows:

        print(f"\nSupplier: {supplier_id}")
        print(f"Investigation Cases: {total}")
        print(f"High-Risk Cases: {high_risk}")
        print(f"Average Risk Score: {average_score}")


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():

    print("=" * 75)
    print("PROJECT PROOF | SQL INVESTIGATION ANALYTICS")
    print("=" * 75)

    connection = connect_to_database()

    try:

        analyse_risk_distribution(connection)
        analyse_supplier_activity(connection)
        analyse_finding_frequency(connection)
        analyse_high_value_cases(connection)
        analyse_priority_queue(connection)
        analyse_evidence_coverage(connection)
        analyse_supplier_risk(connection)

        print("\n" + "=" * 75)
        print("SQL ANALYTICS: COMPLETED")
        print("=" * 75)

    finally:
        connection.close()


if __name__ == "__main__":
    main()

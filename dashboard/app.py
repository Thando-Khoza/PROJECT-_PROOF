
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# PROJECT PROOF | FINANCIAL INVESTIGATION PLATFORM
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

CASES_FILE = PROCESSED_DIR / "investigation_cases.csv"
EVIDENCE_FILE = PROCESSED_DIR / "investigation_evidence.csv"
PRIORITY_FILE = PROCESSED_DIR / "investigation_priority_queue.csv"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Project Proof | Financial Intelligence",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: 1px;
    }

    .subtitle {
        color: #8994A5;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    div[data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.07);
        border: 1px solid rgba(128, 128, 128, 0.18);
        padding: 16px;
        border-radius: 10px;
    }

    div[data-testid="stMetricLabel"] {
        font-weight: 600;
    }

    .section-label {
        font-size: 1.1rem;
        font-weight: 700;
        margin-top: 1rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_data():

    required_files = [
        CASES_FILE,
        EVIDENCE_FILE,
        PRIORITY_FILE
    ]

    for file_path in required_files:
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file not found: {file_path}"
            )

    cases = pd.read_csv(CASES_FILE)
    evidence = pd.read_csv(EVIDENCE_FILE)
    priorities = pd.read_csv(PRIORITY_FILE)

    return cases, evidence, priorities


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_currency(value):

    try:
        if pd.isna(value):
            return "R0.00"

        return f"R{float(value):,.2f}"

    except (ValueError, TypeError):
        return "Not available"


def numeric_column(data, column):

    if column not in data.columns:
        return pd.Series(0.0, index=data.index)

    return pd.to_numeric(
        data[column],
        errors="coerce"
    ).fillna(0)


def safe_text(value):

    if pd.isna(value):
        return "Not available"

    return str(value)


def get_supplier_text(row):

    supplier_ids = safe_text(
        row.get("supplier_ids", "")
    )

    supplier_names = safe_text(
        row.get("supplier_name", "")
    )

    if supplier_names != "Not available":
        return supplier_names

    if supplier_ids != "Not available":
        return supplier_ids

    return "Not available"


def prepare_data(cases, evidence, priorities):

    cases = cases.copy()
    evidence = evidence.copy()
    priorities = priorities.copy()

    cases["case_id"] = cases["case_id"].astype(str)

    cases["risk_level"] = (
        cases["risk_level"]
        .fillna("UNCLASSIFIED")
        .astype(str)
        .str.upper()
    )

    cases["risk_score"] = pd.to_numeric(
        cases["risk_score"],
        errors="coerce"
    )

    cases["financial_difference"] = numeric_column(
        cases,
        "financial_difference"
    )

    cases["order_value_exposure"] = numeric_column(
        cases,
        "order_value_exposure"
    )

    evidence["case_id"] = evidence["case_id"].astype(str)

    priorities["case_id"] = priorities["case_id"].astype(str)

    # Summarise evidence without removing original records.

    if "issue_type" in evidence.columns:

        evidence_summary = (
            evidence.groupby("case_id")
            .agg(
                evidence_count=("issue_type", "count"),
                detected_issues=(
                    "issue_type",
                    lambda values: ", ".join(
                        sorted(
                            set(values.dropna().astype(str))
                        )
                    )
                )
            )
            .reset_index()
        )

    else:

        evidence_summary = (
            evidence.groupby("case_id")
            .size()
            .reset_index(name="evidence_count")
        )

    cases = cases.merge(
        evidence_summary,
        on="case_id",
        how="left",
        validate="one_to_one"
    )

    cases["evidence_count"] = (
        cases["evidence_count"]
        .fillna(0)
        .astype(int)
    )

    if "detected_issues" not in cases.columns:
        cases["detected_issues"] = ""

    # Add priority information.

    priority_columns = [
        column for column in [
            "case_id",
            "priority_rank",
            "recommended_action",
            "investigation_status"
        ]
        if column in priorities.columns
    ]

    priority_data = priorities[priority_columns].drop_duplicates(
        subset=["case_id"]
    )

    cases = cases.merge(
        priority_data,
        on="case_id",
        how="left",
        suffixes=("", "_priority"),
        validate="one_to_one"
    )

    cases["supplier_display"] = cases.apply(
        get_supplier_text,
        axis=1
    )

    cases["priority_rank"] = pd.to_numeric(
        cases.get(
            "priority_rank",
            pd.Series(index=cases.index, dtype="float64")
        ),
        errors="coerce"
    )

    return cases, evidence, priorities


def apply_filters(
    data,
    selected_risks,
    selected_issues,
    search_term
):

    filtered = data.copy()

    filtered = filtered[
        filtered["risk_level"].isin(selected_risks)
    ]

    if selected_issues:

        filtered = filtered[
            filtered["detected_issues"].fillna("").apply(
                lambda value: any(
                    issue in str(value).split(", ")
                    for issue in selected_issues
                )
            )
        ]

    if search_term.strip():

        searchable_columns = [
            column for column in [
                "case_id",
                "record_id",
                "record_type",
                "supplier_ids",
                "supplier_name"
            ]
            if column in filtered.columns
        ]

        matches = pd.Series(
            False,
            index=filtered.index
        )

        for column in searchable_columns:

            matches |= (
                filtered[column]
                .fillna("")
                .astype(str)
                .str.contains(
                    search_term,
                    case=False,
                    na=False,
                    regex=False
                )
            )

        filtered = filtered[matches]

    return filtered


# ============================================================
# LOAD AND VALIDATE DATA
# ============================================================

st.markdown(
    '<div class="main-title">PROJECT PROOF</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Supplier Financial Investigation and Risk Intelligence Platform'
    '</div>',
    unsafe_allow_html=True
)

try:

    raw_cases, raw_evidence, priorities = load_data()

except (FileNotFoundError, pd.errors.EmptyDataError) as error:

    st.error(f"Unable to load project data: {error}")
    st.stop()

except Exception as error:

    st.error(f"Unexpected data loading error: {error}")
    st.stop()


required_columns = {
    "case_id",
    "risk_level",
    "risk_score"
}

missing_columns = required_columns - set(raw_cases.columns)

if missing_columns:

    st.error(
        "Investigation cases are missing required columns: "
        + ", ".join(sorted(missing_columns))
    )

    st.stop()

if "case_id" not in raw_evidence.columns:

    st.error("Evidence data is missing the case_id column.")
    st.stop()

if "case_id" not in priorities.columns:

    st.error("Priority data is missing the case_id column.")
    st.stop()

cases, evidence, priorities = prepare_data(
    raw_cases,
    raw_evidence,
    priorities
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("Investigation Controls")

st.sidebar.caption(
    "Filter and explore the investigation database."
)

available_risks = sorted(
    cases["risk_level"].dropna().unique().tolist()
)

selected_risks = st.sidebar.multiselect(
    "Risk classification",
    options=available_risks,
    default=available_risks
)

available_issues = sorted({
    issue.strip()
    for values in cases["detected_issues"].dropna()
    for issue in str(values).split(",")
    if issue.strip()
})

selected_issues = st.sidebar.multiselect(
    "Finding classification",
    options=available_issues,
    default=available_issues
)

search_term = st.sidebar.text_input(
    "Search investigations",
    placeholder="Case ID, supplier or record..."
)

if st.sidebar.button(
    "Refresh dashboard",
    use_container_width=True
):

    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()

st.sidebar.caption(
    "PROJECT PROOF\n\n"
    "Automated financial verification and investigation."
)


# ============================================================
# FILTER DATA
# ============================================================

filtered_cases = apply_filters(
    cases,
    selected_risks,
    selected_issues,
    search_term
)


# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================

st.header("Executive Overview")

total_cases = len(cases)

high_cases = int(
    (cases["risk_level"] == "HIGH").sum()
)

medium_cases = int(
    (cases["risk_level"] == "MEDIUM").sum()
)

low_cases = int(
    (cases["risk_level"] == "LOW").sum()
)

total_evidence = len(evidence)

total_findings = (
    evidence["issue_type"].notna().sum()
    if "issue_type" in evidence.columns
    else total_evidence
)

average_risk = cases["risk_score"].mean()

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric(
    "Investigation Cases",
    f"{total_cases:,}"
)

metric2.metric(
    "High-Risk Cases",
    f"{high_cases:,}"
)

metric3.metric(
    "Evidence Records",
    f"{total_evidence:,}"
)

metric4.metric(
    "Average Risk Score",
    f"{average_risk:.1f}/100"
    if pd.notna(average_risk)
    else "N/A"
)

st.caption(
    f"{total_findings} evidence findings recorded across "
    f"{total_cases} investigation cases."
)

st.divider()


# ============================================================
# DASHBOARD TABS
# ============================================================

overview_tab, financial_tab, investigations_tab, quality_tab = st.tabs(
    [
        "Executive Overview",
        "Financial Analysis",
        "Investigations",
        "Data Quality"
    ]
)


# ============================================================
# TAB 1: EXECUTIVE OVERVIEW
# ============================================================

with overview_tab:

    st.subheader("Investigation Risk Distribution")

    chart_col, issue_col = st.columns(2)

    with chart_col:

        risk_distribution = (
            cases["risk_level"]
            .value_counts()
            .reindex(
                ["HIGH", "MEDIUM", "LOW"],
                fill_value=0
            )
        )

        risk_chart = pd.DataFrame({
            "Risk Level": risk_distribution.index,
            "Cases": risk_distribution.values
        })

        st.bar_chart(
            risk_chart.set_index("Risk Level")
        )

    with issue_col:

        if "issue_type" in evidence.columns:

            issue_counts = (
                evidence["issue_type"]
                .value_counts()
                .rename_axis("Finding Type")
                .reset_index(name="Records")
            )

            st.bar_chart(
                issue_counts.set_index("Finding Type")
            )

        else:

            st.info("Finding classifications are unavailable.")

    st.divider()

    st.subheader("Investigation Priority")

    priority_columns = [
        column for column in [
            "case_id",
            "record_id",
            "risk_level",
            "risk_score",
            "priority_rank",
            "supplier_ids",
            "financial_difference",
            "order_value_exposure"
        ]
        if column in cases.columns
    ]

    top_priority = cases.sort_values(
        ["risk_score", "priority_rank"],
        ascending=[False, True],
        na_position="last"
    ).head(10)

    st.dataframe(
        top_priority[priority_columns],
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TAB 2: FINANCIAL ANALYSIS
# ============================================================

with financial_tab:

    st.subheader("Financial Exposure Analysis")

    financial_total = cases[
        "financial_difference"
    ].sum()

    order_exposure = cases[
        "order_value_exposure"
    ].sum()

    financial_col, order_col = st.columns(2)

    financial_col.metric(
        "Recorded Financial Differences",
        format_currency(financial_total)
    )

    order_col.metric(
        "Purchase Order Value Exposure",
        format_currency(order_exposure)
    )

    st.caption(
        "These are recorded case-level values, not confirmed losses. "
        "Purchase order exposure and financial differences represent "
        "different measures and should not be added together."
    )

    st.divider()

    st.subheader("Financial Exposure by Risk Level")

    exposure_data = (
        cases.groupby("risk_level")
        .agg(
            financial_difference=("financial_difference", "sum"),
            order_value_exposure=("order_value_exposure", "sum")
        )
        .reindex(["HIGH", "MEDIUM", "LOW"])
        .fillna(0)
    )

    st.bar_chart(exposure_data)

    st.divider()

    st.subheader("Highest Financial Difference Cases")

    highest_exposure = cases.sort_values(
        "financial_difference",
        ascending=False
    ).head(10)

    financial_display = [
        column for column in [
            "case_id",
            "record_id",
            "risk_level",
            "financial_difference",
            "order_value_exposure"
        ]
        if column in highest_exposure.columns
    ]

    st.dataframe(
        highest_exposure[financial_display],
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TAB 3: INVESTIGATIONS
# ============================================================

with investigations_tab:

    st.subheader("Investigation Case Register")

    st.write(
        f"Showing {len(filtered_cases)} of {total_cases} cases."
    )

    display_columns = [
        column for column in [
            "case_id",
            "record_id",
            "supplier_display",
            "risk_level",
            "risk_score",
            "evidence_count",
            "detected_issues",
            "priority_rank",
            "investigation_status"
        ]
        if column in filtered_cases.columns
    ]

    if filtered_cases.empty:

        st.info("No cases match the selected filters.")

    else:

        st.dataframe(
            filtered_cases[display_columns],
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("Individual Case Review")

        case_options = sorted(
            filtered_cases["case_id"].astype(str).unique()
        )

        selected_case_id = st.selectbox(
            "Select an investigation case",
            options=case_options
        )

        selected_case = filtered_cases[
            filtered_cases["case_id"].astype(str)
            == selected_case_id
        ].iloc[0]

        detail1, detail2, detail3 = st.columns(3)

        detail1.metric(
            "Risk Classification",
            selected_case["risk_level"]
        )

        detail2.metric(
            "Risk Score",
            f"{selected_case['risk_score']:.0f}/100"
            if pd.notna(selected_case["risk_score"])
            else "N/A"
        )

        detail3.metric(
            "Evidence Records",
            int(selected_case["evidence_count"])
        )

        st.divider()

        information_col, exposure_col = st.columns(2)

        with information_col:

            st.markdown("**Record Information**")

            for column in [
                "record_id",
                "record_type",
                "supplier_ids",
                "supplier_name",
                "issue_types",
                "risk_explanation"
            ]:

                if column in selected_case.index:

                    st.write(
                        f"**{column.replace('_', ' ').title()}:** "
                        f"{safe_text(selected_case[column])}"
                    )

        with exposure_col:

            st.markdown("**Financial Information**")

            st.write(
                "**Financial Difference:** "
                + format_currency(
                    selected_case["financial_difference"]
                )
            )

            st.write(
                "**Order Value Exposure:** "
                + format_currency(
                    selected_case["order_value_exposure"]
                )
            )

            if "priority_rank" in selected_case.index:

                st.write(
                    "**Priority Rank:** "
                    + safe_text(selected_case["priority_rank"])
                )

        st.divider()

        st.markdown("**Supporting Investigation Evidence**")

        case_evidence = evidence[
            evidence["case_id"].astype(str) == selected_case_id
        ].copy()

        if not case_evidence.empty:

            st.dataframe(
                case_evidence,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("No evidence records are linked to this case.")

        st.markdown("**Recommended Investigation Action**")

        if "recommended_action" in selected_case.index:

            st.info(
                safe_text(selected_case["recommended_action"])
            )

        else:

            st.info("No recommended action is available.")

        st.caption(
            "Automated findings identify matters requiring human review. "
            "They do not independently establish fraud or confirm losses."
        )


# ============================================================
# TAB 4: DATA QUALITY
# ============================================================

with quality_tab:

    st.subheader("Data Quality and System Coverage")

    quality1, quality2, quality3 = st.columns(3)

    quality1.metric(
        "Case Records",
        f"{len(cases):,}"
    )

    quality2.metric(
        "Evidence Records",
        f"{len(evidence):,}"
    )

    quality3.metric(
        "Priority Records",
        f"{len(priorities):,}"
    )

    st.divider()

    st.subheader("Case ID Integrity")

    unique_cases = cases["case_id"].nunique()

    duplicate_cases = int(
        cases["case_id"].duplicated().sum()
    )

    evidence_case_ids = set(
        evidence["case_id"].dropna()
    )

    known_case_ids = set(
        cases["case_id"].dropna()
    )

    orphan_evidence = len(
        evidence_case_ids - known_case_ids
    )

    check1, check2, check3 = st.columns(3)

    check1.metric(
        "Unique Case IDs",
        unique_cases
    )

    check2.metric(
        "Duplicate Case Rows",
        duplicate_cases
    )

    check3.metric(
        "Unlinked Evidence Case IDs",
        orphan_evidence
    )

    if duplicate_cases == 0 and orphan_evidence == 0:

        st.success(
            "Case identifiers are unique and evidence references "
            "match existing investigation cases."
        )

    else:

        st.warning(
            "Review duplicate case records or evidence references."
        )

    st.divider()

    st.subheader("Risk Classification Coverage")

    risk_quality = (
        cases["risk_level"]
        .value_counts()
        .rename_axis("Risk Level")
        .reset_index(name="Cases")
    )

    st.dataframe(
        risk_quality,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Missing Value Review")

    missing_data = pd.DataFrame({
        "Dataset": [
            "Investigation Cases",
            "Investigation Evidence",
            "Priority Queue"
        ],
        "Rows": [
            len(cases),
            len(evidence),
            len(priorities)
        ],
        "Missing Values": [
            int(cases.isna().sum().sum()),
            int(evidence.isna().sum().sum()),
            int(priorities.isna().sum().sum())
        ]
    })

    st.dataframe(
        missing_data,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# EXPORTS
# ============================================================

st.divider()

st.header("Export Investigation Data")

export1, export2, export3 = st.columns(3)

with export1:

    st.download_button(
        "Download Filtered Cases",
        data=filtered_cases.to_csv(
            index=False
        ).encode("utf-8"),
        file_name="project_proof_filtered_cases.csv",
        mime="text/csv",
        use_container_width=True
    )

with export2:

    st.download_button(
        "Download All Evidence",
        data=evidence.to_csv(
            index=False
        ).encode("utf-8"),
        file_name="project_proof_investigation_evidence.csv",
        mime="text/csv",
        use_container_width=True
    )

with export3:

    st.download_button(
        "Download Priority Queue",
        data=priorities.to_csv(
            index=False
        ).encode("utf-8"),
        file_name="project_proof_priority_queue.csv",
        mime="text/csv",
        use_container_width=True
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "PROJECT PROOF | Supplier Financial Investigation Platform"
)

st.caption(
    "Python | Pandas | SQLite | SQL | Streamlit | Automated Testing"
)

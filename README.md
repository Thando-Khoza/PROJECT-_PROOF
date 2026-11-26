# PROJECT PROOF
### Supplier Financial Verification & Investigation Platform

PROJECT PROOF is a Python-based financial analysis platform designed to identify discrepancies, unusual transaction patterns, and potential risks across supplier purchase orders, invoices, and payment records.

The platform automates financial reconciliation, detects irregularities, generates evidence-backed investigation cases, and prioritises findings to support better financial oversight and decision-making.

## Key Features

- Financial data processing and validation
- Automated invoice and payment reconciliation
- Duplicate transaction and discrepancy detection
- Statistical anomaly detection
- Evidence-based investigation management
- Automated risk scoring and prioritisation
- SQL-based financial analytics
- Management reporting and Excel exports
- Interactive Streamlit dashboard
- Automated testing and database validation

## Technology Stack

- Python
- Pandas
- SQL and SQLite
- Streamlit
- Matplotlib
- OpenPyXL
- Pytest
- Git and GitHub

## Project Results

| Metric | Result |
|---|---:|
| Investigation Cases | 60 |
| Evidence Records | 70 |
| High-Risk Cases | 5 |
| Database Records | 520 |
| Automated Tests Passed | 14 |
| Pipeline Steps Completed | 20/20 |

The detection components achieved 100% precision, recall, and F1-score against the relevant controlled synthetic test cases. These results reflect performance on the generated test data, not guaranteed real-world accuracy.

## Dashboard Preview

### Executive Overview
![Executive Overview](screenshots/01_executive_overview.png)

### Financial Analysis
![Financial Analysis](screenshots/02_financial_analysis.png)

### Investigation Register
![Investigation Register](screenshots/03_investigation_register.png)

### Individual Case Review
![Individual Case Review](screenshots/04_individual_case_review.png)

### Data Quality
![Data Quality](screenshots/05_data_quality.png)

### Data Exports
![Data Exports](screenshots/06_data_exports.png)

## Getting Started

Clone the repository:

```bash
git clone https://github.com/Thando-Khoza/PROJECT_PROOF.git
cd PROJECT_PROOF
```

Install dependencies:

```bash
pip install pandas streamlit matplotlib openpyxl pytest
```

Run the complete project pipeline:

```bash
python src/run_project_proof.py
```

Launch the interactive dashboard:

```bash
streamlit run dashboard/app.py
```

## Project Purpose

PROJECT PROOF demonstrates how programming, data analytics, statistical methods, database management, and automation can be combined to solve practical financial verification problems.

## Project Status

**Completed | Version 1.0**

*Built with Python, SQL, and Streamlit.*

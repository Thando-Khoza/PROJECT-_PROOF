
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo


# ============================================================
# PROJECT PROOF | INVESTIGATION REPORT EXPORTER
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "reports"

OUTPUT_FILE = OUTPUT_DIR / "project_proof_investigation_pack.xlsx"

INPUT_FILES = {
    "Investigation Cases": PROCESSED_DIR / "investigation_cases.csv",
    "Evidence Records": PROCESSED_DIR / "investigation_evidence.csv",
    "Priority Queue": PROCESSED_DIR / "investigation_priority_queue.csv",
    "Validation Results": PROCESSED_DIR / "investigation_validation_results.csv",
}


def load_csv(file_path):
    """Load records and column names from a CSV file."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {file_path}"
        )

    with file_path.open(
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:
        reader = csv.DictReader(file)

        headers = reader.fieldnames

        if not headers:
            raise ValueError(
                f"No column headers found in: {file_path.name}"
            )

        records = list(reader)

    return headers, records


def style_worksheet(worksheet):
    """Apply consistent formatting to a worksheet."""

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="1F4E78"
    )

    header_font = Font(
        bold=True,
        color="FFFFFF",
        size=11
    )

    thin_border = Border(
        bottom=Side(
            style="thin",
            color="D9E2F3"
        )
    )

    for cell in worksheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    worksheet.row_dimensions[1].height = 25

    for row in worksheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(
                vertical="center"
            )
            cell.border = thin_border

    worksheet.freeze_panes = "A2"
    worksheet.sheet_view.showGridLines = False

    if worksheet.max_row >= 2 and worksheet.max_column >= 1:
        worksheet.auto_filter.ref = worksheet.dimensions

    # Set readable column widths.
    for column_cells in worksheet.columns:
        column_letter = get_column_letter(
            column_cells[0].column
        )

        maximum_length = 0

        for cell in column_cells:
            if cell.value is not None:
                maximum_length = max(
                    maximum_length,
                    len(str(cell.value))
                )

        worksheet.column_dimensions[column_letter].width = min(
            max(maximum_length + 3, 14),
            45
        )


def add_excel_table(worksheet, table_name):
    """Add an Excel table when the worksheet contains records."""

    if worksheet.max_row < 2 or worksheet.max_column < 1:
        return

    table = Table(
        displayName=table_name,
        ref=worksheet.dimensions
    )

    table_style = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False
    )

    table.tableStyleInfo = table_style

    worksheet.add_table(table)


def add_worksheet(workbook, sheet_name, headers, records, table_name):
    """Create and populate one worksheet."""

    worksheet = workbook.create_sheet(
        title=sheet_name
    )

    worksheet.append(headers)

    for record in records:
        worksheet.append([
            record.get(header, "")
            for header in headers
        ])

    style_worksheet(worksheet)
    add_excel_table(worksheet, table_name)

    return worksheet


def create_workbook():
    """Build the complete investigation workbook."""

    workbook = Workbook()

    # Remove the default blank worksheet.
    default_sheet = workbook.active
    workbook.remove(default_sheet)

    # Create all four investigation worksheets.
    for index, (sheet_name, file_path) in enumerate(
        INPUT_FILES.items(),
        start=1
    ):
        headers, records = load_csv(file_path)

        add_worksheet(
            workbook,
            sheet_name,
            headers,
            records,
            f"ProjectProofTable{index}"
        )

        print(
            f"PASS: {sheet_name} | "
            f"{len(records)} records exported."
        )

    # Save the workbook.
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    workbook.save(OUTPUT_FILE)

    return workbook


def main():
    print("=" * 75)
    print("PROJECT PROOF | INVESTIGATION REPORT EXPORTER")
    print("=" * 75)

    workbook = create_workbook()

    print("\nEXPORT SUMMARY")
    print("-" * 75)

    for worksheet in workbook.worksheets:
        print(
            f"{worksheet.title}: "
            f"{worksheet.max_row - 1} records"
        )

    print("\nWORKBOOK GENERATED")
    print("-" * 75)
    print(OUTPUT_FILE.relative_to(PROJECT_ROOT))

    print("\nINVESTIGATION REPORT EXPORT: COMPLETED")
    print("=" * 75)


if __name__ == "__main__":
    main()

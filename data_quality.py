import pandas as pd


def check_data_quality(df):
    """
    Checks the uploaded dataset for common data quality problems.
    """

    missing_values = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    empty_columns = [
        column
        for column in df.columns
        if df[column].isnull().all()
    ]

    return {
        "missing_values": missing_values,
        "duplicate_rows": duplicate_rows,
        "empty_columns": empty_columns,
        "rows": len(df),
        "columns": len(df.columns)
    }


def get_quality_status(report):
    """
    Converts the data quality report into a simple status.
    """

    problems = []

    if report["missing_values"] > 0:
        problems.append(
            f"{report['missing_values']} missing values found"
        )

    if report["duplicate_rows"] > 0:
        problems.append(
            f"{report['duplicate_rows']} duplicate rows found"
        )

    if report["empty_columns"]:
        problems.append(
            "Empty columns: "
            + ", ".join(report["empty_columns"])
        )

    if problems:
        return {
            "status": "WARNING",
            "problems": problems
        }

    return {
        "status": "GOOD",
        "problems": []
    }
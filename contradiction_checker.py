def find_common_columns(df1, df2):
    """
    Finds columns shared by two dataframes.
    """

    return list(
        set(df1.columns).intersection(set(df2.columns))
    )


def find_contradictions(df1, df2):
    """
    Looks for conflicting values when two datasets
    share an identifier column.
    """

    common_columns = find_common_columns(df1, df2)

    if not common_columns:
        return []

    # Try common identifier columns first
    id_columns = [
        column
        for column in common_columns
        if column.lower() in [
            "id",
            "order_id",
            "customer_id",
            "product_id",
            "transaction_id"
        ]
    ]

    if not id_columns:
        return []

    id_column = id_columns[0]

    common_ids = set(df1[id_column].dropna()).intersection(
        set(df2[id_column].dropna())
    )

    contradictions = []

    for record_id in common_ids:

        row1 = df1[df1[id_column] == record_id].iloc[0]
        row2 = df2[df2[id_column] == record_id].iloc[0]

        for column in common_columns:

            if column == id_column:
                continue

            value1 = row1[column]
            value2 = row2[column]

            if (
                str(value1) != str(value2)
                and str(value1) != "nan"
                and str(value2) != "nan"
            ):

                contradictions.append({
                    "id": record_id,
                    "column": column,
                    "source_1": value1,
                    "source_2": value2
                })

    return contradictions
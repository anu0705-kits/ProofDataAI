def detect_question_ambiguity(question, dataframes):
    """
    Detects simple cases where the question may not be
    reliable enough to answer automatically.
    """

    question_lower = question.lower()

    warnings = []

    # Currency-related ambiguity
    currencies = set()

    for df in dataframes:

        for column in df.columns:

            if column.lower() in [
                "currency",
                "currencies",
                "currency_code"
            ]:

                values = (
                    df[column]
                    .dropna()
                    .astype(str)
                    .str.upper()
                    .unique()
                )

                currencies.update(values)

    if len(currencies) > 1:

        financial_words = [
            "revenue",
            "sales",
            "price",
            "cost",
            "profit",
            "amount",
            "income"
        ]

        if any(word in question_lower for word in financial_words):

            warnings.append(
                "Multiple currencies are present. "
                "The financial values cannot be safely combined "
                "without a conversion rule."
            )

    # Date ambiguity
    date_words = [
        "date",
        "day",
        "month",
        "year",
        "2025",
        "2026"
    ]

    if any(word in question_lower for word in date_words):

        warnings.append(
            "Verify the date format and date range before answering."
        )

    return warnings


def is_ambiguous(warnings):

    return len(warnings) > 0
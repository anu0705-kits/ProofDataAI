def detect_currencies(dataframes):
    """
    Detects currencies present in one or more dataframes.
    """

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

    return sorted(currencies)


def check_currency_mismatch(dataframes):
    """
    Checks whether multiple currencies are present.
    """

    currencies = detect_currencies(dataframes)

    if len(currencies) == 0:

        return {
            "has_currency": False,
            "mismatch": False,
            "currencies": []
        }

    if len(currencies) == 1:

        return {
            "has_currency": True,
            "mismatch": False,
            "currencies": currencies
        }

    return {
        "has_currency": True,
        "mismatch": True,
        "currencies": currencies
    }


def currency_warning(result):

    if result["mismatch"]:

        return (
            "Multiple currencies detected: "
            + ", ".join(result["currencies"])
            + ". Directly combining them is unsafe."
        )

    if result["has_currency"]:

        return (
            "Currency detected: "
            + ", ".join(result["currencies"])
        )

    return "No currency column detected."
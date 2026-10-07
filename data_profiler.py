def profile_dataframe(df):

    profile = {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_values": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns_list": list(df.columns)
    }

    return profile
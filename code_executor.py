def calculate(df, operation, column):

    values = df[column].dropna()

    if operation == "sum":
        return values.sum()

    elif operation == "average":
        return values.mean()

    elif operation == "max":
        return values.max()

    elif operation == "min":
        return values.min()

    else:
        return None
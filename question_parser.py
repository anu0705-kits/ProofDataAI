def parse_question(question):

    question = question.lower()

    if "total" in question or "sum" in question:
        operation = "sum"

    elif "average" in question or "avg" in question:
        operation = "average"

    elif "maximum" in question or "highest" in question:
        operation = "max"

    elif "minimum" in question or "lowest" in question:
        operation = "min"

    else:
        operation = "unknown"

    return operation
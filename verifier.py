def verify_result(calculated_result, independent_result):
    """
    Compares the main calculation with an independent
    verification result.
    """

    try:

        calculated = float(calculated_result)
        independent = float(independent_result)

        difference = abs(calculated - independent)

        if difference < 0.000001:

            return {
                "verified": True,
                "difference": difference,
                "message": "Result verified successfully."
            }

        return {
            "verified": False,
            "difference": difference,
            "message": (
                "Verification failed. "
                "The two calculations do not match."
            )
        }

    except (ValueError, TypeError):

        return {
            "verified": False,
            "difference": None,
            "message": "Unable to verify the result."
        }
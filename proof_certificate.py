from datetime import datetime
import hashlib


def create_proof_id(question, result):

    text = (
        question
        + str(result)
        + datetime.now().isoformat()
    )

    return "PD-" + hashlib.sha256(
        text.encode()
    ).hexdigest()[:10].upper()


def create_certificate(
    question,
    result,
    dataset_name,
    operation,
    rows_used,
    verification_status
):

    proof_id = create_proof_id(
        question,
        result
    )

    return {
        "proof_id": proof_id,
        "question": question,
        "answer": result,
        "dataset": dataset_name,
        "operation": operation,
        "rows_used": rows_used,
        "verification": verification_status,
        "generated_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }
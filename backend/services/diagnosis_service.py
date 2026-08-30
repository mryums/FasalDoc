"""Diagnosis service layer.

The logic below is a TEMPORARY MOCK. It will be replaced by the real
Qwen/Alibaba Cloud AI service implemented by Member 1. Keep the function
signatures stable so routes don't need to change when the AI layer lands.
"""


def run_diagnosis(filename: str) -> dict:
    """TEMPORARY MOCK diagnosis — replace with Qwen AI service call."""
    return {
        "filename": filename,
        "diagnosis": "Early Blight",
        "confidence": 0.70,
        "advice": "Remove affected leaves and improve airflow around the plant.",
        "needs_expert": False,
    }


def answer_followup(question: str) -> str:
    """TEMPORARY MOCK follow-up answer — replace with Qwen AI service call."""
    return "This is a temporary response. AI integration will be added later."

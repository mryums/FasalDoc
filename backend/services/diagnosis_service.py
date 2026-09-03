import os


class MockDiagnosisProvider:
    """Offline diagnosis provider used when no AI credentials are available."""

    def diagnose(self, filename, data=None, content_type=None):
        return {
            "filename": filename,
            "diagnosis": "Unknown plant disease",
            "confidence": 0.50,
            "advice": "Please consult an agricultural expert for confirmation.",
            "needs_expert": True,
        }

    def answer(self, question):
        return (
            "This is a preliminary response. "
            "For accurate agricultural advice, please consult an expert."
        )


class DiagnosisProvider:
    """Base provider interface."""

    def diagnose(self, filename, data=None, content_type=None):
        raise NotImplementedError

    def answer(self, question):
        raise NotImplementedError


_provider = None


def get_provider():
    global _provider

    if _provider is None:
        api_key = os.getenv("DASHSCOPE_API_KEY")

        if api_key:
            # AI provider will be connected later.
            # For now, keep the system offline and safe.
            _provider = MockDiagnosisProvider()
        else:
            _provider = MockDiagnosisProvider()

    return _provider


def reset_provider():
    global _provider
    _provider = None


def run_diagnosis(filename, data=None, content_type=None):
    provider = get_provider()

    return provider.diagnose(
        filename,
        data=data,
        content_type=content_type,
    )


def answer_followup(question):
    provider = get_provider()
    return provider.answer(question)
class AIServiceError(RuntimeError):
    code = "ai_service_unavailable"
    public_message = "The AI service is temporarily unavailable. Please try again later."
    status_code = 502


class AIConfigurationError(AIServiceError):
    code = "ai_not_configured"
    public_message = "The AI service is not configured."
    status_code = 503


class AIInvalidCredentialError(AIServiceError):
    code = "ai_invalid_credentials"
    public_message = "The AI service credentials are invalid or unavailable."
    status_code = 502


class AIThrottledError(AIServiceError):
    code = "ai_rate_limited"
    public_message = "The AI service is busy. Please try again shortly."
    status_code = 429


class AITimeoutError(AIServiceError):
    code = "ai_timeout"
    public_message = "The AI service took too long to respond. Please try again."
    status_code = 504


class AIUpstreamError(AIServiceError):
    code = "ai_upstream_failure"


class AIInvalidModelOutputError(AIServiceError):
    code = "ai_invalid_model_output"
    public_message = "The AI service returned an unusable response. Please try again."


def translate_provider_error(error: Exception) -> AIServiceError:
    if isinstance(error, AIServiceError):
        return error

    status_code = getattr(error, "status_code", None)
    error_name = type(error).__name__.lower()

    if status_code in {401, 403} or "authentication" in error_name or "permission" in error_name:
        return AIInvalidCredentialError()
    if status_code == 429 or "rate" in error_name or "throttle" in error_name:
        return AIThrottledError()
    if "timeout" in error_name or "timedout" in error_name:
        return AITimeoutError()
    return AIUpstreamError()

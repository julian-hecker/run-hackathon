from fastapi import HTTPException, Request
from twilio.request_validator import RequestValidator

from voice_api.config.settings import settings


async def validate_twilio(request: Request):
    if settings.is_local:
        return
    validator = RequestValidator(settings.twilio.auth_token)
    signature = request.headers.get("X-Twilio-Signature", "")
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("host", request.url.hostname)
    path = request.url.path or ""
    query = request.url.query
    full_url = f"{proto}://{host}{path}"
    if query:
        full_url += f"?{query}"

    form = await request.form()
    is_valid = validator.validate(full_url, dict[str, str](form), signature)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

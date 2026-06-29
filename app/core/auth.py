from fastapi import Header, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if not api_key or api_key != settings.MINHA_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return api_key

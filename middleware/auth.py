"""
Authentication middleware for FastAPI
Extracts and validates JWT from Authorization header.
"""
from fastapi import Request, HTTPException
from services.auth import verify_token


async def require_auth(request: Request) -> dict:
    """
    FastAPI dependency that enforces authentication.

    Returns:
        {userId, clinicId, userRole}

    Raises:
        HTTPException 401 if token is missing or invalid.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(
            status_code=401, detail="Invalid Authorization header format"
        )

    token = parts[1]
    try:
        return verify_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

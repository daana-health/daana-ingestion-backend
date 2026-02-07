"""
Authentication service
Handles sign-in via Supabase and JWT token generation/verification.
Mirrors DaanaRx-Backend/src/services/authService.ts sign-in flow.
"""
import logging
from datetime import datetime, timezone, timedelta
import jwt
from config import settings
from utils.supabase import get_supabase_server, get_supabase_auth

logger = logging.getLogger(__name__)

JWT_EXPIRY_HOURS = 2


def sign_in(email: str, password: str) -> dict:
    """
    Authenticate user via Supabase, fetch user/clinic records, issue JWT.

    Returns:
        {token, user, clinic}
    """
    if not email or not password:
        raise ValueError("Email and password are required")

    normalized_email = email.strip().lower()
    logger.info(f"Attempting sign in for email: {normalized_email}")

    # Authenticate with Supabase Auth (anon key client)
    supabase_auth = get_supabase_auth()
    auth_response = supabase_auth.auth.sign_in_with_password(
        {"email": normalized_email, "password": password}
    )

    if not auth_response.user:
        raise ValueError("Sign in failed: Invalid credentials")

    user_id = auth_response.user.id
    logger.info(f"Authentication successful for user ID: {user_id}")

    # Fetch user record from users table
    supabase_server = get_supabase_server()
    user_result = (
        supabase_server.table("users")
        .select("*")
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not user_result.data:
        raise ValueError("User record not found")

    user = user_result.data
    effective_clinic_id = user.get("active_clinic_id") or user.get("clinic_id")

    # Fetch clinic record
    clinic_result = (
        supabase_server.table("clinics")
        .select("*")
        .eq("clinic_id", effective_clinic_id)
        .single()
        .execute()
    )

    if not clinic_result.data:
        raise ValueError("Clinic not found")

    clinic = clinic_result.data

    # Generate JWT token (same payload shape as DaanaRx backend)
    token = _generate_token(
        user_id=user["user_id"],
        clinic_id=effective_clinic_id,
        user_role=user["user_role"],
    )

    return {
        "token": token,
        "user": {
            "userId": user["user_id"],
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "clinicId": user.get("clinic_id", ""),
            "activeClinicId": effective_clinic_id,
            "userRole": user.get("user_role", ""),
        },
        "clinic": {
            "clinicId": clinic["clinic_id"],
            "name": clinic.get("name", ""),
            "primaryColor": clinic.get("primary_color"),
            "secondaryColor": clinic.get("secondary_color"),
            "logoUrl": clinic.get("logo_url"),
        },
    }


def verify_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Returns:
        {userId, clinicId, userRole}
    """
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET is not configured")

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return {
            "userId": payload["userId"],
            "clinicId": payload["clinicId"],
            "userRole": payload["userRole"],
        }
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


def _generate_token(user_id: str, clinic_id: str, user_role: str) -> str:
    """Generate a JWT token with 2-hour expiry (matches DaanaRx backend)"""
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET is not configured")

    now = datetime.now(timezone.utc)
    payload = {
        "userId": user_id,
        "clinicId": clinic_id,
        "userRole": user_role,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

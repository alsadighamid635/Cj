"""
Authentication API — per-user accounts with private, isolated data.

Endpoints:
  POST /api/auth/signup — create a new account
  POST /api/auth/login  — exchange credentials for a JWT
  GET  /api/auth/me     — return the currently authenticated user

Design:
  - Passwords are hashed with bcrypt (never stored or logged in plain text).
  - Sessions are stateless JWTs signed with SESSION_SECRET, sent as
    `Authorization: Bearer <token>` and verified on every protected request.
  - `require_user` is the FastAPI dependency other routers use to resolve
    the caller's user id and reject unauthenticated/invalid requests.
"""

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field, field_validator

import config
from utils.logger import get_logger

logger = get_logger()

router = APIRouter(prefix="/api/auth", tags=["auth"])

_db = None
_bearer = HTTPBearer(auto_error=False)

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]+$")


def init(db) -> None:
    global _db
    _db = db


# ── Password hashing ────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# ── JWT helpers ───────────────────────────────────────────────────────────────

def _create_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(hours=config.JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def _decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token.")
    return payload["sub"]


def require_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
) -> str:
    """FastAPI dependency: returns the authenticated user's id or raises 401."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return _decode_token(credentials.credentials)


# ── Request/response models ──────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    username: str = Field(..., min_length=config.MIN_USERNAME_LEN, max_length=config.MAX_USERNAME_LEN)
    email:    EmailStr
    password: str = Field(..., min_length=config.MIN_PASSWORD_LEN, max_length=128)

    @field_validator("username")
    @classmethod
    def _valid_username(cls, v: str) -> str:
        v = v.strip()
        if not _USERNAME_RE.match(v):
            raise ValueError("Username may only contain letters, numbers, and underscores.")
        return v


class LoginRequest(BaseModel):
    identifier: str = Field(..., min_length=1, max_length=255)  # username or email
    password:   str = Field(..., min_length=1, max_length=128)


class AuthResponse(BaseModel):
    token:    str
    user_id:  str
    username: str
    email:    str


class MeResponse(BaseModel):
    user_id:  str
    username: str
    email:    str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=AuthResponse)
async def signup(body: SignupRequest):
    if _db.get_user_by_username(body.username):
        raise HTTPException(status_code=409, detail="This username is already taken.")
    if _db.get_user_by_email(body.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user_id = str(uuid.uuid4())
    _db.create_user(user_id, body.username, body.email.lower(), _hash_password(body.password))
    logger.info("New account created: user_id=%s username=%s", user_id[:8], body.username)

    token = _create_token(user_id)
    return AuthResponse(token=token, user_id=user_id, username=body.username, email=body.email.lower())


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    identifier = body.identifier.strip()
    user = _db.get_user_by_email(identifier) or _db.get_user_by_username(identifier)

    if not user or not _verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username/email or password.")

    token = _create_token(user["id"])
    return AuthResponse(token=token, user_id=user["id"], username=user["username"], email=user["email"])


@router.get("/me", response_model=MeResponse)
async def me(user_id: Annotated[str, Depends(require_user)]):
    user = _db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Account no longer exists.")
    return MeResponse(user_id=user["id"], username=user["username"], email=user["email"])

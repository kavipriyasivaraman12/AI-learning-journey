"""
Authentication Router.

Handles user registration, login, token issuance, and current-user lookup.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.schemas.user_schema import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student account",
)
def register_user(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Registers a new student:
    1. Validates input format (Email and password length).
    2. Checks for existing account with the same email.
    3. Hashes the password using bcrypt.
    4. Persists the new user in PostgreSQL.
    """
    normalized_email = request.email.lower().strip()

    # Check for existing email using SQLAlchemy 2.x select
    existing_user = db.scalar(select(User).where(User.email == normalized_email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Hash the password securely
    hashed_pwd = hash_password(request.password)

    # Create new user record
    new_user = User(
        email=normalized_email,
        hashed_password=hashed_pwd,
        full_name=request.full_name.strip(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and obtain a JWT access token",
)
def login_user(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticates a student:
    1. Looks up the user by email.
    2. Verifies the password hash using bcrypt.
    3. Generates a signed JWT access token.
    """
    normalized_email = request.email.lower().strip()

    user = db.scalar(select(User).where(User.email == normalized_email))
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    # Issue JWT access token
    access_token = create_access_token(data={"sub": user.id, "email": user.email})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get authenticated student profile",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the currently authenticated user's profile information.
    Protected endpoint: Requires a valid Bearer JWT in the Authorization header.
    """
    return current_user

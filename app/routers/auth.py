from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import EmailAlreadyRegistered
from app.models import User
from app.repository import create_user, get_user_by_email
from app.schemas.user import Token, UserCreate, UserRead, normalize_email
from app.security import (
    DUMMY_HASHED_PASSWORD,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

CREDENTIALS_ERROR_DETAIL = "Could not validate credentials."
DbDep = Annotated[Session, Depends(get_db)]
Oauth2Dep = Annotated[OAuth2PasswordRequestForm, Depends()]

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Creates a new user",
    description="Creates a new user, Email must be valid.",
)
def register_user(user: UserCreate, session: DbDep) -> User:
    hashed_password = hash_password(user.password)
    try:
        new_user = create_user(session, user.email, hashed_password)
    except EmailAlreadyRegistered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already exists."
        ) from None
    session.commit()
    return new_user


@router.post("/token", response_model=Token)
def login(form_data: Oauth2Dep, session: DbDep) -> Token:
    clean_email = normalize_email(form_data.username)
    user = get_user_by_email(session, clean_email)
    hashed_password = user.hashed_password if user else DUMMY_HASHED_PASSWORD
    is_password_ok = verify_password(form_data.password, hashed_password)

    if user is None or not is_password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=CREDENTIALS_ERROR_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import EmailAlreadyRegistered
from app.models import User
from app.repository import create_user, get_user_by_email
from app.schemas.user import UserCreate, UserRead, normalize_email, Token
from app.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

DbDep = Annotated[Session, Depends(get_db)]
Oauth2Dep = Annotated[OAuth2PasswordRequestForm, Depends()]
CurrentUserDep = Annotated[User, Depends(get_current_user)]

router = APIRouter()


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
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Username or Password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.get("/users/me", response_model=UserRead)
def read_me(current_user: CurrentUserDep):
    return current_user

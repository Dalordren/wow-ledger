from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import EmailAlreadyRegistered
from app.models import User
from app.repository import create_user
from app.schemas.user import UserCreate, UserRead
from app.security import hash_password

DbDep = Annotated[Session, Depends(get_db)]

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

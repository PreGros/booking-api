from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import CurrentUser
from app.db import SessionDep
from app.ratelimit import rate_limit
from app.schemas import Token, UserCreate, UserRead
from app.security import create_access_token
from app.services import users as user_service

router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(rate_limit)])


@router.post("/register", response_model=UserRead, status_code=201)
async def register(data: UserCreate, session: SessionDep):
    return await user_service.create_user(session, data.email, data.password)


@router.post("/login", response_model=Token)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep
) -> Token:
    user = await user_service.authenticate(session, form.username, form.password)
    return Token(access_token=create_access_token(user.id, user.role))


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser):
    return user

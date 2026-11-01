import asyncio

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import EmailAlreadyRegistered, InvalidCredentials
from app.models import User
from app.security import hash_password, verify_password

# Verified against when the email is unknown, so both failures take equally long
DUMMY_HASH = hash_password("dummy-password")


async def create_user(session: AsyncSession, email: str, password: str) -> User:
    hashed = await asyncio.to_thread(hash_password, password)
    user = User(email=email.lower(), hashed_password=hashed)
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise EmailAlreadyRegistered from exc
    return user


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    user = await session.scalar(select(User).where(User.email == email.lower()))
    hashed = user.hashed_password if user else DUMMY_HASH
    valid = await asyncio.to_thread(verify_password, password, hashed)
    if user is None or not valid:
        raise InvalidCredentials
    return user

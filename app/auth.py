from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.db import SessionDep
from app.errors import InsufficientPermissions, InvalidToken
from app.models import Role, User
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep
) -> User:
    try:
        payload = decode_access_token(token)
    except jwt.InvalidTokenError as exc:
        raise InvalidToken from exc
    user = await session.get(User, int(payload["sub"]))
    if user is None:
        raise InvalidToken
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: Role):
    async def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise InsufficientPermissions
        return user

    return checker

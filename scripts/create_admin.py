import asyncio
import getpass
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings
from app.models import Role, User
from app.security import hash_password


async def main(email: str, password: str) -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine) as session:
        user = await session.scalar(select(User).where(User.email == email.lower()))
        if user is None:
            session.add(
                User(email=email.lower(), hashed_password=hash_password(password), role=Role.ADMIN)
            )
        else:
            user.role = Role.ADMIN  # existing user: password is ignored
        await session.commit()
    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python -m scripts.create_admin EMAIL")
    asyncio.run(main(sys.argv[1], getpass.getpass("Password: ")))
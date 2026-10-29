from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from owlin.core.db import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

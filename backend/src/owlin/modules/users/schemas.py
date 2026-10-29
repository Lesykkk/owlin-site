from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MeResponse(BaseModel):
    id: UUID
    username: str
    avatar_url: str | None
    discord_id: str | None
    created_at: datetime
    is_admin: bool

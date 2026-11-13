from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
import strawberry


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@strawberry.type
@dataclass
class User:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    password_hash: strawberry.Private[str] = ""
    email_verified: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

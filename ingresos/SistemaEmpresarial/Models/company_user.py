from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Optional
import strawberry
from .company import Company
from .user import User


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@strawberry.type
@dataclass
class CompanyUser:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    user_id: str = ""
    is_admin: bool = False
    is_active: bool = True
    joined_at: datetime = field(default_factory=_utc_now)
    company: Optional[Company] = None
    user: Optional[User] = None

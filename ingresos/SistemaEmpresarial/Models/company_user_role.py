from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Optional
import strawberry
from .company_user import CompanyUser
from .role import Role


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Une la membresía (CompanyUser) con su rol. Solo una pareja activa por membresía.
@strawberry.type
@dataclass
class CompanyUserRole:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_user_id: str = ""
    role_id: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=_utc_now)
    company_user: Optional[CompanyUser] = None
    role: Optional[Role] = None

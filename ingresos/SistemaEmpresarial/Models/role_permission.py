from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Optional
import strawberry
from .role import Role
from .permission import Permission


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Tabla puente Role N ── N Permission
@strawberry.type
@dataclass
class RolePermission:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role_id: str = ""
    permission_id: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=_utc_now)
    role: Optional[Role] = None
    permission: Optional[Permission] = None

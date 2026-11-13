from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Optional
import strawberry


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Catálogo compartido de roles (puestos). Se desactivan, no se borran.
@strawberry.type
@dataclass
class Role:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    code: str = ""
    name: str = ""
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=_utc_now)

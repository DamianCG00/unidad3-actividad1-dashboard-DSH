from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Optional
import strawberry


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@strawberry.type
@dataclass
class Company:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

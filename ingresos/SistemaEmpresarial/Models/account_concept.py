from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Optional
import strawberry
from .account import Account
from .concept import Concept


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@strawberry.type
@dataclass
class AccountConcept:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str = ""
    concept_id: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=_utc_now)
    account: Optional[Account] = None
    concept: Optional[Concept] = None

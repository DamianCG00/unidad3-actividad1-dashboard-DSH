from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Optional
import strawberry
from .company import Company


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@strawberry.enum
class ConceptType(Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


@strawberry.type
@dataclass
class Concept:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    concept_type: ConceptType = ConceptType.INCOME
    name: str = ""
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    company: Optional[Company] = None

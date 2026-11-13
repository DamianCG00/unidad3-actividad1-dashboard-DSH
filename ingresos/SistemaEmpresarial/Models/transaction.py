from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
import uuid
from typing import Optional, NewType
import strawberry
from .account import Account
from .concept import Concept
from .user import User


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


DecimalScalar = strawberry.scalar(
    NewType("DecimalScalar", Decimal),
    name="Decimal",
    serialize=lambda v: float(v) if v is not None else 0.0,
    parse_value=lambda v: Decimal(str(v)),
)


@strawberry.enum
class TransactionType(Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


@strawberry.type
@dataclass
class Transaction:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str = ""
    concept_id: str = ""
    transaction_type: TransactionType = TransactionType.INCOME
    amount: DecimalScalar = field(default_factory=lambda: DecimalScalar(Decimal("0.00")))
    transaction_date: datetime = field(default_factory=_utc_now)
    captured_at: datetime = field(default_factory=_utc_now)
    captured_by: str = ""
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    account: Optional[Account] = None
    concept: Optional[Concept] = None
    captured_by_user: Optional[User] = None

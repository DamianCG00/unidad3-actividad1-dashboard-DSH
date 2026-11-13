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
class AccountType(Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
    CASH = "CASH"
    SAVINGS = "SAVINGS"
    INVESTMENT = "INVESTMENT"
    WALLET = "WALLET"
    OTHER = "OTHER"


@strawberry.type
@dataclass
class Account:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    account_type: AccountType = AccountType.DEBIT
    name: str = ""
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    clabe: Optional[str] = None
    card_last_digits: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    company: Optional[Company] = None

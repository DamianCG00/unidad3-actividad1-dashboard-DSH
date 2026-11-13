from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List
import strawberry
from Balances import ResultadoCuenta


@strawberry.type(name="AccountBalance")
@dataclass
class AccountBalanceResult:
    """
    Los importes se devuelven como cadenas con dos decimales ("1800.00"),
    para no perder centavos en el cliente.
    """
    account_id: strawberry.ID = strawberry.ID("")
    account_name: str = ""
    is_active: bool = True
    opening_balance: str = "0.00"
    total_income: str = "0.00"
    total_expense: str = "0.00"
    profit: str = "0.00"
    closing_balance: str = "0.00"
    is_in_red: bool = False

    @staticmethod
    def fmt(valor: Decimal) -> str:
        return f"{Decimal(str(valor)):.2f}"

    @classmethod
    def from_resultado(cls, r: ResultadoCuenta) -> "AccountBalanceResult":
        return cls(
            account_id=strawberry.ID(r.account_id),
            account_name=r.account_name,
            is_active=r.is_active,
            opening_balance=cls.fmt(r.opening_balance),
            total_income=cls.fmt(r.total_income),
            total_expense=cls.fmt(r.total_expense),
            profit=cls.fmt(r.profit),
            closing_balance=cls.fmt(r.closing_balance),
            is_in_red=r.is_in_red,
        )


@strawberry.type(name="GeneralBalance")
@dataclass
class GeneralBalanceResult:
    company_id: strawberry.ID = strawberry.ID("")
    currency: str = "MXN"
    from_date: date = field(default_factory=date.today)
    to_date: date = field(default_factory=date.today)
    opening_balance: str = "0.00"
    total_income: str = "0.00"
    total_expense: str = "0.00"
    profit: str = "0.00"
    closing_balance: str = "0.00"
    is_in_red: bool = False
    accounts_in_red: int = 0
    accounts: List[AccountBalanceResult] = field(default_factory=list)

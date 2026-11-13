from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, List, Optional, Union
from Models import Account


def _to_dec(val: Union[Decimal, int, float, str]) -> Decimal:
    if isinstance(val, Decimal):
        return val
    if isinstance(val, float):
        return Decimal(f"{val:.2f}")
    return Decimal(str(val))


@dataclass(frozen=True)
class SaldosCuenta:
    """Saldos agregados de una cuenta para el período (calculados en la base)."""
    apertura: Decimal
    ingresos: Decimal
    egresos: Decimal

    def __init__(
        self,
        apertura: Union[Decimal, int, float, str] = Decimal("0.00"),
        ingresos: Union[Decimal, int, float, str] = Decimal("0.00"),
        egresos: Union[Decimal, int, float, str] = Decimal("0.00"),
    ):
        object.__setattr__(self, "apertura", _to_dec(apertura))
        object.__setattr__(self, "ingresos", _to_dec(ingresos))
        object.__setattr__(self, "egresos", _to_dec(egresos))


@dataclass(frozen=True)
class ResultadoCuenta:
    account_id: str
    account_name: str
    is_active: bool
    opening_balance: Decimal
    total_income: Decimal
    total_expense: Decimal
    profit: Decimal
    closing_balance: Decimal
    is_in_red: bool


@dataclass(frozen=True)
class ResultadoGeneral:
    opening_balance: Decimal
    total_income: Decimal
    total_expense: Decimal
    profit: Decimal
    closing_balance: Decimal
    is_in_red: bool
    accounts_in_red: int
    accounts: List[ResultadoCuenta]


class BalanceCalculator:
    """Lógica pura: no toca la base. Así se puede probar con datos escritos a mano."""

    @staticmethod
    def calcular_cuenta(cuenta: Account, saldos: Optional[SaldosCuenta] = None) -> ResultadoCuenta:
        s = saldos if saldos is not None else SaldosCuenta(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))

        profit = s.ingresos - s.egresos
        cierre = s.apertura + profit

        return ResultadoCuenta(
            account_id=cuenta.id,
            account_name=cuenta.name,
            is_active=cuenta.is_active,
            opening_balance=s.apertura,
            total_income=s.ingresos,
            total_expense=s.egresos,
            profit=profit,
            closing_balance=cierre,
            is_in_red=cierre < Decimal("0.00"),
        )

    @staticmethod
    def calcular_general(
        cuentas: Iterable[Account],
        saldos: Dict[str, SaldosCuenta],
    ) -> ResultadoGeneral:
        cuentas_ordenadas = sorted(cuentas, key=lambda c: c.id)
        detalle = [
            BalanceCalculator.calcular_cuenta(c, saldos.get(c.id))
            for c in cuentas_ordenadas
        ]

        apertura = sum((c.opening_balance for c in detalle), Decimal("0.00"))
        ingresos = sum((c.total_income for c in detalle), Decimal("0.00"))
        egresos = sum((c.total_expense for c in detalle), Decimal("0.00"))
        profit = ingresos - egresos
        cierre = apertura + profit

        # El total puede ser positivo mientras una cuenta está en rojo: se cuentan por separado.
        en_rojo = sum(1 for c in detalle if c.closing_balance < Decimal("0.00"))

        return ResultadoGeneral(
            opening_balance=apertura,
            total_income=ingresos,
            total_expense=egresos,
            profit=profit,
            closing_balance=cierre,
            is_in_red=cierre < Decimal("0.00"),
            accounts_in_red=en_rojo,
            accounts=detalle,
        )

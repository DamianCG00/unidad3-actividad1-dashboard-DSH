from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional
from Data import AppDbContext
from Models import TransactionType
from .balance_calculator import SaldosCuenta


class BalanceService:
    """
    Una sola consulta agrupada por cuenta. Solo movimientos activos de la empresa,
    con fecha de operación anterior a fin. Las fechas se comparan con TransactionDate,
    nunca con CapturedAt.
    """

    @staticmethod
    def cargar_saldos(
        db: AppDbContext,
        company_id: str,
        inicio: datetime,
        fin: datetime,
        account_id: Optional[str] = None,
    ) -> Dict[str, SaldosCuenta]:
        movimientos = db.get_transactions_for_company(
            company_id=company_id,
            account_id=account_id,
            include_relations=False,
        )

        por_cuenta: Dict[str, Dict[str, Decimal]] = {}

        for t in movimientos:
            if not t.is_active:
                continue
            if t.transaction_date >= fin:
                continue

            acc_id = t.account_id
            if acc_id not in por_cuenta:
                por_cuenta[acc_id] = {
                    "apertura": Decimal("0.00"),
                    "ingresos": Decimal("0.00"),
                    "egresos": Decimal("0.00"),
                }

            monto = Decimal(str(t.amount))
            if t.transaction_date < inicio:
                if t.transaction_type == TransactionType.INCOME:
                    por_cuenta[acc_id]["apertura"] += monto
                else:
                    por_cuenta[acc_id]["apertura"] -= monto
            else:
                if t.transaction_type == TransactionType.INCOME:
                    por_cuenta[acc_id]["ingresos"] += monto
                elif t.transaction_type == TransactionType.EXPENSE:
                    por_cuenta[acc_id]["egresos"] += monto

        return {
            acc_id: SaldosCuenta(vals["apertura"], vals["ingresos"], vals["egresos"])
            for acc_id, vals in por_cuenta.items()
        }

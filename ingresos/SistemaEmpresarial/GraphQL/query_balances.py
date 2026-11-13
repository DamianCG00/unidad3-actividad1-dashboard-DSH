from datetime import date
from typing import Optional
import strawberry
from strawberry.types import Info
from Acceso import AccessControl, Perm
from Balances import BalanceCalculator, BalancePeriodo, BalanceService, GraphQLException
from Data import AppDbContext
from .balance_types import AccountBalanceResult, GeneralBalanceResult


def _db_from_info(info: Optional[Info], context: Optional[AppDbContext] = None) -> AppDbContext:
    if context is not None:
        return context
    if info is not None and isinstance(info.context, dict) and "db" in info.context:
        return info.context["db"]
    raise RuntimeError("No se encontró AppDbContext en el contexto de la consulta")


@strawberry.type
class QueryBalances:
    @strawberry.field(name="accountBalance")
    def get_account_balance(
        self,
        info: Info,
        account_id: strawberry.ID,
        from_date: date,
        to_date: date,
        actor_company_user_id: str,
    ) -> AccountBalanceResult:
        """
        Balance de una cuenta. Exige accounts.read y transactions.read.
        La empresa sale de la membresía; la cuenta ajena o inexistente responde igual.
        """
        context = _db_from_info(info)
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.ACCOUNTS_READ)
        AccessControl.exigir_permiso(context, actor_company_user_id, Perm.TRANSACTIONS_READ)

        inicio, fin = BalancePeriodo.calcular(from_date, to_date)

        acc_id_str = str(account_id)
        cuenta = context.get_account_by_id(acc_id_str)
        if cuenta is None or cuenta.company_id != actor.company_id:
            raise GraphQLException("Cuenta no disponible")

        saldos = BalanceService.cargar_saldos(context, actor.company_id, inicio, fin, acc_id_str)
        saldos_cuenta = saldos.get(acc_id_str)

        return AccountBalanceResult.from_resultado(
            BalanceCalculator.calcular_cuenta(cuenta, saldos_cuenta)
        )

    @strawberry.field(name="miGeneralBalance")
    def get_mi_general_balance(
        self,
        info: Info,
        from_date: date,
        to_date: date,
    ) -> GeneralBalanceResult:
        """
        Igual que generalBalance, pero la membresía sale del Bearer token (claim companyUserId).
        """
        claims = info.context.get("claims") if isinstance(info.context, dict) else None
        company_user_id = claims.get("companyUserId") if isinstance(claims, dict) else None
        if not company_user_id:
            raise GraphQLException("Sesión no válida")

        return QueryBalances.get_general_balance(
            self,
            info=info,
            from_date=from_date,
            to_date=to_date,
            actor_company_user_id=str(company_user_id),
        )

    @strawberry.field(name="generalBalance")
    def get_general_balance(
        self,
        info: Info,
        from_date: date,
        to_date: date,
        actor_company_user_id: str,
    ) -> GeneralBalanceResult:
        """
        Resumen de la empresa de la membresía. Usa el mismo conjunto de datos que el detalle.
        """
        context = _db_from_info(info)
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.ACCOUNTS_READ)
        AccessControl.exigir_permiso(context, actor_company_user_id, Perm.TRANSACTIONS_READ)

        inicio, fin = BalancePeriodo.calcular(from_date, to_date)

        cuentas = context.get_accounts_by_company(actor.company_id)
        saldos = BalanceService.cargar_saldos(context, actor.company_id, inicio, fin)

        r = BalanceCalculator.calcular_general(cuentas, saldos)

        return GeneralBalanceResult(
            company_id=strawberry.ID(actor.company_id),
            currency="MXN",
            from_date=from_date,
            to_date=to_date,
            opening_balance=AccountBalanceResult.fmt(r.opening_balance),
            total_income=AccountBalanceResult.fmt(r.total_income),
            total_expense=AccountBalanceResult.fmt(r.total_expense),
            profit=AccountBalanceResult.fmt(r.profit),
            closing_balance=AccountBalanceResult.fmt(r.closing_balance),
            is_in_red=r.is_in_red,
            accounts_in_red=r.accounts_in_red,
            accounts=[AccountBalanceResult.from_resultado(a) for a in r.accounts],
        )

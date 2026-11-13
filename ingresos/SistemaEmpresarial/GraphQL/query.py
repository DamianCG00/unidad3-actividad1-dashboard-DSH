from typing import List, Optional
import strawberry
from strawberry.types import Info
from Acceso import AccessControl, Perm
from Balances import GraphQLException
from Models import (
    Account,
    AccountConcept,
    AccountType,
    Company,
    CompanyUser,
    CompanyUserRole,
    Concept,
    ConceptType,
    Permission,
    Role,
    RolePermission,
    Transaction,
    TransactionType,
)
from .query_balances import QueryBalances, _db_from_info
from .query_role_permissions import QueryRolePermissions


@strawberry.type
class Query(QueryBalances, QueryRolePermissions):
    @strawberry.field(name="companies")
    def get_companies(
        self,
        info: Info,
        active_only: Optional[bool] = None,
    ) -> List[Company]:
        context = _db_from_info(info)
        return context.get_companies(active_only=active_only)

    @strawberry.field(name="company")
    def get_company(
        self,
        info: Info,
        id: str,
    ) -> Optional[Company]:
        context = _db_from_info(info)
        return context.get_company_by_id(id)

    @strawberry.field(name="accounts")
    def get_accounts(
        self,
        info: Info,
        company_id: str,
        actor_company_user_id: str,
        account_type: Optional[AccountType] = None,
        active_only: Optional[bool] = None,
    ) -> List[Account]:
        context = _db_from_info(info)
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.ACCOUNTS_READ)
        AccessControl.exigir_misma_empresa(actor, company_id)

        return context.get_accounts_by_company(
            company_id=company_id,
            account_type=account_type,
            active_only=active_only,
            include_company=True,
        )

    @strawberry.field(name="concepts")
    def get_concepts(
        self,
        info: Info,
        company_id: str,
        actor_company_user_id: str,
        concept_type: Optional[ConceptType] = None,
        active_only: Optional[bool] = None,
    ) -> List[Concept]:
        context = _db_from_info(info)
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.CONCEPTS_READ)
        AccessControl.exigir_misma_empresa(actor, company_id)

        return context.get_concepts_by_company(
            company_id=company_id,
            concept_type=concept_type,
            active_only=active_only,
        )

    @strawberry.field(name="accountConcepts")
    def get_account_concepts(
        self,
        info: Info,
        account_id: str,
        actor_company_user_id: str,
    ) -> List[AccountConcept]:
        context = _db_from_info(info)
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.CONCEPTS_READ)

        account = context.get_account_by_id(account_id)
        if account is None:
            raise GraphQLException("La cuenta no existe")

        AccessControl.exigir_misma_empresa(actor, account.company_id)

        return context.get_account_concepts_by_account(account_id)

    @strawberry.field(name="transactions")
    def get_transactions(
        self,
        info: Info,
        actor_company_user_id: str,
        account_id: Optional[str] = None,
        transaction_type: Optional[TransactionType] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Transaction]:
        """Los movimientos que se devuelven son los de la empresa de la membresía que consulta."""
        context = _db_from_info(info)
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.TRANSACTIONS_READ)

        return context.get_transactions_for_company(
            company_id=actor.company_id,
            account_id=account_id,
            transaction_type=transaction_type,
            limit=limit,
            offset=offset,
            include_relations=True,
        )

    # ---------- Roles y permisos ----------

    @strawberry.field(name="roles")
    def get_roles(
        self,
        info: Info,
        actor_company_user_id: str,
        active_only: Optional[bool] = None,
    ) -> List[Role]:
        context = _db_from_info(info)
        AccessControl.exigir_permiso(context, actor_company_user_id, Perm.ROLES_READ)
        return context.get_roles(active_only=active_only)

    @strawberry.field(name="role")
    def get_role(
        self,
        info: Info,
        id: str,
        actor_company_user_id: str,
    ) -> Optional[Role]:
        context = _db_from_info(info)
        AccessControl.exigir_permiso(context, actor_company_user_id, Perm.ROLES_READ)
        return context.get_role_by_id(id)

    @strawberry.field(name="permissions")
    def get_permissions(
        self,
        info: Info,
        actor_company_user_id: str,
        active_only: Optional[bool] = None,
    ) -> List[Permission]:
        context = _db_from_info(info)
        AccessControl.exigir_permiso(context, actor_company_user_id, Perm.ROLES_READ)
        return context.get_permissions(active_only=active_only)

    @strawberry.field(name="rolePermissions")
    def get_role_permissions(
        self,
        info: Info,
        role_id: str,
        actor_company_user_id: str,
    ) -> List[RolePermission]:
        """Permisos activos de un rol."""
        context = _db_from_info(info)
        AccessControl.exigir_permiso(context, actor_company_user_id, Perm.ROLES_READ)
        return context.get_role_permissions_by_role(role_id, active_only=True)

    @strawberry.field(name="companyUsers")
    def get_company_users(
        self,
        info: Info,
        company_id: str,
        actor_company_user_id: str,
    ) -> List[CompanyUser]:
        """Membresías de la empresa del actor (para conocer los companyUserId)."""
        context = _db_from_info(info)
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.COMPANY_USERS_READ)
        AccessControl.exigir_misma_empresa(actor, company_id)
        return context.get_company_users(company_id)

    @strawberry.field(name="companyUserRoles")
    def get_company_user_roles(
        self,
        info: Info,
        company_id: str,
        actor_company_user_id: str,
    ) -> List[CompanyUserRole]:
        """Rol activo de cada membresía de la empresa del actor."""
        context = _db_from_info(info)
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.COMPANY_USERS_READ)
        AccessControl.exigir_misma_empresa(actor, company_id)
        return context.get_company_user_roles_by_company(company_id)

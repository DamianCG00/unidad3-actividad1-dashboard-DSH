from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import re
from typing import Any, Dict, Optional
import strawberry
from strawberry.types import Info
from Acceso import AccessControl, JwtService, PasswordService, Perm
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
    DecimalScalar,
    Permission,
    Role,
    RolePermission,
    Transaction,
    TransactionType,
    User,
)
from .mutation_role_permissions import MutationRolePermissions
from .query_balances import _db_from_info


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_valid_email(email: str) -> bool:
    if not email or " " in email:
        return False
    return bool(_EMAIL_RE.match(email))


# Definición de los inputs requeridos por el esquema

@strawberry.input
@dataclass
class CreateCompanyInput:
    name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


@strawberry.input
@dataclass
class UpdateCompanyInput:
    id: str
    name: Optional[str] = None
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


@strawberry.input
@dataclass
class CreateAdminInput:
    company_id: str = ""
    name: str = ""
    email: str = ""
    password: str = ""


@strawberry.input
@dataclass
class CreateUserInput:
    company_id: str
    name: str
    email: str
    password: str


@strawberry.input
@dataclass
class LoginInput:
    email: str
    password: str


@strawberry.input
@dataclass
class CreateAccountInput:
    company_id: str
    account_type: AccountType
    name: str
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    clabe: Optional[str] = None
    card_last_digits: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None


@strawberry.input
@dataclass
class CreateConceptInput:
    company_id: str
    concept_type: ConceptType
    name: str
    short_description: Optional[str] = None
    long_description: Optional[str] = None


@strawberry.input
@dataclass
class AssignConceptToAccountInput:
    account_id: str
    concept_id: str


@strawberry.input
@dataclass
class CreateTransactionInput:
    account_id: str
    concept_id: str
    transaction_type: TransactionType
    amount: DecimalScalar
    transaction_date: Optional[datetime] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None


@strawberry.input
@dataclass
class CreateRoleInput:
    code: str
    name: str
    description: Optional[str] = None


@strawberry.input
@dataclass
class CreatePermissionInput:
    code: str
    name: str
    description: Optional[str] = None


@strawberry.input
@dataclass
class AssignPermissionToRoleInput:
    role_id: str
    permission_id: str


@strawberry.input
@dataclass
class AssignRoleInput:
    company_user_id: str
    role_id: str


@strawberry.type
@dataclass
class LoginResult:
    success: bool = False
    message: str = ""
    user_id: str = ""
    name: str = ""
    email: str = ""
    token: Optional[str] = None
    token_type: str = "Bearer"


@strawberry.type
class Mutation(MutationRolePermissions):
    @strawberry.mutation(name="createCompany")
    def create_company(self, info: Info, input: CreateCompanyInput) -> Company:
        context = _db_from_info(info)
        company = Company(
            name=input.name,
            legal_name=input.legal_name,
            tax_id=input.tax_id,
            email=input.email,
            phone=input.phone,
        )
        context.add_company(company)
        context.save_changes()
        return company

    @strawberry.mutation(name="updateCompany")
    def update_company(self, info: Info, input: UpdateCompanyInput) -> Company:
        context = _db_from_info(info)
        company = context.get_company_by_id(input.id)
        if company is None:
            raise GraphQLException("Empresa no encontrada")

        if input.name is not None:
            company.name = input.name
        if input.legal_name is not None:
            company.legal_name = input.legal_name
        if input.tax_id is not None:
            company.tax_id = input.tax_id
        if input.email is not None:
            company.email = input.email
        if input.phone is not None:
            company.phone = input.phone
        if input.is_active is not None:
            company.is_active = input.is_active

        company.updated_at = _utc_now()
        context.update_company(company)
        context.save_changes()
        return company

    @strawberry.mutation(name="deactivateCompany")
    def deactivate_company(self, info: Info, id: str) -> Company:
        context = _db_from_info(info)
        company = context.get_company_by_id(id)
        if company is None:
            raise GraphQLException("Empresa no encontrada")

        company.is_active = False
        company.updated_at = _utc_now()
        context.update_company(company)
        context.save_changes()
        return company

    @strawberry.mutation(name="createAdmin")
    def create_admin(self, info: Info, input: CreateAdminInput) -> User:
        context = _db_from_info(info)
        company = context.get_company_by_id(input.company_id)
        if company is None:
            raise GraphQLException("La empresa no existe")

        email = input.email.strip().lower()
        if not _is_valid_email(email):
            raise GraphQLException("El formato del correo electrónico no es válido")

        if context.get_user_by_email(email) is not None:
            raise GraphQLException("El correo electrónico ya está registrado")

        if context.has_active_admin(input.company_id):
            raise GraphQLException("La empresa ya tiene un administrador principal")

        now = _utc_now()
        user = User(
            name=input.name,
            email=email,
            password_hash=PasswordService.hash_password(input.password),
            email_verified=False,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        context.add_user(user)

        company_user = CompanyUser(
            company_id=input.company_id,
            user_id=user.id,
            is_admin=True,
            is_active=True,
            joined_at=now,
        )
        context.add_company_user(company_user)

        admin_role = context.get_role_by_code("ADMINISTRADOR")
        if admin_role is None or not admin_role.is_active:
            raise GraphQLException("El rol ADMINISTRADOR no existe")

        context.add_company_user_role(
            CompanyUserRole(
                company_user_id=company_user.id,
                role_id=admin_role.id,
                is_active=True,
            )
        )

        context.save_changes()
        return user

    @strawberry.mutation(name="createUser")
    def create_user(
        self,
        info: Info,
        input: CreateUserInput,
        actor_company_user_id: str,
    ) -> User:
        context = _db_from_info(info)
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.COMPANY_USERS_WRITE)
        AccessControl.exigir_misma_empresa(actor, input.company_id)

        company = context.get_company_by_id(input.company_id)
        if company is None:
            raise GraphQLException("La empresa no existe")

        email = input.email.strip().lower()
        if not _is_valid_email(email):
            raise GraphQLException("El formato del correo electrónico no es válido")

        if context.get_user_by_email(email) is not None:
            raise GraphQLException("El correo electrónico ya está registrado")

        now = _utc_now()
        user = User(
            name=input.name,
            email=email,
            password_hash=PasswordService.hash_password(input.password),
            email_verified=False,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        context.add_user(user)

        company_user = CompanyUser(
            company_id=input.company_id,
            user_id=user.id,
            is_admin=False,
            is_active=True,
            joined_at=now,
        )
        context.add_company_user(company_user)
        context.save_changes()
        return user

    @strawberry.mutation(name="login")
    def login(self, info: Info, input: LoginInput) -> LoginResult:
        context = _db_from_info(info)
        cfg: Dict[str, Any] = info.context.get("config", {}) if isinstance(info.context, dict) else {}

        email = input.email.strip().lower()
        user = context.get_user_by_email(email)
        if user is None:
            raise GraphQLException("Credenciales incorrectas")

        if not user.is_active:
            raise GraphQLException("El usuario está inactivo")

        if not PasswordService.verify_password(input.password, user.password_hash):
            raise GraphQLException("Credenciales incorrectas")

        membresia = context.get_active_company_user_for_user(user.id)
        if membresia is None:
            raise GraphQLException("El usuario no tiene una empresa activa")

        return LoginResult(
            success=True,
            message="Autenticación correcta",
            user_id=user.id,
            name=user.name,
            email=user.email,
            token=JwtService.generar(user, membresia.id, membresia.company_id, cfg),
            token_type="Bearer",
        )

    @strawberry.mutation(name="createAccount")
    def create_account(
        self,
        info: Info,
        input: CreateAccountInput,
        actor_company_user_id: str,
    ) -> Account:
        context = _db_from_info(info)
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.ACCOUNTS_WRITE)
        AccessControl.exigir_misma_empresa(actor, input.company_id)

        company = context.get_company_by_id(input.company_id)
        if company is None:
            raise GraphQLException("La empresa no existe")

        name = input.name.strip()
        if context.account_name_exists(input.company_id, name):
            raise GraphQLException("Ya existe una cuenta con ese nombre para esta empresa")

        account = Account(
            company_id=input.company_id,
            account_type=input.account_type,
            name=name,
            bank_name=input.bank_name,
            account_number=input.account_number,
            clabe=input.clabe,
            card_last_digits=input.card_last_digits,
            short_description=input.short_description,
            long_description=input.long_description,
            company=company,
        )
        context.add_account(account)
        context.save_changes()
        return account

    @strawberry.mutation(name="createConcept")
    def create_concept(
        self,
        info: Info,
        input: CreateConceptInput,
        actor_company_user_id: str,
    ) -> Concept:
        context = _db_from_info(info)
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.CONCEPTS_WRITE)
        AccessControl.exigir_misma_empresa(actor, input.company_id)

        company = context.get_company_by_id(input.company_id)
        if company is None:
            raise GraphQLException("La empresa no existe")

        name = input.name.strip()
        if context.concept_exists(input.company_id, input.concept_type, name):
            raise GraphQLException("Ya existe un concepto con ese nombre y tipo para esta empresa")

        concept = Concept(
            company_id=input.company_id,
            concept_type=input.concept_type,
            name=name,
            short_description=input.short_description,
            long_description=input.long_description,
            company=company,
        )
        context.add_concept(concept)
        context.save_changes()
        return concept

    @strawberry.mutation(name="assignConceptToAccount")
    def assign_concept_to_account(
        self,
        info: Info,
        input: AssignConceptToAccountInput,
        actor_company_user_id: str,
    ) -> AccountConcept:
        context = _db_from_info(info)
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.CONCEPTS_WRITE)

        account = context.get_account_by_id(input.account_id)
        if account is None:
            raise GraphQLException("La cuenta no existe")

        AccessControl.exigir_misma_empresa(actor, account.company_id)

        concept = context.get_concept_by_id(input.concept_id)
        if concept is None:
            raise GraphQLException("El concepto no existe")

        if account.company_id != concept.company_id:
            raise GraphQLException("La cuenta y el concepto deben pertenecer a la misma empresa")

        existing = context.get_account_concept(input.account_id, input.concept_id)
        if existing is not None:
            if existing.is_active:
                raise GraphQLException("El concepto ya está asignado a esta cuenta")
            existing.is_active = True
            context.update_account_concept_active(existing.id, True)
            context.save_changes()
            existing.account = account
            existing.concept = concept
            return existing

        account_concept = AccountConcept(
            account_id=input.account_id,
            concept_id=input.concept_id,
            is_active=True,
            account=account,
            concept=concept,
        )
        context.add_account_concept(account_concept)
        context.save_changes()
        return account_concept

    @strawberry.mutation(name="removeConceptFromAccount")
    def remove_concept_from_account(
        self,
        info: Info,
        account_id: str,
        concept_id: str,
        actor_company_user_id: str,
    ) -> bool:
        context = _db_from_info(info)
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.CONCEPTS_WRITE)

        account_concept = context.get_account_concept(account_id, concept_id, include_relations=True)
        if account_concept is None or account_concept.account is None:
            raise GraphQLException("La relación entre la cuenta y el concepto no existe")

        AccessControl.exigir_misma_empresa(actor, account_concept.account.company_id)

        if not account_concept.is_active:
            raise GraphQLException("La relación ya se encuentra desactivada")

        context.update_account_concept_active(account_concept.id, False)
        context.save_changes()
        return True

    @strawberry.mutation(name="createTransaction")
    def create_transaction(
        self,
        info: Info,
        input: CreateTransactionInput,
        actor_company_user_id: str,
    ) -> Transaction:
        context = _db_from_info(info)
        # 1. Exigir el permiso antes de validar o escribir cualquier cosa
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.TRANSACTIONS_WRITE)

        # 2. Validar monto
        amount = Decimal(str(input.amount))
        if amount <= Decimal("0"):
            raise GraphQLException("El monto debe ser mayor que 0")

        if amount >= Decimal("10000000000"):
            raise GraphQLException("El monto excede el máximo permitido")

        if round(amount, 2) != amount:
            raise GraphQLException("El monto admite como máximo dos decimales")

        # 3. Buscar cuenta
        account = context.get_account_by_id(input.account_id)
        if account is None:
            raise GraphQLException("La cuenta no existe")
        if not account.is_active:
            raise GraphQLException("La cuenta está inactiva")

        # 4. Buscar concepto
        concept = context.get_concept_by_id(input.concept_id)
        if concept is None:
            raise GraphQLException("El concepto no existe")
        if not concept.is_active:
            raise GraphQLException("El concepto está inactivo")

        # 5. Cuenta y concepto deben pertenecer a la misma empresa
        if account.company_id != concept.company_id:
            raise GraphQLException("La cuenta y el concepto deben pertenecer a la misma empresa")

        # 6. El concepto debe estar permitido para la cuenta
        relation = context.get_account_concept(input.account_id, input.concept_id)
        if relation is None or not relation.is_active:
            raise GraphQLException("El concepto no está permitido para la cuenta seleccionada")

        # 7. El usuario que captura es el de la membresía que actúa
        user = actor.user
        assert user is not None

        # 8. La membresía debe pertenecer a la misma empresa que la cuenta
        if actor.company_id != account.company_id:
            raise GraphQLException("El usuario no pertenece a la misma empresa que la cuenta")

        # 9. El tipo de movimiento debe coincidir con el tipo del concepto
        if input.transaction_type == TransactionType.INCOME and concept.concept_type != ConceptType.INCOME:
            raise GraphQLException("El tipo INCOME no es compatible con el concepto seleccionado")

        if input.transaction_type == TransactionType.EXPENSE and concept.concept_type != ConceptType.EXPENSE:
            raise GraphQLException("El tipo EXPENSE no es compatible con el concepto seleccionado")

        # 10. Crear movimiento
        now = _utc_now()
        tx_date = input.transaction_date if input.transaction_date is not None else now
        if tx_date.tzinfo is None:
            tx_date = tx_date.replace(tzinfo=timezone.utc)

        transaction = Transaction(
            account_id=account.id,
            concept_id=concept.id,
            transaction_type=input.transaction_type,
            amount=DecimalScalar(amount.quantize(Decimal("0.01"))),
            transaction_date=tx_date,
            captured_at=now,
            captured_by=user.id,
            short_description=input.short_description,
            long_description=input.long_description,
            is_active=True,
            created_at=now,
            updated_at=now,
            account=account,
            concept=concept,
            captured_by_user=user,
        )
        context.add_transaction(transaction)
        context.save_changes()
        return transaction

    @strawberry.mutation(name="deleteTransaction")
    def delete_transaction(
        self,
        info: Info,
        id: str,
        actor_company_user_id: str,
    ) -> Transaction:
        context = _db_from_info(info)
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.TRANSACTIONS_WRITE)

        transaction = context.get_transaction_by_id(id, include_relations=True)
        if transaction is None:
            raise GraphQLException("El movimiento no existe")

        if not transaction.is_active:
            raise GraphQLException("El movimiento ya está eliminado")

        company_id = transaction.account.company_id if transaction.account else None
        if company_id is None:
            raise GraphQLException("La cuenta del movimiento no existe")

        if actor.company_id != company_id:
            raise GraphQLException("El usuario no pertenece a la misma empresa que el movimiento")

        now = _utc_now()
        transaction.is_active = False
        transaction.updated_at = now
        context.update_transaction_active(transaction.id, False, now)
        context.save_changes()
        return transaction

    # ---------- Roles y permisos ----------

    @strawberry.mutation(name="createRole")
    def create_role(
        self,
        info: Info,
        input: CreateRoleInput,
        actor_company_user_id: str,
    ) -> Role:
        context = _db_from_info(info)
        AccessControl.exigir_permiso(context, actor_company_user_id, Perm.ROLES_WRITE)

        code = input.code.strip().upper()
        name = input.name.strip()
        if not code or not name:
            raise GraphQLException("El código y el nombre del rol son obligatorios")

        if context.get_role_by_code(code) is not None:
            raise GraphQLException("Ya existe un rol con ese código")

        role = Role(code=code, name=name, description=input.description)
        context.add_role(role)
        context.save_changes()
        return role

    @strawberry.mutation(name="deactivateRole")
    def deactivate_role(
        self,
        info: Info,
        id: str,
        actor_company_user_id: str,
    ) -> Role:
        context = _db_from_info(info)
        AccessControl.exigir_permiso(context, actor_company_user_id, Perm.ROLES_WRITE)

        role = context.get_role_by_id(id)
        if role is None:
            raise GraphQLException("El rol no existe")

        if role.code == "ADMINISTRADOR":
            raise GraphQLException("El rol ADMINISTRADOR no se puede desactivar")

        if not role.is_active:
            raise GraphQLException("El rol ya está desactivado")

        role.is_active = False
        context.update_role_active(role.id, False)
        context.save_changes()
        return role

    @strawberry.mutation(name="createPermission")
    def create_permission(
        self,
        info: Info,
        input: CreatePermissionInput,
        actor_company_user_id: str,
    ) -> Permission:
        context = _db_from_info(info)
        AccessControl.exigir_permiso(context, actor_company_user_id, Perm.ROLES_WRITE)

        code = input.code.strip().lower()
        name = input.name.strip()
        if not code or not name:
            raise GraphQLException("El código y el nombre del permiso son obligatorios")

        if context.get_permission_by_code(code) is not None:
            raise GraphQLException("Ya existe un permiso con ese código")

        permission = Permission(code=code, name=name, description=input.description)
        context.add_permission(permission)
        context.save_changes()
        return permission

    @strawberry.mutation(name="assignPermissionToRole")
    def assign_permission_to_role(
        self,
        info: Info,
        input: AssignPermissionToRoleInput,
        actor_company_user_id: str,
    ) -> RolePermission:
        context = _db_from_info(info)
        AccessControl.exigir_permiso(context, actor_company_user_id, Perm.ROLES_WRITE)

        role = context.get_role_by_id(input.role_id)
        if role is None or not role.is_active:
            raise GraphQLException("El rol no existe o está inactivo")

        permission = context.get_permission_by_id(input.permission_id)
        if permission is None or not permission.is_active:
            raise GraphQLException("El permiso no existe o está inactivo")

        existing = context.get_role_permission(input.role_id, input.permission_id)
        if existing is not None:
            if existing.is_active:
                raise GraphQLException("El rol ya tiene asignado ese permiso")
            existing.is_active = True
            context.update_role_permission_active(existing.id, True)
            context.save_changes()
            existing.role = role
            existing.permission = permission
            return existing

        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission.id,
            is_active=True,
            role=role,
            permission=permission,
        )
        context.add_role_permission(role_permission)
        context.save_changes()
        return role_permission

    @strawberry.mutation(name="removePermissionFromRole")
    def remove_permission_from_role(
        self,
        info: Info,
        role_id: str,
        permission_id: str,
        actor_company_user_id: str,
    ) -> bool:
        context = _db_from_info(info)
        AccessControl.exigir_permiso(context, actor_company_user_id, Perm.ROLES_WRITE)

        role_permission = context.get_role_permission(role_id, permission_id)
        if role_permission is None:
            raise GraphQLException("El rol no tiene asignado ese permiso")

        if not role_permission.is_active:
            raise GraphQLException("El permiso ya está desactivado para ese rol")

        context.update_role_permission_active(role_permission.id, False)
        context.save_changes()
        return True

    @strawberry.mutation(name="assignRole")
    def assign_role(
        self,
        info: Info,
        input: AssignRoleInput,
        actor_company_user_id: str,
    ) -> CompanyUserRole:
        context = _db_from_info(info)
        actor = AccessControl.exigir_permiso(context, actor_company_user_id, Perm.ROLES_WRITE)

        target = context.get_company_user_by_id(input.company_user_id, include_user=True)
        if target is None or not target.is_active:
            raise GraphQLException("La membresía no existe o está inactiva")

        AccessControl.exigir_misma_empresa(actor, target.company_id)

        role = context.get_role_by_id(input.role_id)
        if role is None or not role.is_active:
            raise GraphQLException("El rol no existe o está inactivo")

        if role.code == "ADMINISTRADOR" and not target.is_admin:
            raise GraphQLException("El rol ADMINISTRADOR es solo del administrador principal")

        if target.is_admin and role.code != "ADMINISTRADOR":
            raise GraphQLException("El administrador principal conserva el rol ADMINISTRADOR")

        actuales = context.get_active_company_user_roles(target.id)
        mismo = next((cur for cur in actuales if cur.role_id == role.id), None)
        if mismo is not None and len(actuales) == 1:
            mismo.company_user = target
            mismo.role = role
            return mismo

        tx = context.begin_transaction()
        tx.__enter__()
        try:
            for anterior in actuales:
                anterior.is_active = False
                context.update_company_user_role_active(anterior.id, False)

            context.save_changes()

            nuevo = CompanyUserRole(
                company_user_id=target.id,
                role_id=role.id,
                is_active=True,
                company_user=target,
                role=role,
            )
            context.add_company_user_role(nuevo)
            context.save_changes()
            tx.commit()
            return nuevo
        except Exception:
            tx.rollback()
            raise

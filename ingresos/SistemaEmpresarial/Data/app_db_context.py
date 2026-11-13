from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

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


def _fmt_dt(dt: Optional[datetime]) -> str:
    if dt is None:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat()


def _parse_dt(val: Any) -> datetime:
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)
    if isinstance(val, str):
        s = val.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return datetime.now(timezone.utc)


_ACCOUNT_TYPES_BY_INT = list(AccountType)
_CONCEPT_TYPES_BY_INT = list(ConceptType)
_TX_TYPES_BY_INT = list(TransactionType)


def _parse_account_type(val: Any) -> AccountType:
    if isinstance(val, AccountType):
        return val
    if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
        return _ACCOUNT_TYPES_BY_INT[int(val)]
    return AccountType(str(val))


def _parse_concept_type(val: Any) -> ConceptType:
    if isinstance(val, ConceptType):
        return val
    if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
        return _CONCEPT_TYPES_BY_INT[int(val)]
    return ConceptType(str(val))


def _parse_tx_type(val: Any) -> TransactionType:
    if isinstance(val, TransactionType):
        return val
    if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
        return _TX_TYPES_BY_INT[int(val)]
    return TransactionType(str(val))


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS "Companies" (
    "Id" TEXT NOT NULL PRIMARY KEY,
    "Name" TEXT NOT NULL,
    "LegalName" TEXT NULL,
    "TaxId" TEXT NULL,
    "Email" TEXT NULL,
    "Phone" TEXT NULL,
    "IsActive" INTEGER NOT NULL DEFAULT 1,
    "CreatedAt" TEXT NOT NULL,
    "UpdatedAt" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "Users" (
    "Id" TEXT NOT NULL PRIMARY KEY,
    "Name" TEXT NOT NULL,
    "Email" TEXT NOT NULL,
    "PasswordHash" TEXT NOT NULL,
    "EmailVerified" INTEGER NOT NULL DEFAULT 0,
    "IsActive" INTEGER NOT NULL DEFAULT 1,
    "CreatedAt" TEXT NOT NULL,
    "UpdatedAt" TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS "IX_Users_Email" ON "Users" ("Email");

CREATE TABLE IF NOT EXISTS "CompanyUsers" (
    "Id" TEXT NOT NULL PRIMARY KEY,
    "CompanyId" TEXT NOT NULL,
    "UserId" TEXT NOT NULL,
    "IsAdmin" INTEGER NOT NULL DEFAULT 0,
    "IsActive" INTEGER NOT NULL DEFAULT 1,
    "JoinedAt" TEXT NOT NULL,
    FOREIGN KEY ("CompanyId") REFERENCES "Companies" ("Id") ON DELETE CASCADE,
    FOREIGN KEY ("UserId") REFERENCES "Users" ("Id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "IX_CompanyUsers_CompanyId_Admin"
    ON "CompanyUsers" ("CompanyId") WHERE "IsAdmin" = 1;

CREATE TABLE IF NOT EXISTS "Accounts" (
    "Id" TEXT NOT NULL PRIMARY KEY,
    "CompanyId" TEXT NOT NULL,
    "AccountType" TEXT NOT NULL,
    "Name" TEXT NOT NULL,
    "BankName" TEXT NULL,
    "AccountNumber" TEXT NULL,
    "Clabe" TEXT NULL,
    "CardLastDigits" TEXT NULL,
    "ShortDescription" TEXT NULL,
    "LongDescription" TEXT NULL,
    "IsActive" INTEGER NOT NULL DEFAULT 1,
    "CreatedAt" TEXT NOT NULL,
    "UpdatedAt" TEXT NOT NULL,
    FOREIGN KEY ("CompanyId") REFERENCES "Companies" ("Id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "IX_Accounts_CompanyId_Name"
    ON "Accounts" ("CompanyId", "Name");

CREATE TABLE IF NOT EXISTS "Concepts" (
    "Id" TEXT NOT NULL PRIMARY KEY,
    "CompanyId" TEXT NOT NULL,
    "ConceptType" TEXT NOT NULL,
    "Name" TEXT NOT NULL,
    "ShortDescription" TEXT NULL,
    "LongDescription" TEXT NULL,
    "IsActive" INTEGER NOT NULL DEFAULT 1,
    "CreatedAt" TEXT NOT NULL,
    "UpdatedAt" TEXT NOT NULL,
    FOREIGN KEY ("CompanyId") REFERENCES "Companies" ("Id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "IX_Concepts_CompanyId_Name_ConceptType"
    ON "Concepts" ("CompanyId", "Name", "ConceptType");

CREATE TABLE IF NOT EXISTS "AccountConcepts" (
    "Id" TEXT NOT NULL PRIMARY KEY,
    "AccountId" TEXT NOT NULL,
    "ConceptId" TEXT NOT NULL,
    "IsActive" INTEGER NOT NULL DEFAULT 1,
    "CreatedAt" TEXT NOT NULL,
    FOREIGN KEY ("AccountId") REFERENCES "Accounts" ("Id") ON DELETE CASCADE,
    FOREIGN KEY ("ConceptId") REFERENCES "Concepts" ("Id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "IX_AccountConcepts_AccountId_ConceptId"
    ON "AccountConcepts" ("AccountId", "ConceptId");

CREATE TABLE IF NOT EXISTS "Transactions" (
    "Id" TEXT NOT NULL PRIMARY KEY,
    "AccountId" TEXT NOT NULL,
    "ConceptId" TEXT NOT NULL,
    "TransactionType" TEXT NOT NULL,
    "Amount" TEXT NOT NULL,
    "TransactionDate" TEXT NOT NULL,
    "CapturedAt" TEXT NOT NULL,
    "CapturedBy" TEXT NOT NULL,
    "ShortDescription" TEXT NULL,
    "LongDescription" TEXT NULL,
    "IsActive" INTEGER NOT NULL DEFAULT 1,
    "CreatedAt" TEXT NOT NULL,
    "UpdatedAt" TEXT NOT NULL,
    FOREIGN KEY ("AccountId") REFERENCES "Accounts" ("Id") ON DELETE RESTRICT,
    FOREIGN KEY ("ConceptId") REFERENCES "Concepts" ("Id") ON DELETE RESTRICT,
    FOREIGN KEY ("CapturedBy") REFERENCES "Users" ("Id") ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS "IX_Transactions_AccountId_TransactionDate"
    ON "Transactions" ("AccountId", "TransactionDate");

CREATE TABLE IF NOT EXISTS "Roles" (
    "Id" TEXT NOT NULL PRIMARY KEY,
    "Code" TEXT NOT NULL,
    "Name" TEXT NOT NULL,
    "Description" TEXT NULL,
    "IsActive" INTEGER NOT NULL DEFAULT 1,
    "CreatedAt" TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS "IX_Roles_Code" ON "Roles" ("Code");

CREATE TABLE IF NOT EXISTS "Permissions" (
    "Id" TEXT NOT NULL PRIMARY KEY,
    "Code" TEXT NOT NULL,
    "Name" TEXT NOT NULL,
    "Description" TEXT NULL,
    "IsActive" INTEGER NOT NULL DEFAULT 1,
    "CreatedAt" TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS "IX_Permissions_Code" ON "Permissions" ("Code");

CREATE TABLE IF NOT EXISTS "RolePermissions" (
    "Id" TEXT NOT NULL PRIMARY KEY,
    "RoleId" TEXT NOT NULL,
    "PermissionId" TEXT NOT NULL,
    "IsActive" INTEGER NOT NULL DEFAULT 1,
    "CreatedAt" TEXT NOT NULL,
    FOREIGN KEY ("RoleId") REFERENCES "Roles" ("Id") ON DELETE RESTRICT,
    FOREIGN KEY ("PermissionId") REFERENCES "Permissions" ("Id") ON DELETE RESTRICT
);
CREATE UNIQUE INDEX IF NOT EXISTS "IX_RolePermissions_RoleId_PermissionId"
    ON "RolePermissions" ("RoleId", "PermissionId");
CREATE INDEX IF NOT EXISTS "IX_RolePermissions_PermissionId"
    ON "RolePermissions" ("PermissionId");

CREATE TABLE IF NOT EXISTS "CompanyUserRoles" (
    "Id" TEXT NOT NULL PRIMARY KEY,
    "CompanyUserId" TEXT NOT NULL,
    "RoleId" TEXT NOT NULL,
    "IsActive" INTEGER NOT NULL DEFAULT 1,
    "CreatedAt" TEXT NOT NULL,
    FOREIGN KEY ("CompanyUserId") REFERENCES "CompanyUsers" ("Id") ON DELETE CASCADE,
    FOREIGN KEY ("RoleId") REFERENCES "Roles" ("Id") ON DELETE RESTRICT
);
CREATE UNIQUE INDEX IF NOT EXISTS "IX_CompanyUserRoles_CompanyUserId"
    ON "CompanyUserRoles" ("CompanyUserId") WHERE "IsActive" = 1;
CREATE INDEX IF NOT EXISTS "IX_CompanyUserRoles_RoleId"
    ON "CompanyUserRoles" ("RoleId");
"""


class DbTransaction:
    def __init__(self, ctx: "AppDbContext"):
        self._ctx = ctx
        self._active = False

    def __enter__(self) -> "DbTransaction":
        if not self._ctx._in_transaction:
            self._ctx.conn.execute("BEGIN")
            self._ctx._in_transaction = True
            self._active = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._active and self._ctx._in_transaction:
            if exc_type is not None:
                self.rollback()
            else:
                self.commit()

    def commit(self) -> None:
        if self._ctx._in_transaction:
            self._ctx.conn.commit()
            self._ctx._in_transaction = False
            self._active = False

    def rollback(self) -> None:
        if self._ctx._in_transaction:
            self._ctx.conn.rollback()
            self._ctx._in_transaction = False
            self._active = False


class AppDbContext:
    """
    Equivalente en Python a AppDbContext (Entity Framework Core).
    Gestiona las entidades, consultas y transacciones sobre SQLite o PostgreSQL.
    """

    def __init__(
        self,
        connection: Union[str, sqlite3.Connection] = "sistema_empresarial.db",
        after_save_interceptor: Optional[Callable[[], None]] = None,
    ):
        if isinstance(connection, sqlite3.Connection):
            self.conn = connection
            self._owns_connection = False
        else:
            db_path = connection
            if not db_path or "Host=" in db_path or db_path.startswith("postgres"):
                # Si se pasa una cadena de conexión estilo PostgreSQL pero se ejecuta localmente sin driver externo,
                # usa el archivo SQLite local por defecto manteniendo exactamente el mismo esquema SQL.
                db_path = "sistema_empresarial.db"
            self.conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
            self._owns_connection = True

        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._in_transaction = False
        self._after_save_interceptor = after_save_interceptor
        self._pending_ops: List[Tuple[str, Tuple[Any, ...]]] = []

    def ensure_created(self) -> None:
        for stmt in [s.strip() for s in SCHEMA_SQL.split(";") if s.strip()]:
            self.conn.execute(stmt)

    def execute_sql_raw(self, sql: str) -> None:
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            try:
                self.conn.execute(stmt)
            except sqlite3.OperationalError:
                pass

    def begin_transaction(self) -> DbTransaction:
        return DbTransaction(self)

    def queue_sql(self, sql: str, params: Tuple[Any, ...] = ()) -> None:
        self._pending_ops.append((sql, params))

    def save_changes(self) -> int:
        own_tx = not self._in_transaction
        if own_tx:
            self.conn.execute("BEGIN")
            self._in_transaction = True
        try:
            count = 0
            while self._pending_ops:
                sql, params = self._pending_ops.pop(0)
                cur = self.conn.execute(sql, params)
                count += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 1

            # Interceptor equivalente a SaveChangesInterceptor.SavedChangesAsync (después del flush, antes del commit)
            if self._after_save_interceptor is not None:
                self._after_save_interceptor()

            if own_tx:
                self.conn.commit()
                self._in_transaction = False
            return count
        except Exception:
            if own_tx and self._in_transaction:
                self.conn.rollback()
                self._in_transaction = False
            raise

    def close(self) -> None:
        if self._owns_connection:
            self.conn.close()

    # ---------- Mapeadores de filas a Modelos ----------

    @staticmethod
    def _row_to_company(row: sqlite3.Row) -> Company:
        return Company(
            id=row["Id"],
            name=row["Name"],
            legal_name=row["LegalName"],
            tax_id=row["TaxId"],
            email=row["Email"],
            phone=row["Phone"],
            is_active=bool(row["IsActive"]),
            created_at=_parse_dt(row["CreatedAt"]),
            updated_at=_parse_dt(row["UpdatedAt"]),
        )

    @staticmethod
    def _row_to_user(row: sqlite3.Row) -> User:
        return User(
            id=row["Id"],
            name=row["Name"],
            email=row["Email"],
            password_hash=row["PasswordHash"],
            email_verified=bool(row["EmailVerified"]),
            is_active=bool(row["IsActive"]),
            created_at=_parse_dt(row["CreatedAt"]),
            updated_at=_parse_dt(row["UpdatedAt"]),
        )

    @staticmethod
    def _row_to_company_user(row: sqlite3.Row) -> CompanyUser:
        return CompanyUser(
            id=row["Id"],
            company_id=row["CompanyId"],
            user_id=row["UserId"],
            is_admin=bool(row["IsAdmin"]),
            is_active=bool(row["IsActive"]),
            joined_at=_parse_dt(row["JoinedAt"]),
        )

    @staticmethod
    def _row_to_account(row: sqlite3.Row) -> Account:
        return Account(
            id=row["Id"],
            company_id=row["CompanyId"],
            account_type=_parse_account_type(row["AccountType"]),
            name=row["Name"],
            bank_name=row["BankName"],
            account_number=row["AccountNumber"],
            clabe=row["Clabe"],
            card_last_digits=row["CardLastDigits"],
            short_description=row["ShortDescription"],
            long_description=row["LongDescription"],
            is_active=bool(row["IsActive"]),
            created_at=_parse_dt(row["CreatedAt"]),
            updated_at=_parse_dt(row["UpdatedAt"]),
        )

    @staticmethod
    def _row_to_concept(row: sqlite3.Row) -> Concept:
        return Concept(
            id=row["Id"],
            company_id=row["CompanyId"],
            concept_type=_parse_concept_type(row["ConceptType"]),
            name=row["Name"],
            short_description=row["ShortDescription"],
            long_description=row["LongDescription"],
            is_active=bool(row["IsActive"]),
            created_at=_parse_dt(row["CreatedAt"]),
            updated_at=_parse_dt(row["UpdatedAt"]),
        )

    @staticmethod
    def _row_to_account_concept(row: sqlite3.Row) -> AccountConcept:
        return AccountConcept(
            id=row["Id"],
            account_id=row["AccountId"],
            concept_id=row["ConceptId"],
            is_active=bool(row["IsActive"]),
            created_at=_parse_dt(row["CreatedAt"]),
        )

    @staticmethod
    def _row_to_transaction(row: sqlite3.Row) -> Transaction:
        return Transaction(
            id=row["Id"],
            account_id=row["AccountId"],
            concept_id=row["ConceptId"],
            transaction_type=_parse_tx_type(row["TransactionType"]),
            amount=DecimalScalar(Decimal(str(row["Amount"]))),
            transaction_date=_parse_dt(row["TransactionDate"]),
            captured_at=_parse_dt(row["CapturedAt"]),
            captured_by=row["CapturedBy"],
            short_description=row["ShortDescription"],
            long_description=row["LongDescription"],
            is_active=bool(row["IsActive"]),
            created_at=_parse_dt(row["CreatedAt"]),
            updated_at=_parse_dt(row["UpdatedAt"]),
        )

    @staticmethod
    def _row_to_role(row: sqlite3.Row) -> Role:
        return Role(
            id=row["Id"],
            code=row["Code"],
            name=row["Name"],
            description=row["Description"],
            is_active=bool(row["IsActive"]),
            created_at=_parse_dt(row["CreatedAt"]),
        )

    @staticmethod
    def _row_to_permission(row: sqlite3.Row) -> Permission:
        return Permission(
            id=row["Id"],
            code=row["Code"],
            name=row["Name"],
            description=row["Description"],
            is_active=bool(row["IsActive"]),
            created_at=_parse_dt(row["CreatedAt"]),
        )

    @staticmethod
    def _row_to_role_permission(row: sqlite3.Row) -> RolePermission:
        return RolePermission(
            id=row["Id"],
            role_id=row["RoleId"],
            permission_id=row["PermissionId"],
            is_active=bool(row["IsActive"]),
            created_at=_parse_dt(row["CreatedAt"]),
        )

    @staticmethod
    def _row_to_company_user_role(row: sqlite3.Row) -> CompanyUserRole:
        return CompanyUserRole(
            id=row["Id"],
            company_user_id=row["CompanyUserId"],
            role_id=row["RoleId"],
            is_active=bool(row["IsActive"]),
            created_at=_parse_dt(row["CreatedAt"]),
        )

    # ---------- Operaciones de inserción y actualización ----------

    def add_company(self, c: Company) -> None:
        self.queue_sql(
            'INSERT INTO "Companies" ("Id", "Name", "LegalName", "TaxId", "Email", "Phone", "IsActive", "CreatedAt", "UpdatedAt") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (c.id, c.name, c.legal_name, c.tax_id, c.email, c.phone, int(c.is_active), _fmt_dt(c.created_at), _fmt_dt(c.updated_at)),
        )

    def update_company(self, c: Company) -> None:
        self.queue_sql(
            'UPDATE "Companies" SET "Name"=?, "LegalName"=?, "TaxId"=?, "Email"=?, "Phone"=?, "IsActive"=?, "UpdatedAt"=? WHERE "Id"=?',
            (c.name, c.legal_name, c.tax_id, c.email, c.phone, int(c.is_active), _fmt_dt(c.updated_at), c.id),
        )

    def add_user(self, u: User) -> None:
        self.queue_sql(
            'INSERT INTO "Users" ("Id", "Name", "Email", "PasswordHash", "EmailVerified", "IsActive", "CreatedAt", "UpdatedAt") VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (u.id, u.name, u.email, u.password_hash, int(u.email_verified), int(u.is_active), _fmt_dt(u.created_at), _fmt_dt(u.updated_at)),
        )

    def add_company_user(self, cu: CompanyUser) -> None:
        self.queue_sql(
            'INSERT INTO "CompanyUsers" ("Id", "CompanyId", "UserId", "IsAdmin", "IsActive", "JoinedAt") VALUES (?, ?, ?, ?, ?, ?)',
            (cu.id, cu.company_id, cu.user_id, int(cu.is_admin), int(cu.is_active), _fmt_dt(cu.joined_at)),
        )

    def add_account(self, a: Account) -> None:
        self.queue_sql(
            'INSERT INTO "Accounts" ("Id", "CompanyId", "AccountType", "Name", "BankName", "AccountNumber", "Clabe", "CardLastDigits", "ShortDescription", "LongDescription", "IsActive", "CreatedAt", "UpdatedAt") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                a.id,
                a.company_id,
                a.account_type.value,
                a.name,
                a.bank_name,
                a.account_number,
                a.clabe,
                a.card_last_digits,
                a.short_description,
                a.long_description,
                int(a.is_active),
                _fmt_dt(a.created_at),
                _fmt_dt(a.updated_at),
            ),
        )

    def add_concept(self, c: Concept) -> None:
        self.queue_sql(
            'INSERT INTO "Concepts" ("Id", "CompanyId", "ConceptType", "Name", "ShortDescription", "LongDescription", "IsActive", "CreatedAt", "UpdatedAt") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                c.id,
                c.company_id,
                c.concept_type.value,
                c.name,
                c.short_description,
                c.long_description,
                int(c.is_active),
                _fmt_dt(c.created_at),
                _fmt_dt(c.updated_at),
            ),
        )

    def add_account_concept(self, ac: AccountConcept) -> None:
        self.queue_sql(
            'INSERT INTO "AccountConcepts" ("Id", "AccountId", "ConceptId", "IsActive", "CreatedAt") VALUES (?, ?, ?, ?, ?)',
            (ac.id, ac.account_id, ac.concept_id, int(ac.is_active), _fmt_dt(ac.created_at)),
        )

    def update_account_concept_active(self, ac_id: str, is_active: bool) -> None:
        self.queue_sql(
            'UPDATE "AccountConcepts" SET "IsActive"=? WHERE "Id"=?',
            (int(is_active), ac_id),
        )

    def add_transaction(self, t: Transaction) -> None:
        amt_str = f"{Decimal(str(t.amount)):.2f}"
        self.queue_sql(
            'INSERT INTO "Transactions" ("Id", "AccountId", "ConceptId", "TransactionType", "Amount", "TransactionDate", "CapturedAt", "CapturedBy", "ShortDescription", "LongDescription", "IsActive", "CreatedAt", "UpdatedAt") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                t.id,
                t.account_id,
                t.concept_id,
                t.transaction_type.value,
                amt_str,
                _fmt_dt(t.transaction_date),
                _fmt_dt(t.captured_at),
                t.captured_by,
                t.short_description,
                t.long_description,
                int(t.is_active),
                _fmt_dt(t.created_at),
                _fmt_dt(t.updated_at),
            ),
        )

    def update_transaction_active(self, tx_id: str, is_active: bool, updated_at: datetime) -> None:
        self.queue_sql(
            'UPDATE "Transactions" SET "IsActive"=?, "UpdatedAt"=? WHERE "Id"=?',
            (int(is_active), _fmt_dt(updated_at), tx_id),
        )

    def add_role(self, r: Role) -> None:
        self.queue_sql(
            'INSERT INTO "Roles" ("Id", "Code", "Name", "Description", "IsActive", "CreatedAt") VALUES (?, ?, ?, ?, ?, ?)',
            (r.id, r.code, r.name, r.description, int(r.is_active), _fmt_dt(r.created_at)),
        )

    def update_role_active(self, role_id: str, is_active: bool) -> None:
        self.queue_sql(
            'UPDATE "Roles" SET "IsActive"=? WHERE "Id"=?',
            (int(is_active), role_id),
        )

    def add_permission(self, p: Permission) -> None:
        self.queue_sql(
            'INSERT INTO "Permissions" ("Id", "Code", "Name", "Description", "IsActive", "CreatedAt") VALUES (?, ?, ?, ?, ?, ?)',
            (p.id, p.code, p.name, p.description, int(p.is_active), _fmt_dt(p.created_at)),
        )

    def add_role_permission(self, rp: RolePermission) -> None:
        self.queue_sql(
            'INSERT INTO "RolePermissions" ("Id", "RoleId", "PermissionId", "IsActive", "CreatedAt") VALUES (?, ?, ?, ?, ?)',
            (rp.id, rp.role_id, rp.permission_id, int(rp.is_active), _fmt_dt(rp.created_at)),
        )

    def update_role_permission_active(self, rp_id: str, is_active: bool) -> None:
        self.queue_sql(
            'UPDATE "RolePermissions" SET "IsActive"=? WHERE "Id"=?',
            (int(is_active), rp_id),
        )

    def add_company_user_role(self, cur: CompanyUserRole) -> None:
        self.queue_sql(
            'INSERT INTO "CompanyUserRoles" ("Id", "CompanyUserId", "RoleId", "IsActive", "CreatedAt") VALUES (?, ?, ?, ?, ?)',
            (cur.id, cur.company_user_id, cur.role_id, int(cur.is_active), _fmt_dt(cur.created_at)),
        )

    def update_company_user_role_active(self, cur_id: str, is_active: bool) -> None:
        self.queue_sql(
            'UPDATE "CompanyUserRoles" SET "IsActive"=? WHERE "Id"=?',
            (int(is_active), cur_id),
        )

    # ---------- Consultas ----------

    def get_company_by_id(self, company_id: str) -> Optional[Company]:
        row = self.conn.execute('SELECT * FROM "Companies" WHERE "Id"=?', (company_id,)).fetchone()
        return self._row_to_company(row) if row else None

    def get_companies(self, active_only: Optional[bool] = None) -> List[Company]:
        if active_only:
            rows = self.conn.execute('SELECT * FROM "Companies" WHERE "IsActive"=1').fetchall()
        else:
            rows = self.conn.execute('SELECT * FROM "Companies"').fetchall()
        return [self._row_to_company(r) for r in rows]

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        row = self.conn.execute('SELECT * FROM "Users" WHERE "Id"=?', (user_id,)).fetchone()
        return self._row_to_user(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[User]:
        row = self.conn.execute('SELECT * FROM "Users" WHERE "Email"=?', (email,)).fetchone()
        return self._row_to_user(row) if row else None

    def get_company_user_by_id(self, cu_id: str, include_user: bool = False, include_company: bool = False) -> Optional[CompanyUser]:
        row = self.conn.execute('SELECT * FROM "CompanyUsers" WHERE "Id"=?', (cu_id,)).fetchone()
        if not row:
            return None
        cu = self._row_to_company_user(row)
        if include_user:
            cu.user = self.get_user_by_id(cu.user_id)
        if include_company:
            cu.company = self.get_company_by_id(cu.company_id)
        return cu

    def get_active_company_user_for_user(self, user_id: str) -> Optional[CompanyUser]:
        row = self.conn.execute(
            'SELECT * FROM "CompanyUsers" WHERE "UserId"=? AND "IsActive"=1 LIMIT 1',
            (user_id,),
        ).fetchone()
        return self._row_to_company_user(row) if row else None

    def has_active_admin(self, company_id: str) -> bool:
        row = self.conn.execute(
            'SELECT 1 FROM "CompanyUsers" WHERE "CompanyId"=? AND "IsAdmin"=1 AND "IsActive"=1 LIMIT 1',
            (company_id,),
        ).fetchone()
        return row is not None

    def get_company_users(self, company_id: str) -> List[CompanyUser]:
        rows = self.conn.execute('SELECT * FROM "CompanyUsers" WHERE "CompanyId"=?', (company_id,)).fetchall()
        result: List[CompanyUser] = []
        for r in rows:
            cu = self._row_to_company_user(r)
            cu.user = self.get_user_by_id(cu.user_id)
            cu.company = self.get_company_by_id(cu.company_id)
            result.append(cu)
        return result

    def get_all_company_users(self) -> List[CompanyUser]:
        rows = self.conn.execute('SELECT * FROM "CompanyUsers"').fetchall()
        return [self._row_to_company_user(r) for r in rows]

    def get_account_by_id(self, account_id: str) -> Optional[Account]:
        row = self.conn.execute('SELECT * FROM "Accounts" WHERE "Id"=?', (account_id,)).fetchone()
        return self._row_to_account(row) if row else None

    def get_accounts_by_company(
        self,
        company_id: str,
        account_type: Optional[AccountType] = None,
        active_only: Optional[bool] = None,
        include_company: bool = False,
    ) -> List[Account]:
        sql = 'SELECT * FROM "Accounts" WHERE "CompanyId"=?'
        params: List[Any] = [company_id]
        if account_type is not None:
            sql += ' AND "AccountType"=?'
            params.append(account_type.value)
        if active_only:
            sql += ' AND "IsActive"=1'
        rows = self.conn.execute(sql, tuple(params)).fetchall()
        comp = self.get_company_by_id(company_id) if include_company else None
        accounts: List[Account] = []
        for r in rows:
            a = self._row_to_account(r)
            if include_company:
                a.company = comp
            accounts.append(a)
        return accounts

    def account_name_exists(self, company_id: str, name: str) -> bool:
        row = self.conn.execute(
            'SELECT 1 FROM "Accounts" WHERE "CompanyId"=? AND LOWER("Name")=LOWER(?) LIMIT 1',
            (company_id, name),
        ).fetchone()
        return row is not None

    def get_concept_by_id(self, concept_id: str) -> Optional[Concept]:
        row = self.conn.execute('SELECT * FROM "Concepts" WHERE "Id"=?', (concept_id,)).fetchone()
        return self._row_to_concept(row) if row else None

    def get_concepts_by_company(
        self,
        company_id: str,
        concept_type: Optional[ConceptType] = None,
        active_only: Optional[bool] = None,
    ) -> List[Concept]:
        sql = 'SELECT * FROM "Concepts" WHERE "CompanyId"=?'
        params: List[Any] = [company_id]
        if concept_type is not None:
            sql += ' AND "ConceptType"=?'
            params.append(concept_type.value)
        if active_only:
            sql += ' AND "IsActive"=1'
        rows = self.conn.execute(sql, tuple(params)).fetchall()
        return [self._row_to_concept(r) for r in rows]

    def concept_exists(self, company_id: str, concept_type: ConceptType, name: str) -> bool:
        row = self.conn.execute(
            'SELECT 1 FROM "Concepts" WHERE "CompanyId"=? AND "ConceptType"=? AND LOWER("Name")=LOWER(?) LIMIT 1',
            (company_id, concept_type.value, name),
        ).fetchone()
        return row is not None

    def get_account_concept(self, account_id: str, concept_id: str, include_relations: bool = False) -> Optional[AccountConcept]:
        row = self.conn.execute(
            'SELECT * FROM "AccountConcepts" WHERE "AccountId"=? AND "ConceptId"=?',
            (account_id, concept_id),
        ).fetchone()
        if not row:
            return None
        ac = self._row_to_account_concept(row)
        if include_relations:
            ac.account = self.get_account_by_id(ac.account_id)
            ac.concept = self.get_concept_by_id(ac.concept_id)
        return ac

    def get_account_concepts_by_account(self, account_id: str) -> List[AccountConcept]:
        rows = self.conn.execute('SELECT * FROM "AccountConcepts" WHERE "AccountId"=?', (account_id,)).fetchall()
        acc = self.get_account_by_id(account_id)
        result: List[AccountConcept] = []
        for r in rows:
            ac = self._row_to_account_concept(r)
            ac.account = acc
            ac.concept = self.get_concept_by_id(ac.concept_id)
            result.append(ac)
        return result

    def get_transaction_by_id(self, tx_id: str, include_relations: bool = True) -> Optional[Transaction]:
        row = self.conn.execute('SELECT * FROM "Transactions" WHERE "Id"=?', (tx_id,)).fetchone()
        if not row:
            return None
        t = self._row_to_transaction(row)
        if include_relations:
            t.account = self.get_account_by_id(t.account_id)
            t.concept = self.get_concept_by_id(t.concept_id)
            t.captured_by_user = self.get_user_by_id(t.captured_by)
        return t

    def get_transactions_for_company(
        self,
        company_id: str,
        account_id: Optional[str] = None,
        transaction_type: Optional[TransactionType] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_relations: bool = True,
    ) -> List[Transaction]:
        sql = """
            SELECT t.* FROM "Transactions" t
            JOIN "Accounts" a ON a."Id" = t."AccountId"
            WHERE t."IsActive" = 1 AND a."CompanyId" = ?
        """
        params: List[Any] = [company_id]
        if account_id and account_id.strip():
            sql += ' AND t."AccountId" = ?'
            params.append(account_id)
        if transaction_type is not None:
            sql += ' AND t."TransactionType" = ?'
            params.append(transaction_type.value)
        sql += ' ORDER BY t."TransactionDate" DESC'
        rows = self.conn.execute(sql, tuple(params)).fetchall()
        items = [self._row_to_transaction(r) for r in rows]
        # Ordenar por datetime real descendente por seguridad ante formatos ISO
        items.sort(key=lambda x: x.transaction_date, reverse=True)
        if offset is not None and offset > 0:
            items = items[offset:]
        if limit is not None and limit > 0:
            items = items[:limit]
        if include_relations:
            for t in items:
                t.account = self.get_account_by_id(t.account_id)
                t.concept = self.get_concept_by_id(t.concept_id)
                t.captured_by_user = self.get_user_by_id(t.captured_by)
        return items

    def get_roles(self, active_only: Optional[bool] = None) -> List[Role]:
        if active_only:
            rows = self.conn.execute('SELECT * FROM "Roles" WHERE "IsActive"=1 ORDER BY "Code"').fetchall()
        else:
            rows = self.conn.execute('SELECT * FROM "Roles" ORDER BY "Code"').fetchall()
        return [self._row_to_role(r) for r in rows]

    def get_role_by_id(self, role_id: str) -> Optional[Role]:
        row = self.conn.execute('SELECT * FROM "Roles" WHERE "Id"=?', (role_id,)).fetchone()
        return self._row_to_role(row) if row else None

    def get_role_by_code(self, code: str) -> Optional[Role]:
        row = self.conn.execute('SELECT * FROM "Roles" WHERE "Code"=?', (code,)).fetchone()
        return self._row_to_role(row) if row else None

    def get_permissions(self, active_only: Optional[bool] = None, prefix: Optional[str] = None) -> List[Permission]:
        sql = 'SELECT * FROM "Permissions" WHERE 1=1'
        params: List[Any] = []
        if active_only:
            sql += ' AND "IsActive"=1'
        if prefix is not None:
            sql += ' AND "Code" LIKE ?'
            params.append(f"{prefix}%")
        sql += ' ORDER BY "Code"'
        rows = self.conn.execute(sql, tuple(params)).fetchall()
        return [self._row_to_permission(r) for r in rows]

    def get_permission_by_id(self, perm_id: str) -> Optional[Permission]:
        row = self.conn.execute('SELECT * FROM "Permissions" WHERE "Id"=?', (perm_id,)).fetchone()
        return self._row_to_permission(row) if row else None

    def get_permission_by_code(self, code: str) -> Optional[Permission]:
        row = self.conn.execute('SELECT * FROM "Permissions" WHERE "Code"=?', (code,)).fetchone()
        return self._row_to_permission(row) if row else None

    def get_permissions_by_ids(self, ids: List[str]) -> List[Permission]:
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        rows = self.conn.execute(
            f'SELECT * FROM "Permissions" WHERE "Id" IN ({placeholders})',
            tuple(ids),
        ).fetchall()
        return [self._row_to_permission(r) for r in rows]

    def get_role_permissions_by_role(self, role_id: str, active_only: bool = False) -> List[RolePermission]:
        sql = 'SELECT * FROM "RolePermissions" WHERE "RoleId"=?'
        if active_only:
            sql += ' AND "IsActive"=1'
        rows = self.conn.execute(sql, (role_id,)).fetchall()
        role = self.get_role_by_id(role_id)
        result: List[RolePermission] = []
        for r in rows:
            rp = self._row_to_role_permission(r)
            rp.role = role
            rp.permission = self.get_permission_by_id(rp.permission_id)
            result.append(rp)
        result.sort(key=lambda x: x.permission.code if x.permission else "")
        return result

    def get_role_permission(self, role_id: str, permission_id: str) -> Optional[RolePermission]:
        row = self.conn.execute(
            'SELECT * FROM "RolePermissions" WHERE "RoleId"=? AND "PermissionId"=?',
            (role_id, permission_id),
        ).fetchone()
        return self._row_to_role_permission(row) if row else None

    def get_active_company_user_roles(self, company_user_id: str) -> List[CompanyUserRole]:
        rows = self.conn.execute(
            'SELECT * FROM "CompanyUserRoles" WHERE "CompanyUserId"=? AND "IsActive"=1',
            (company_user_id,),
        ).fetchall()
        return [self._row_to_company_user_role(r) for r in rows]

    def get_company_user_roles_by_company(self, company_id: str) -> List[CompanyUserRole]:
        sql = """
            SELECT cur.* FROM "CompanyUserRoles" cur
            JOIN "CompanyUsers" cu ON cu."Id" = cur."CompanyUserId"
            WHERE cur."IsActive" = 1 AND cu."CompanyId" = ?
        """
        rows = self.conn.execute(sql, (company_id,)).fetchall()
        result: List[CompanyUserRole] = []
        for r in rows:
            cur = self._row_to_company_user_role(r)
            cur.company_user = self.get_company_user_by_id(cur.company_user_id, include_user=True, include_company=True)
            cur.role = self.get_role_by_id(cur.role_id)
            result.append(cur)
        return result

    def role_has_active_permission(self, role_id: str, perm_code: str) -> bool:
        sql = """
            SELECT 1
            FROM "RolePermissions" rp
            JOIN "Roles" r ON r."Id" = rp."RoleId"
            JOIN "Permissions" p ON p."Id" = rp."PermissionId"
            WHERE rp."RoleId" = ?
              AND rp."IsActive" = 1
              AND r."IsActive" = 1
              AND p."Code" = ?
              AND p."IsActive" = 1
            LIMIT 1
        """
        row = self.conn.execute(sql, (role_id, perm_code)).fetchone()
        return row is not None

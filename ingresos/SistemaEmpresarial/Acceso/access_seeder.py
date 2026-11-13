from Data import AppDbContext
from Models import CompanyUserRole, Permission, Role, RolePermission
from .access_control import Perm


class AccessSeeder:
    # Los cuatro roles del documento
    ROLES_INICIALES = [
        ("ADMINISTRADOR", "Administrador", "Administrador principal de la empresa"),
        ("CONTADOR", "Contador", "Arma cuentas y conceptos y registra movimientos"),
        ("CAPTURISTA", "Capturista", "Registra movimientos"),
        ("CONSULTA", "Consulta", "Solo lee"),
    ]

    # Los diez permisos del documento
    PERMISOS_INICIALES = [
        (Perm.COMPANY_USERS_READ, "Ver usuarios", "Ver las membresías de la empresa"),
        (Perm.COMPANY_USERS_WRITE, "Administrar usuarios", "Crear usuarios y desactivar membresías"),
        (Perm.ACCOUNTS_READ, "Consultar cuentas", "Consultar cuentas"),
        (Perm.ACCOUNTS_WRITE, "Crear cuentas", "Crear cuentas"),
        (Perm.CONCEPTS_READ, "Consultar conceptos", "Consultar conceptos"),
        (Perm.CONCEPTS_WRITE, "Crear conceptos", "Crear conceptos y asignarlos a una cuenta"),
        (Perm.TRANSACTIONS_READ, "Consultar movimientos", "Consultar movimientos"),
        (Perm.TRANSACTIONS_WRITE, "Registrar movimientos", "Registrar un ingreso o un egreso"),
        (Perm.ROLES_READ, "Ver roles", "Ver roles y la matriz de permisos"),
        (Perm.ROLES_WRITE, "Administrar roles", "Asignar o quitar permisos de un rol, y asignar un rol a una membresía"),
    ]

    # Matriz inicial: rol → permisos
    MATRIZ = {
        "ADMINISTRADOR": [
            Perm.COMPANY_USERS_READ, Perm.COMPANY_USERS_WRITE,
            Perm.ACCOUNTS_READ, Perm.ACCOUNTS_WRITE,
            Perm.CONCEPTS_READ, Perm.CONCEPTS_WRITE,
            Perm.TRANSACTIONS_READ, Perm.TRANSACTIONS_WRITE,
            Perm.ROLES_READ, Perm.ROLES_WRITE,
        ],
        "CONTADOR": [
            Perm.COMPANY_USERS_READ,
            Perm.ACCOUNTS_READ, Perm.ACCOUNTS_WRITE,
            Perm.CONCEPTS_READ, Perm.CONCEPTS_WRITE,
            Perm.TRANSACTIONS_READ, Perm.TRANSACTIONS_WRITE,
            Perm.ROLES_READ,
        ],
        "CAPTURISTA": [
            Perm.ACCOUNTS_READ,
            Perm.CONCEPTS_READ,
            Perm.TRANSACTIONS_READ, Perm.TRANSACTIONS_WRITE,
        ],
        "CONSULTA": [
            Perm.COMPANY_USERS_READ,
            Perm.ACCOUNTS_READ,
            Perm.CONCEPTS_READ,
            Perm.TRANSACTIONS_READ,
        ],
    }

    @classmethod
    def seed(cls, db: AppDbContext) -> None:
        db.ensure_created()

        # 1. Roles: solo si la tabla está vacía (un reinicio no duplica)
        if not db.get_roles():
            for code, name, desc in cls.ROLES_INICIALES:
                db.add_role(Role(code=code, name=name, description=desc))
            db.save_changes()

        # 2. Permisos: solo si la tabla está vacía
        if not db.get_permissions():
            for code, name, desc in cls.PERMISOS_INICIALES:
                db.add_permission(Permission(code=code, name=name, description=desc))
            db.save_changes()

        # 3. Matriz: solo para los roles que todavía no tienen ningún permiso
        permisos_por_codigo = {p.code: p.id for p in db.get_permissions()}

        for rol in db.get_roles():
            codigos = cls.MATRIZ.get(rol.code)
            if not codigos:
                continue
            if db.get_role_permissions_by_role(rol.id):
                continue
            for codigo in codigos:
                perm_id = permisos_por_codigo.get(codigo)
                if perm_id:
                    db.add_role_permission(RolePermission(role_id=rol.id, permission_id=perm_id))

        db.save_changes()

        # 4. Administradores que ya existían antes de esta actividad reciben el rol ADMINISTRADOR
        admin = db.get_role_by_code("ADMINISTRADOR")
        if admin is not None:
            for cu in db.get_all_company_users():
                if cu.is_admin and cu.is_active:
                    activos = db.get_active_company_user_roles(cu.id)
                    if not activos:
                        db.add_company_user_role(CompanyUserRole(company_user_id=cu.id, role_id=admin.id))
            db.save_changes()

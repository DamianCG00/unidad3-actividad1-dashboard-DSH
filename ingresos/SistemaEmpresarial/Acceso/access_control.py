from Balances import GraphQLException
from Data import AppDbContext
from Models import CompanyUser


class Perm:
    """Códigos de permiso del catálogo (recurso.accion)."""
    COMPANY_USERS_READ = "company.users.read"
    COMPANY_USERS_WRITE = "company.users.write"
    ACCOUNTS_READ = "accounts.read"
    ACCOUNTS_WRITE = "accounts.write"
    CONCEPTS_READ = "concepts.read"
    CONCEPTS_WRITE = "concepts.write"
    TRANSACTIONS_READ = "transactions.read"
    TRANSACTIONS_WRITE = "transactions.write"
    ROLES_READ = "roles.read"
    ROLES_WRITE = "roles.write"


class AccessControl:
    """
    Cadena: membresía → rol activo → permisos activos del rol → ¿está el código?
    Si falta algo lanza el error ANTES de que el resolver escriba, así no hay commit.
    Devuelve la membresía que actúa para que el resolver conozca su empresa y su usuario.
    """

    @staticmethod
    def exigir_permiso(db: AppDbContext, actor_company_user_id: str, codigo: str) -> CompanyUser:
        actor = db.get_company_user_by_id(actor_company_user_id, include_user=True)

        if actor is None or not actor.is_active:
            raise GraphQLException("La membresía no existe o está inactiva")

        if actor.user is None or not actor.user.is_active:
            raise GraphQLException("El usuario de la membresía está inactivo")

        asignaciones = db.get_active_company_user_roles(actor_company_user_id)
        if not asignaciones:
            raise GraphQLException("La membresía no tiene un rol activo")

        asignacion = asignaciones[0]

        permitido = db.role_has_active_permission(asignacion.role_id, codigo)
        if not permitido:
            raise GraphQLException(f"El rol no tiene el permiso {codigo}")

        return actor

    @staticmethod
    def exigir_misma_empresa(actor: CompanyUser, company_id: str) -> None:
        """Frontera entre empresas: el actor solo opera sobre datos de su propia empresa."""
        if actor.company_id != company_id:
            raise GraphQLException("La membresía no pertenece a la empresa del recurso")

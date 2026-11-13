from enum import Enum
import strawberry


@strawberry.enum
class PermissionResource(Enum):
    """Recursos del catálogo de permisos (filtro de permissionCatalog)."""
    COMPANY_USERS = "COMPANY_USERS"
    ACCOUNTS = "ACCOUNTS"
    CONCEPTS = "CONCEPTS"
    TRANSACTIONS = "TRANSACTIONS"
    ROLES = "ROLES"


class PermissionResourceMap:
    """
    Traduce el recurso al prefijo ya existente del código del permiso.
    No crea permisos nuevos.
    """

    @staticmethod
    def prefijo_de(recurso: PermissionResource) -> str:
        mapping = {
            PermissionResource.COMPANY_USERS: "company.users.",
            PermissionResource.ACCOUNTS: "accounts.",
            PermissionResource.CONCEPTS: "concepts.",
            PermissionResource.TRANSACTIONS: "transactions.",
            PermissionResource.ROLES: "roles.",
        }
        if recurso not in mapping:
            raise ValueError(f"Recurso fuera de rango: {recurso}")
        return mapping[recurso]

from typing import List, Optional
import strawberry
from strawberry.types import Info
from Acceso import AccessControl, Perm, PermissionResource, PermissionResourceMap, RolePermissionPlanner
from Models import Permission
from .query_balances import _db_from_info
from .role_permission_types import RolePermissionPlan, SetRolePermissionsInput


@strawberry.type
class QueryRolePermissions:
    @strawberry.field(name="permissionCatalog")
    def get_permission_catalog(
        self,
        info: Info,
        actor_company_user_id: strawberry.ID,
        resource: Optional[PermissionResource] = None,
    ) -> List[Permission]:
        """Solo permisos activos; sin resource (o null) devuelve todo el catálogo activo."""
        context = _db_from_info(info)
        AccessControl.exigir_permiso(context, str(actor_company_user_id), Perm.ROLES_READ)

        prefijo = PermissionResourceMap.prefijo_de(resource) if resource is not None else None
        return context.get_permissions(active_only=True, prefix=prefijo)

    @strawberry.field(name="previewRolePermissions")
    def preview_role_permissions(
        self,
        info: Info,
        input: SetRolePermissionsInput,
        actor_company_user_id: strawberry.ID,
    ) -> Optional[RolePermissionPlan]:
        """Valida y calcula. No inserta, actualiza ni desactiva filas."""
        context = _db_from_info(info)
        AccessControl.exigir_permiso(context, str(actor_company_user_id), Perm.ROLES_READ)

        return RolePermissionPlanner.calcular(
            context,
            str(input.role_id),
            [str(pid) for pid in input.permission_ids],
        )

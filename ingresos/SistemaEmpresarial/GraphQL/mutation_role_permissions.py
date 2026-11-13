import strawberry
from strawberry.types import Info
from Acceso import AccessControl, Perm, RolePermissionPlanner
from Data import AppDbContext
from Models import RolePermission
from .query_balances import _db_from_info
from .role_permission_types import RolePermissionUpdate, SetRolePermissionsInput


@strawberry.type
class MutationRolePermissions:
    def set_role_permissions_sync(
        self,
        input: SetRolePermissionsInput,
        actor_company_user_id: str,
        context: AppDbContext,
    ) -> RolePermissionUpdate:
        """
        Establece exactamente la lista recibida, en una sola transacción.
        Repetir la misma lista no cambia nada: changed = False.
        """
        AccessControl.exigir_permiso(context, str(actor_company_user_id), Perm.ROLES_WRITE)

        transaccion = context.begin_transaction()
        transaccion.__enter__()
        try:
            # Validar y calcular contra la base actual, dentro de la transacción
            plan = RolePermissionPlanner.calcular(
                context,
                str(input.role_id),
                [str(pid) for pid in input.permission_ids],
            )

            if plan.has_changes:
                for permiso in plan.to_activate:
                    existente = plan.relaciones.get(permiso.id)
                    if existente is not None:
                        # Reactiva la misma fila; no inserta duplicados
                        existente.is_active = True
                        context.update_role_permission_active(existente.id, True)
                    else:
                        context.add_role_permission(
                            RolePermission(
                                role_id=plan.role.id,
                                permission_id=permiso.id,
                                is_active=True,
                            )
                        )

                for permiso in plan.to_deactivate:
                    existente = plan.relaciones[permiso.id]
                    existente.is_active = False
                    context.update_role_permission_active(existente.id, False)

                context.save_changes()

            transaccion.commit()

            return RolePermissionUpdate(
                role=plan.role,
                activated=plan.to_activate,
                deactivated=plan.to_deactivate,
                unchanged=plan.unchanged,
                final_count=plan.final_count,
                changed=plan.has_changes,
            )
        except Exception:
            transaccion.rollback()
            raise

    @strawberry.mutation(name="setRolePermissions")
    def set_role_permissions(
        self,
        info: Info,
        input: SetRolePermissionsInput,
        actor_company_user_id: strawberry.ID,
    ) -> RolePermissionUpdate:
        context = _db_from_info(info)
        return MutationRolePermissions.set_role_permissions_sync(self, input, str(actor_company_user_id), context)

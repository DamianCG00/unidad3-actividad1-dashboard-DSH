from __future__ import annotations
from typing import Dict, List, Sequence
from Balances import GraphQLException
from Data import AppDbContext
from Models import Permission, RolePermission


class RolePermissionPlanner:
    """
    Validación y cálculo compartidos por previewRolePermissions y setRolePermissions.
    Así la previsualización y la aplicación no pueden dar resultados distintos.
    """

    CODIGO_ADMINISTRADOR = "ADMINISTRADOR"

    @classmethod
    def calcular(
        cls,
        db: AppDbContext,
        role_id: str,
        permission_ids: Sequence[str],
    ):
        from GraphQL.role_permission_types import RolePermissionPlan

        ids = [str(i) for i in permission_ids]

        # 1. Rol existente y activo
        role = db.get_role_by_id(role_id)
        if role is None or not role.is_active:
            raise GraphQLException("El rol no existe o está inactivo")

        # Regla del ejercicio: no dejar al administrador sin su lista
        if role.code == cls.CODIGO_ADMINISTRADOR:
            raise GraphQLException("En este laboratorio no se modifica la lista del rol ADMINISTRADOR")

        # 2. IDs repetidos: se rechazan, no se eliminan en silencio
        vistos = set()
        repetidos: List[str] = []
        for pid in ids:
            if pid in vistos and pid not in repetidos:
                repetidos.append(pid)
            vistos.add(pid)

        if repetidos:
            raise GraphQLException(f"IDs de permiso repetidos: {', '.join(repetidos)}")

        # 3. Existencia y estado activo de cada permiso
        permisos = db.get_permissions_by_ids(ids)
        encontrados_ids = {p.id for p in permisos}
        inexistentes = [pid for pid in ids if pid not in encontrados_ids]

        if inexistentes:
            raise GraphQLException(f"Permisos inexistentes: {', '.join(inexistentes)}")

        inactivos = [p.code for p in permisos if not p.is_active]
        if inactivos:
            raise GraphQLException(f"Permisos inactivos: {', '.join(inactivos)}")

        # 4. Comparación con la configuración actual
        # Un [] es válido: desactiva todas las relaciones activas del rol.
        relaciones = db.get_role_permissions_by_role(role.id, active_only=False)

        activos: List[Permission] = sorted(
            [rp.permission for rp in relaciones if rp.is_active and rp.permission is not None],
            key=lambda p: p.code,
        )
        deseados: List[Permission] = sorted(permisos, key=lambda p: p.code)

        ids_activos = {p.id for p in activos}
        ids_deseados = {p.id for p in deseados}

        relaciones_dict: Dict[str, RolePermission] = {rp.permission_id: rp for rp in relaciones}

        return RolePermissionPlan(
            role=role,
            current=activos,
            to_activate=[p for p in deseados if p.id not in ids_activos],
            to_deactivate=[p for p in activos if p.id not in ids_deseados],
            unchanged=[p for p in deseados if p.id in ids_activos],
            final_count=len(deseados),
            relaciones=relaciones_dict,
        )

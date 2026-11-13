from dataclasses import dataclass, field
from typing import Dict, List, Sequence
import strawberry
from Models import Permission, Role, RolePermission


@strawberry.input
@dataclass
class SetRolePermissionsInput:
    """Lista final de permisos de un rol. permissionIds: [ID!]! (la lista vacía sí es válida)."""
    role_id: strawberry.ID
    permission_ids: List[strawberry.ID]

    def __init__(self, role_id: str, permission_ids: Sequence[str]):
        self.role_id = strawberry.ID(str(role_id))
        self.permission_ids = [strawberry.ID(str(p)) for p in permission_ids]


@strawberry.type
@dataclass
class RolePermissionPlan:
    """Resultado de previewRolePermissions: calcula, no escribe."""
    role: Role
    current: List[Permission] = field(default_factory=list)
    to_activate: List[Permission] = field(default_factory=list)
    to_deactivate: List[Permission] = field(default_factory=list)
    unchanged: List[Permission] = field(default_factory=list)
    final_count: int = 0
    relaciones: strawberry.Private[Dict[str, RolePermission]] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return len(self.to_activate) > 0 or len(self.to_deactivate) > 0


@strawberry.type
@dataclass
class RolePermissionUpdate:
    """Resultado de setRolePermissions."""
    role: Role
    activated: List[Permission] = field(default_factory=list)
    deactivated: List[Permission] = field(default_factory=list)
    unchanged: List[Permission] = field(default_factory=list)
    final_count: int = 0
    changed: bool = False

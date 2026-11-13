import os
import sqlite3
import sys
import unittest
from dataclasses import dataclass
from typing import Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "SistemaEmpresarial")))

from Data import AppDbContext
from GraphQL import Mutation, SetRolePermissionsInput
from Models import Company, CompanyUser, CompanyUserRole, Permission, Role, RolePermission, User


@dataclass(frozen=True)
class Datos:
    actor_id: str
    rol_id: str
    permisos: Dict[str, str]


def _fallo_despues_de_flush() -> None:
    """
    Simula un fallo después de que el contexto envió los cambios a la base (flush),
    pero antes de que la transacción de la operación confirme.
    """
    raise RuntimeError("Fallo controlado después del flush")


class RolePermissionAtomicityTests(unittest.TestCase):
    """
    E07. Reversión de un fallo: se provoca una excepción después del flush
    y antes del commit. La base debe conservar la lista previa.
    """

    @staticmethod
    def _opciones(conexion: sqlite3.Connection, con_fallo: bool) -> AppDbContext:
        interceptor = _fallo_despues_de_flush if con_fallo else None
        return AppDbContext(conexion, after_save_interceptor=interceptor)

    @staticmethod
    def _sembrar(db: AppDbContext) -> Datos:
        empresa = Company(name="Empresa de prueba")
        usuario = User(name="Ana de prueba", email="ana@prueba.test", password_hash="no-se-usa")
        membresia = CompanyUser(company_id=empresa.id, user_id=usuario.id, is_admin=False)

        operador = Role(code="OPERADOR", name="Operador")
        capturista = Role(code="CAPTURISTA", name="Capturista")

        permisos = [
            Permission(code="roles.read", name="Ver roles"),
            Permission(code="roles.write", name="Administrar roles"),
            Permission(code="accounts.read", name="Consultar cuentas"),
            Permission(code="accounts.write", name="Crear cuentas"),
            Permission(code="concepts.read", name="Consultar conceptos"),
        ]

        db.add_company(empresa)
        db.add_user(usuario)
        db.add_company_user(membresia)
        db.add_role(operador)
        db.add_role(capturista)
        for p in permisos:
            db.add_permission(p)
        db.save_changes()

        por_codigo = {p.code: p.id for p in permisos}

        # Operador: puede leer y administrar roles
        db.add_role_permission(RolePermission(role_id=operador.id, permission_id=por_codigo["roles.read"]))
        db.add_role_permission(RolePermission(role_id=operador.id, permission_id=por_codigo["roles.write"]))

        # Capturista, lista inicial: accounts.read y concepts.read
        db.add_role_permission(RolePermission(role_id=capturista.id, permission_id=por_codigo["accounts.read"]))
        db.add_role_permission(RolePermission(role_id=capturista.id, permission_id=por_codigo["concepts.read"]))

        db.add_company_user_role(CompanyUserRole(company_user_id=membresia.id, role_id=operador.id))
        db.save_changes()

        return Datos(membresia.id, capturista.id, por_codigo)

    def test_Fallo_despues_del_flush_revierte_todas_las_relaciones(self):
        conexion = sqlite3.connect(":memory:", isolation_level=None)
        try:
            preparacion = self._opciones(conexion, con_fallo=False)
            preparacion.ensure_created()
            datos = self._sembrar(preparacion)

            # Lista deseada: activa accounts.write (alta) y desactiva concepts.read (baja).
            # Ambas escrituras llegan a la base antes del fallo.
            entrada = SetRolePermissionsInput(
                datos.rol_id,
                [datos.permisos["accounts.read"], datos.permisos["accounts.write"]],
            )

            ctx = self._opciones(conexion, con_fallo=True)
            mutacion = Mutation()

            with self.assertRaises(RuntimeError):
                mutacion.set_role_permissions_sync(entrada, datos.actor_id, ctx)

            # Verificación desde una sesión nueva
            verificacion = self._opciones(conexion, con_fallo=False)
            relaciones = verificacion.get_role_permissions_by_role(datos.rol_id, active_only=False)

            activos = sorted(
                rp.permission.code
                for rp in relaciones
                if rp.is_active and rp.permission is not None
            )

            self.assertEqual(["accounts.read", "concepts.read"], activos)
            self.assertFalse(any(rp.permission and rp.permission.code == "accounts.write" for rp in relaciones))
        finally:
            conexion.close()


if __name__ == "__main__":
    unittest.main()

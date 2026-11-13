import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "SistemaEmpresarial")))

import strawberry
from Acceso import AccessSeeder, JwtService
from Data import AppDbContext
from GraphQL import Mutation, Query


class GraphQLIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:", isolation_level=None)
        self.db = AppDbContext(self.conn)
        self.db.ensure_created()
        AccessSeeder.seed(self.db)
        self.cfg = {
            "Jwt": {
                "Key": "clave_secreta_desarrollo_sistema_empresarial_32chars",
                "Issuer": "SistemaEmpresarial",
                "Audience": "dashboard",
            }
        }
        self.schema = strawberry.Schema(query=Query, mutation=Mutation)

    def tearDown(self):
        self.conn.close()

    def _exec(self, query: str, variables: dict = None, token: str = None):
        claims = JwtService.validar(token, self.cfg) if token else None
        ctx = {"db": self.db, "config": self.cfg, "claims": claims}
        return self.schema.execute_sync(query, variable_values=variables or {}, context_value=ctx)

    def test_flujo_completo_dashboard_y_operaciones_graphql(self):
        # 1. Crear empresa y administrador
        r_comp = self._exec('mutation { createCompany(input: { name: "Empresa Demo" }) { id name } }')
        self.assertIsNone(r_comp.errors)
        company_id = r_comp.data["createCompany"]["id"]

        r_admin = self._exec(
            """
            mutation($cid: String!) {
              createAdmin(input: {
                companyId: $cid,
                name: "Admin Demo",
                email: "admin@demo.com",
                password: "password123"
              }) { id name email }
            }
            """,
            {"cid": company_id},
        )
        self.assertIsNone(r_admin.errors)

        # 2. Login como lo hace dashboard/index.html
        mut_login = """
        mutation Login($input: LoginInput!) {
          login(input: $input) { success message token tokenType }
        }
        """
        r_login = self._exec(mut_login, {"input": {"email": "admin@demo.com", "password": "password123"}})
        self.assertIsNone(r_login.errors)
        self.assertTrue(r_login.data["login"]["success"])
        token = r_login.data["login"]["token"]
        self.assertIsNotNone(token)

        claims = JwtService.validar(token, self.cfg)
        actor_id = claims["companyUserId"]

        # 3. Crear cuentas Banco, Caja, Ahorro y conceptos de ingreso/egreso
        accs = {}
        for nombre, tipo in [("Banco", "DEBIT"), ("Caja", "CASH"), ("Ahorro", "SAVINGS")]:
            res = self._exec(
                """
                mutation($actor: String!, $cid: String!, $name: String!, $type: AccountType!) {
                  createAccount(actorCompanyUserId: $actor, input: {
                    companyId: $cid, accountType: $type, name: $name
                  }) { id name }
                }
                """,
                {"actor": actor_id, "cid": company_id, "name": nombre, "type": tipo},
            )
            self.assertIsNone(res.errors)
            accs[nombre] = res.data["createAccount"]["id"]

        r_inc = self._exec(
            """
            mutation($actor: String!, $cid: String!) {
              createConcept(actorCompanyUserId: $actor, input: {
                companyId: $cid, conceptType: INCOME, name: "Ventas"
              }) { id }
            }
            """,
            {"actor": actor_id, "cid": company_id},
        )
        inc_id = r_inc.data["createConcept"]["id"]

        r_exp = self._exec(
            """
            mutation($actor: String!, $cid: String!) {
              createConcept(actorCompanyUserId: $actor, input: {
                companyId: $cid, conceptType: EXPENSE, name: "Gastos"
              }) { id }
            }
            """,
            {"actor": actor_id, "cid": company_id},
        )
        exp_id = r_exp.data["createConcept"]["id"]

        for acc_id in accs.values():
            for cid_concept in (inc_id, exp_id):
                res_assign = self._exec(
                    """
                    mutation($actor: String!, $aid: String!, $cid: String!) {
                      assignConceptToAccount(actorCompanyUserId: $actor, input: {
                        accountId: $aid, conceptId: $cid
                      }) { id isActive }
                    }
                    """,
                    {"actor": actor_id, "aid": acc_id, "cid": cid_concept},
                )
                self.assertIsNone(res_assign.errors)

        # 4. Registrar movimientos para replicar los valores esperados del README (26-30 oct 2026):
        # Banco: apertura 1000.00 (antes del 26 oct), ingresos 3000.00, egresos 2200.00 -> cierre 1800.00
        # Caja: apertura 0.00, ingresos 500.00, egresos 700.00 -> cierre -200.00 (en rojo)
        # Ahorro: sin movimientos -> cierre 0.00
        movimientos = [
            (accs["Banco"], inc_id, "INCOME", 1000.00, "2026-10-20T12:00:00Z"),
            (accs["Banco"], inc_id, "INCOME", 3000.00, "2026-10-27T12:00:00Z"),
            (accs["Banco"], exp_id, "EXPENSE", 2200.00, "2026-10-28T12:00:00Z"),
            (accs["Caja"], inc_id, "INCOME", 500.00, "2026-10-27T15:00:00Z"),
            (accs["Caja"], exp_id, "EXPENSE", 700.00, "2026-10-29T15:00:00Z"),
        ]
        for aid, cid_c, ttype, amt, tdate in movimientos:
            r_tx = self._exec(
                """
                mutation($actor: String!, $aid: String!, $cid: String!, $ttype: TransactionType!, $amt: Decimal!, $dt: DateTime!) {
                  createTransaction(actorCompanyUserId: $actor, input: {
                    accountId: $aid, conceptId: $cid, transactionType: $ttype, amount: $amt, transactionDate: $dt
                  }) { id amount }
                }
                """,
                {"actor": actor_id, "aid": aid, "cid": cid_c, "ttype": ttype, "amt": amt, "dt": tdate},
            )
            self.assertIsNone(r_tx.errors)

        # 5. Consultar miGeneralBalance exactamente como lo hace dashboard/index.html
        qry_balance = """
        query Indicadores($from: Date!, $to: Date!) {
          miGeneralBalance(fromDate: $from, toDate: $to) {
            fromDate toDate currency openingBalance totalIncome totalExpense
            profit closingBalance isInRed accountsInRed
            accounts { accountId accountName isActive openingBalance totalIncome totalExpense profit closingBalance isInRed }
          }
        }
        """
        r_bal = self._exec(qry_balance, {"from": "2026-10-26", "to": "2026-10-30"}, token=token)
        self.assertIsNone(r_bal.errors)
        b = r_bal.data["miGeneralBalance"]
        self.assertEqual("1000.00", b["openingBalance"])
        self.assertEqual("3500.00", b["totalIncome"])
        self.assertEqual("2900.00", b["totalExpense"])
        self.assertEqual("600.00", b["profit"])
        self.assertEqual("1600.00", b["closingBalance"])
        self.assertFalse(b["isInRed"])
        self.assertEqual(1, b["accountsInRed"])

        # 6. Consultar operaciones.graphql (ExplorarCatalogo)
        qry_catalogo = """
        query ExplorarCatalogo($actor: ID!) {
          cuentas: permissionCatalog(resource: ACCOUNTS, actorCompanyUserId: $actor) {
            id code name
          }
          movimientos: permissionCatalog(resource: TRANSACTIONS, actorCompanyUserId: $actor) {
            id code name
          }
        }
        """
        r_cat = self._exec(qry_catalogo, {"actor": actor_id})
        self.assertIsNone(r_cat.errors)
        self.assertEqual(2, len(r_cat.data["cuentas"]))
        self.assertEqual(2, len(r_cat.data["movimientos"]))


if __name__ == "__main__":
    unittest.main()

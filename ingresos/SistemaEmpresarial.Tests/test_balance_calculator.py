import os
import sys
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal

# Agregar SistemaEmpresarial al path para importar los módulos igual que ProjectReference
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "SistemaEmpresarial")))

from Balances import BalanceCalculator, BalancePeriodo, GraphQLException, SaldosCuenta
from Models import Account, AccountType


class BalanceCalculatorTests(unittest.TestCase):
    """
    Valores esperados escritos a mano a partir de los datos de entrada del enunciado.
    No se usa el servicio de balances para generar la respuesta esperada.
    """

    @staticmethod
    def _cuenta(acc_id: str, nombre: str) -> Account:
        return Account(
            id=acc_id,
            name=nombre,
            company_id="empresa-prueba",
            account_type=AccountType.DEBIT,
        )

    # B01: Banco, Caja y Ahorro del 26 al 30 de octubre
    def test_B01_BalanceGeneralCoincideConLaTablaDeReferencia(self):
        cuentas = [
            self._cuenta("banco", "Banco"),
            self._cuenta("caja", "Caja"),
            self._cuenta("ahorro", "Ahorro"),
        ]
        saldos = {
            "banco": SaldosCuenta(Decimal("1000.00"), Decimal("3000.00"), Decimal("2200.00")),
            "caja": SaldosCuenta(Decimal("0.00"), Decimal("500.00"), Decimal("700.00")),
        }

        general = BalanceCalculator.calcular_general(cuentas, saldos)

        banco = next(c for c in general.accounts if c.account_id == "banco")
        self.assertEqual(Decimal("1000.00"), banco.opening_balance)
        self.assertEqual(Decimal("800.00"), banco.profit)
        self.assertEqual(Decimal("1800.00"), banco.closing_balance)
        self.assertFalse(banco.is_in_red)

        caja = next(c for c in general.accounts if c.account_id == "caja")
        self.assertEqual(Decimal("-200.00"), caja.profit)
        self.assertEqual(Decimal("-200.00"), caja.closing_balance)
        self.assertTrue(caja.is_in_red)

        ahorro = next(c for c in general.accounts if c.account_id == "ahorro")
        self.assertEqual(Decimal("0.00"), ahorro.closing_balance)
        self.assertFalse(ahorro.is_in_red)

        self.assertEqual(Decimal("1000.00"), general.opening_balance)
        self.assertEqual(Decimal("3500.00"), general.total_income)
        self.assertEqual(Decimal("2900.00"), general.total_expense)
        self.assertEqual(Decimal("600.00"), general.profit)
        self.assertEqual(Decimal("1600.00"), general.closing_balance)
        self.assertFalse(general.is_in_red)
        self.assertEqual(1, general.accounts_in_red)

    # B02: Banco solo el 28 de octubre
    def test_B02_ProfitNegativoDelDiaNoImplicaSaldoFinalNegativo(self):
        cuentas = [self._cuenta("banco", "Banco")]
        saldos = {
            "banco": SaldosCuenta(Decimal("2800.00"), Decimal("0.00"), Decimal("1000.00")),
        }

        general = BalanceCalculator.calcular_general(cuentas, saldos)
        banco = general.accounts[0]

        self.assertEqual(Decimal("-1000.00"), banco.profit)
        self.assertEqual(Decimal("1800.00"), banco.closing_balance)
        self.assertFalse(banco.is_in_red)

    # B03: empresa sin cuentas
    def test_B03_EmpresaSinCuentasDevuelveCeros(self):
        general = BalanceCalculator.calcular_general([], {})

        self.assertEqual(0, len(general.accounts))
        self.assertEqual(Decimal("0.00"), general.closing_balance)
        self.assertEqual(0, general.accounts_in_red)
        self.assertFalse(general.is_in_red)

    # B06: 0.10 + 0.20 de ingresos y 0.30 de egresos en una cuenta vacía
    def test_B06_CentavosExactosNoQuedanEnRojo(self):
        cuentas = [self._cuenta("nueva", "Nueva")]
        saldos = {
            "nueva": SaldosCuenta(Decimal("0.00"), Decimal("0.10") + Decimal("0.20"), Decimal("0.30")),
        }

        general = BalanceCalculator.calcular_general(cuentas, saldos)
        cuenta = general.accounts[0]

        self.assertEqual(Decimal("0.00"), cuenta.profit)
        self.assertEqual(Decimal("0.00"), cuenta.closing_balance)
        self.assertFalse(cuenta.is_in_red)

    # B15 (parte de cálculo): egreso de 50.00 en cuenta vacía queda en -50.00 y en rojo
    def test_B15_EgresoEnCuentaVaciaQuedaEnRojo(self):
        cuentas = [self._cuenta("nueva", "Nueva")]
        saldos = {
            "nueva": SaldosCuenta(Decimal("0.00"), Decimal("0.00"), Decimal("50.00")),
        }

        general = BalanceCalculator.calcular_general(cuentas, saldos)

        self.assertEqual(Decimal("-50.00"), general.accounts[0].closing_balance)
        self.assertTrue(general.accounts[0].is_in_red)
        self.assertTrue(general.is_in_red)
        self.assertEqual(1, general.accounts_in_red)

    # B04: límites del período (inicio incluido, fin excluido)
    def test_B04_PeriodoUsaDiasCompletosUtc(self):
        inicio, fin = BalancePeriodo.calcular(
            date(2026, 10, 26),
            date(2026, 10, 30),
        )

        self.assertEqual(datetime(2026, 10, 26, 0, 0, 0, tzinfo=timezone.utc), inicio)
        self.assertEqual(datetime(2026, 10, 31, 0, 0, 0, tzinfo=timezone.utc), fin)

        # 25 23:59:59 queda antes del inicio; 26 00:00:00 entra; 30 23:59:59 entra; 31 00:00:00 queda fuera
        self.assertTrue(datetime(2026, 10, 25, 23, 59, 59, tzinfo=timezone.utc) < inicio)
        self.assertTrue(datetime(2026, 10, 26, 0, 0, 0, tzinfo=timezone.utc) >= inicio)
        self.assertTrue(datetime(2026, 10, 30, 23, 59, 59, tzinfo=timezone.utc) < fin)
        self.assertFalse(datetime(2026, 10, 31, 0, 0, 0, tzinfo=timezone.utc) < fin)

    # B10: fromDate posterior a toDate
    def test_B10_FechasInvertidasRechazan(self):
        with self.assertRaises(GraphQLException):
            BalancePeriodo.calcular(date(2026, 10, 30), date(2026, 10, 26))


if __name__ == "__main__":
    unittest.main()

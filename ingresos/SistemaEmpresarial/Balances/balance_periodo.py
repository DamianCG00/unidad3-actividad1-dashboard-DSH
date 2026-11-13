from datetime import date, datetime, time, timedelta, timezone
from typing import Tuple


class GraphQLException(Exception):
    """Excepción de negocio para operaciones GraphQL."""
    pass


class BalancePeriodo:
    """
    Convierte dos fechas de día completo (UTC) en límites de consulta:
    inicio incluido, fin excluido (medianoche del día siguiente a toDate).
    """

    @staticmethod
    def calcular(from_date: date, to_date: date) -> Tuple[datetime, datetime]:
        if from_date > to_date:
            raise GraphQLException("fromDate no puede ser posterior a toDate")

        inicio = datetime.combine(from_date, time.min, tzinfo=timezone.utc)
        fin = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=timezone.utc)

        return inicio, fin

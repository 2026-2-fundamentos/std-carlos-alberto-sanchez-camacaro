from collections import Counter

from ._records import read_records


def pregunta_04():
    """
    Cuente cuántos registros hay en cada mes, usando la fecha de la tercera
    columna (`date`). Represente el mes como un texto de dos dígitos y retorne
    una lista de tuplas `(mes, cantidad)` ordenada por el mes.

    Ejemplo del formato de la respuesta:

        [("01", 3), ("02", 4), ("03", 2), ...]
    """

    # El archivo contiene dias invalidos; solo se necesita el mes original.
    counts = Counter(record.date.split("-")[1] for record in read_records())
    return sorted(counts.items())

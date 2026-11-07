from collections import defaultdict

from ._records import read_records


def pregunta_05():
    """
    Para cada letra de la primera columna (`letter`), encuentre el valor
    máximo y el valor mínimo de la segunda columna (`value`). Retorne una lista
    de tuplas `(letra, máximo, mínimo)` ordenada alfabéticamente por la letra.

    Ejemplo del formato de la respuesta:

        [("A", 9, 2), ("B", 9, 1), ...]
    """

    values = defaultdict(list)
    for record in read_records():
        values[record.letter].append(record.value)
    return [(letter, max(group), min(group)) for letter, group in sorted(values.items())]

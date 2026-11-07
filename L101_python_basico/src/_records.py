"""Lectura de los registros del archivo comprimido de L101."""

import csv
import gzip
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "data.csv.gz"


class Record(NamedTuple):
    letter: str
    value: int
    date: str
    codes: tuple[str, ...]
    metrics: tuple[tuple[str, int], ...]


def read_records() -> Iterator[Record]:
    """Entregar registros tipados en el orden del archivo TSV, sin encabezado."""
    with gzip.open(DATA_FILE, mode="rt", encoding="utf-8", newline="") as source:
        rows = csv.reader(source, delimiter="\t")
        for letter, value, raw_date, codes, metrics in rows:
            metric_pairs = (pair.split(":", 1) for pair in metrics.split(",") if pair)
            yield Record(
                letter,
                int(value),
                raw_date,
                tuple(code for code in codes.split(",") if code),
                tuple((key, int(number)) for key, number in metric_pairs),
            )

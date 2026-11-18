"""Genera la entrega seudonimizada con DuckDB."""

import csv
from pathlib import Path

import duckdb


ACTIVITY = Path(__file__).resolve().parents[1]


def main() -> None:
    source = ACTIVITY / "data/raw.csv"
    output = ACTIVITY / "submission/anonymized.csv"
    query = Path(__file__).with_name("anonymize.sql").read_text(encoding="utf-8")
    with duckdb.connect() as db:
        db.read_csv(str(source), header=True, all_varchar=True).create_view("raw_customers")
        result = db.sql(query)
        rows = result.fetchall()
        if any(None in row for row in rows) or len({row[2] for row in rows}) != len(rows):
            raise ValueError("Perfiles incompletos o identificadores repetidos.")
        output.parent.mkdir(parents=True, exist_ok=True)
        # Materializar una vez para no volver a evaluar los UUID.
        with output.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file, lineterminator="\n")
            writer.writerow(result.columns)
            writer.writerows(rows)


if __name__ == "__main__":
    main()

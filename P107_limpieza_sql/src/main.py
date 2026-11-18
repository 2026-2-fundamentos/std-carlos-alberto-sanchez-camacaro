"""Limpieza de ventas en DuckDB y exportación del resultado."""

from pathlib import Path

import duckdb


ACTIVITY = Path(__file__).resolve().parents[1]


def main() -> None:
    source = ACTIVITY / "data/ventas.csv"
    output = ACTIVITY / "submission/ventas.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    query = Path(__file__).with_name("clean_sales.sql").read_text(encoding="utf-8")
    with duckdb.connect() as db:
        db.read_csv(str(source), header=True, all_varchar=True).create_view("raw_sales")
        db.sql(query).write_csv(str(output))


if __name__ == "__main__":
    main()

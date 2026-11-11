"""Normaliza el archivo de ventas de P106 con Pandas."""

from pathlib import Path

import pandas as pd


ACTIVITY_DIR = Path(__file__).resolve().parents[1]
COLUMNS = [
    "supplier_id", "supplier", "country", "city", "purchase_date",
    "amount", "discount", "weight", "units", "unit_price", "contact_email",
]
CITIES = {
    "bogot\u00e1": "Bogot\u00e1", "bogota": "Bogot\u00e1",
    "medell\u00edn": "Medell\u00edn", "medellin": "Medell\u00edn",
    "sop\u00f3": "Sop\u00f3", "sopo": "Sop\u00f3", "tenjo": "Tenjo",
}


def parse_money(values: pd.Series) -> pd.Series:
    """Convierte importes en COP, incluidos separadores de miles y sufijos K."""
    values = values.str.upper().str.replace(r"\s+|COP|\$", "", regex=True)
    in_thousands = values.str.endswith("K", na=False)
    numbers = (
        values.str.removesuffix("K")
        .str.replace(",", "", regex=False)
        .str.replace(r"\.(?=\d{3}(?:\.|$))", "", regex=True)
    )
    return pd.to_numeric(numbers, errors="coerce").mul(
        in_thousands.map({True: 1000, False: 1})
    )


def parse_dates(values: pd.Series) -> pd.Series:
    """Prioriza dia/mes cuando es ambiguo; conserva el orden de fechas ISO."""
    year_first = values.str.match(r"\d{4}[-/]", na=False)
    iso = pd.to_datetime(
        values.where(year_first).str.replace("/", "-", regex=False),
        format="%Y-%m-%d",
        errors="coerce",
    )
    local = pd.to_datetime(
        values.mask(year_first), format="mixed", dayfirst=True, errors="coerce"
    )
    return iso.fillna(local).dt.strftime("%Y-%m-%d")


def clean_sales(raw: pd.DataFrame) -> pd.DataFrame:
    """Normaliza las ventas y elimina solo las filas completamente duplicadas."""
    sales = raw.rename(columns=lambda name: "_".join(name.lower().split()))
    sales = sales.loc[:, COLUMNS].astype("string").apply(lambda col: col.str.strip())
    sales = sales.replace({"": pd.NA, "N/A": pd.NA})

    sales["supplier"] = sales["supplier"].str.replace(r"\s+", " ", regex=True)
    sales["country"] = sales["country"].str.upper().replace(
        {"CO": "COL", "COLOMBIA": "COL"}
    )
    sales["city"] = sales["city"].str.casefold().replace(CITIES)
    sales["purchase_date"] = parse_dates(sales["purchase_date"])
    sales["amount"] = parse_money(sales["amount"])

    discount = sales["discount"]
    percent = discount.str.endswith("%", na=False)
    rate = pd.to_numeric(discount.str.removesuffix("%"), errors="coerce")
    rate = rate.mask(percent | rate.gt(1), rate / 100)
    sales["discount"] = rate.where(rate.between(0, 1))

    weight = sales["weight"].str.lower().str.replace(",", ".", regex=False)
    parts = weight.str.extract(r"^(?P<value>-?\d+(?:\.\d+)?)\s*(?P<unit>kg|g|ton)?$")
    factors = parts["unit"].fillna("kg").map({"kg": 1, "g": 0.001, "ton": 1000})
    kilos = pd.to_numeric(parts["value"], errors="coerce") * factors
    sales["weight"] = kilos.where(kilos.ge(0))

    sales["units"] = pd.to_numeric(sales["units"], errors="coerce").astype("Int64")
    unit_price = parse_money(sales["unit_price"])
    # Un precio unitario negativo se deja vacio, sin inferir un valor sustituto.
    sales["unit_price"] = unit_price.where(unit_price.ge(0))
    sales["contact_email"] = (
        sales["contact_email"].str.lower().replace("sin correo", pd.NA)
    )
    # Compare supplier names without case, retaining the first spelling.
    duplicate = sales.assign(supplier=sales["supplier"].str.casefold()).duplicated()
    return sales.loc[~duplicate].reset_index(drop=True)


def main() -> None:
    raw = pd.read_csv(ACTIVITY_DIR / "data" / "ventas.csv", dtype="string")
    destination = ACTIVITY_DIR / "submission" / "ventas.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    clean_sales(raw).to_csv(destination, index=False)


if __name__ == "__main__":
    main()

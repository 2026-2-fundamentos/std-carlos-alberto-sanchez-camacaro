"""Genera la entrega de P108 con identificadores enmascarados y agrupados."""

from pathlib import Path
from secrets import token_hex

import pandas as pd


ACTIVITY_DIR = Path(__file__).resolve().parents[1]
REGIONS = {
    "Andina": (
        "Bello", "Bogot\u00e1", "Bucaramanga", "Envigado", "Itag\u00fc\u00ed",
        "Manizales", "Medell\u00edn", "Pereira", "Rionegro",
    ),
    "Caribe": ("Barranquilla", "Cartagena"),
    "Pac\u00edfica": ("Cali",),
}
OCCUPATION_GROUPS = {
    "Comercio y oficios": ("Comerciante", "T\u00e9cnico electricista"),
    "Salud y educaci\u00f3n": ("Docente", "Enfermera", "M\u00e9dico"),
    "Servicios profesionales": (
        "Abogada", "Administradora", "Analista financiera", "Contadora",
    ),
    "Tecnolog\u00eda y dise\u00f1o": (
        "Arquitecta", "Dise\u00f1adora gr\u00e1fica", "Ingeniero de sistemas",
    ),
}
PROFILE_COLUMNS = ["age_group", "region", "occupation_group"]


def generalize_profiles(data: pd.DataFrame) -> pd.DataFrame:
    """Agrupa los cuasi-identificadores que comparten los dos archivos."""
    ages = pd.cut(
        data["age"],
        bins=[20, 30, 40, 50, 60, 70],
        labels=["20-29", "30-39", "40-49", "50-59", "60-69"],
        right=False,
    ).astype("string")
    cities = {city: region for region, items in REGIONS.items() for city in items}
    jobs = {job: group for group, items in OCCUPATION_GROUPS.items() for job in items}
    profiles = pd.DataFrame({
        "age_group": ages,
        "region": data["city"].map(cities),
        "occupation_group": data["occupation"].map(jobs),
    })
    if profiles.isna().any().any():
        raise ValueError("Hay perfiles con edades, ciudades u ocupaciones no reconocidas.")
    return profiles


def new_customer_ids(count: int) -> list[str]:
    """Crea identificadores aleatorios sin usar datos personales como semilla."""
    ids = {}
    while len(ids) < count:
        ids[f"CUST-{token_hex(6).upper()}"] = None
    return list(ids)


def anonymize(data: pd.DataFrame) -> pd.DataFrame:
    """Proyecta solo las columnas autorizadas, en el orden de la actividad."""
    cards = data["loyalty_card_number"].astype("string").str.zfill(12)
    if not cards.str.fullmatch(r"\d{12}").fillna(False).all():
        raise ValueError("Las tarjetas deben contener hasta doce digitos.")
    masked = pd.DataFrame({
        "loyalty_card_number": "********" + cards.str[-4:],
        "annual_spend": data["annual_spend"],
        "customer_id": new_customer_ids(len(data)),
    }, index=data.index)
    return pd.concat([masked, generalize_profiles(data)], axis=1)


def main() -> None:
    raw = pd.read_csv(
        ACTIVITY_DIR / "data/raw.csv", dtype={"loyalty_card_number": "string"}
    )
    output = ACTIVITY_DIR / "submission/anonymized.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    anonymize(raw).to_csv(output, index=False)


if __name__ == "__main__":
    main()

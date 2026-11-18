"""Entrena y compara modelos de regresión para el consumo de combustible."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, PolynomialFeatures, StandardScaler


ACTIVITY = Path(__file__).resolve().parents[1]
NUMERIC = ["Cylinders", "Displacement", "Horsepower", "Weight", "Acceleration", "Model Year"]
CATEGORICAL = ["Origin"]
SEED = 42


def build_preprocessor(degree: int) -> ColumnTransformer:
    """Imputa y escala numéricas; codifica el origen como categoría."""
    numeric = [SimpleImputer(strategy="median"), StandardScaler()]
    if degree > 1:
        numeric.append(PolynomialFeatures(degree=degree, include_bias=False))
    return ColumnTransformer([
        ("numeric", make_pipeline(*numeric), NUMERIC),
        ("origin", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
    ])


def load_split():
    data = pd.read_csv(ACTIVITY / "data/auto_mpg.csv", na_values=["?"])
    return train_test_split(
        data[NUMERIC + CATEGORICAL], data["MPG"], test_size=0.2, random_state=SEED
    )


def main() -> pd.DataFrame:
    x_train, x_test, y_train, y_test = load_split()
    basic = build_preprocessor(degree=1)
    flexible = build_preprocessor(degree=2)
    basic_train, basic_test = basic.fit_transform(x_train), basic.transform(x_test)
    flex_train, flex_test = flexible.fit_transform(x_train), flexible.transform(x_test)

    linear_basic = LinearRegression().fit(basic_train, y_train)
    linear_flexible = LinearRegression().fit(flex_train, y_train)
    mlp = MLPRegressor(
        hidden_layer_sizes=(32, 16),
        max_iter=2000,
        early_stopping=True,
        n_iter_no_change=30,
        random_state=SEED,
    ).fit(basic_train, y_train)

    scores = []
    for name, model, features in (
        ("linear_baseline", linear_basic, basic_test),
        ("linear_flexible", linear_flexible, flex_test),
        ("mlp", mlp, basic_test),
    ):
        predictions = model.predict(features)
        scores.append({
            "model": name,
            "mae": mean_absolute_error(y_test, predictions),
            "rmse": np.sqrt(mean_squared_error(y_test, predictions)),
            "r2": r2_score(y_test, predictions),
        })

    comparison = pd.DataFrame(scores)
    output = ACTIVITY / "submission"
    output.mkdir(parents=True, exist_ok=True)
    for name, fitted in (
        ("features_preprocessor", basic),
        ("flexible_features_preprocessor", flexible),
        ("linear_flexible_model", linear_flexible),
        ("mlp", mlp),
    ):
        joblib.dump(fitted, output / f"{name}.pkl")
    comparison.to_csv(output / "model_comparison.csv", index=False)
    return comparison


if __name__ == "__main__":
    print(main().to_string(index=False))

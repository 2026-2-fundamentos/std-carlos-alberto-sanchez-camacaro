"""Verifica la particion y el comportamiento de los artefactos entrenados."""

import json
import runpy
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, f1_score


ACTIVITY = Path(__file__).resolve().parents[1]
MODULE = runpy.run_path(str(ACTIVITY / "src/main.py"))


def test_split_has_no_shared_phrases():
    train, test, train_y, test_y = MODULE["load_split"]()
    assert set(train.str.casefold()).isdisjoint(test.str.casefold())
    assert len(train) + len(test) == 2259
    assert set(train_y) == set(test_y) == set(MODULE["LABELS"])


def test_saved_model_reproduces_reported_scores():
    _, test, _, labels = MODULE["load_split"]()
    output = ACTIVITY / "submission"
    clf = joblib.load(output / "clf.pkl")
    vectorizer = joblib.load(output / "vectorizer.pkl")
    metrics = json.loads((output / "metrics.json").read_text(encoding="utf-8"))
    predictions = clf.predict(vectorizer.transform(test))
    assert set(predictions) <= set(MODULE["LABELS"])
    np.testing.assert_allclose(
        accuracy_score(labels, predictions), metrics["test"]["accuracy"]
    )
    np.testing.assert_allclose(
        f1_score(labels, predictions, average="macro"), metrics["test"]["f1_macro"]
    )
    assert metrics["test"]["f1_macro"] > metrics["baseline"]["f1_macro"]

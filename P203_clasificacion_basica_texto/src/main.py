"""Clasificacion de sentimiento con TF-IDF y SVM lineal."""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC


ACTIVITY_DIR = Path(__file__).resolve().parents[1]
LABELS = ["negative", "neutral", "positive"]
SEED = 42


def load_split():
    """Evita que una misma frase aparezca en entrenamiento y prueba."""
    data = pd.read_csv(ACTIVITY_DIR / "data/sentences.csv.gz")
    data["phrase"] = data["phrase"].str.replace(r"\s+", " ", regex=True).str.strip()
    data["key"] = data["phrase"].str.casefold()
    if data[["phrase", "target"]].isna().any().any():
        raise ValueError("Hay frases o etiquetas ausentes.")
    if not data["target"].isin(LABELS).all() or data["phrase"].eq("").any():
        raise ValueError("Frases vacias o etiquetas desconocidas.")
    if data.groupby("key")["target"].nunique().gt(1).any():
        raise ValueError("Una misma frase tiene etiquetas contradictorias.")
    data = data.drop_duplicates("key")
    return train_test_split(
        data["phrase"], data["target"],
        test_size=0.2, stratify=data["target"], random_state=SEED,
    )


def evaluate(actual, predicted):
    return {
        "accuracy": accuracy_score(actual, predicted),
        "f1_macro": f1_score(actual, predicted, labels=LABELS, average="macro"),
        "confusion_matrix": confusion_matrix(actual, predicted, labels=LABELS).tolist(),
        "classification_report": classification_report(
            actual, predicted, labels=LABELS, output_dict=True, zero_division=0
        ),
    }


def main():
    train_text, test_text, train_y, test_y = load_split()
    vectorizer = TfidfVectorizer(
        lowercase=True, strip_accents="unicode", ngram_range=(1, 2),
        min_df=2, sublinear_tf=True,
    )
    # El vocabulario y los pesos IDF se aprenden exclusivamente del entrenamiento.
    train_x = vectorizer.fit_transform(train_text)
    test_x = vectorizer.transform(test_text)
    clf = LinearSVC(class_weight="balanced", random_state=SEED, dual="auto")
    clf.fit(train_x, train_y)
    predicted = clf.predict(test_x)
    baseline = DummyClassifier(strategy="most_frequent").fit(train_x, train_y)
    metrics = {
        "model": "TF-IDF + LinearSVC",
        "random_state": SEED,
        "train_size": len(train_y),
        "test_size": len(test_y),
        "labels": LABELS,
        "test": evaluate(test_y, predicted),
        "baseline": evaluate(test_y, baseline.predict(test_x)),
    }
    output = ACTIVITY_DIR / "submission"
    output.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, output / "vectorizer.pkl")
    joblib.dump(clf, output / "clf.pkl")
    (output / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return metrics


if __name__ == "__main__":
    results = main()
    print(json.dumps({key: results[key] for key in ("train_size", "test_size")}))
    print("F1 macro:", results["test"]["f1_macro"])
    print("F1 macro de referencia:", results["baseline"]["f1_macro"])

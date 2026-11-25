"""Agrupa perfiles horarios de demanda y clasifica un dia reservado."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from threadpoolctl import threadpool_limits


ACTIVITY = Path(__file__).resolve().parents[1]
HOURS = [f"H{hour:02d}" for hour in range(1, 25)]
SEED = 42


def load_data():
    data = pd.read_csv(ACTIVITY / "data/demanda_comercial.csv.gz")
    data["Fecha"] = pd.to_datetime(data["Fecha"], errors="raise")
    data = data.sort_values("Fecha").reset_index(drop=True)
    values = data[HOURS].to_numpy(dtype=float)
    if data["Fecha"].duplicated().any() or not np.isfinite(values).all():
        raise ValueError("Fechas repetidas o mediciones no finitas.")
    if (values < 0).any() or (values.mean(axis=1) <= 0).any():
        raise ValueError("La demanda debe ser no negativa y tener media positiva.")
    return data


def normalize(values):
    return values / values.mean(axis=1, keepdims=True)


def save_figure(fig, output, filename):
    fig.tight_layout()
    fig.savefig(output / filename, dpi=150)
    plt.close(fig)


def main():
    data = load_data()
    train, received = data.iloc[:-1], data.iloc[-1:]
    x = normalize(train[HOURS].to_numpy(dtype=float))
    output = ACTIVITY / "submission"
    output.mkdir(parents=True, exist_ok=True)
    models, scores = {}, []
    # Limita los hilos para evitar sobrecarga en matrices pequenas.
    with threadpool_limits(limits=1):
        for k in range(2, 9):
            model = KMeans(n_clusters=k, n_init=20, random_state=SEED).fit(x)
            models[k] = model
            scores.append({
                "n_clusters": k, "inertia": model.inertia_,
                "silhouette": silhouette_score(
                    x, model.labels_, sample_size=min(1000, len(x)), random_state=SEED
                ),
            })
    selection = pd.DataFrame(scores)
    best_k = int(selection.sort_values(
        ["silhouette", "n_clusters"], ascending=[False, True]
    ).iloc[0]["n_clusters"])
    selection["selected"] = selection.n_clusters.eq(best_k)
    selection.to_csv(output / "cluster-selection.csv", index=False)
    model = models[best_k]

    days = train.copy()
    days["cluster"] = model.labels_
    days["daily_mean"] = train[HOURS].mean(axis=1)
    days["day_of_week"] = days.Fecha.dt.dayofweek
    days.to_csv(output / "demanda-comercial-dias.csv", index=False, date_format="%Y-%m-%d")

    centers = pd.DataFrame(model.cluster_centers_, columns=HOURS)
    centers.insert(0, "cluster", range(best_k))
    centers["n_days"] = np.bincount(model.labels_, minlength=best_k)
    centers.to_csv(output / "demanda-comercial-clusters.csv", index=False)

    profile = normalize(received[HOURS].to_numpy(dtype=float))
    distances = model.transform(profile)
    prediction = received.copy()
    prediction["cluster"] = model.predict(profile)
    prediction["distance_to_center"] = distances.min(axis=1)
    prediction.to_csv(output / "perfil-recibido.csv", index=False, date_format="%Y-%m-%d")

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(data.Fecha, data[HOURS].mean(axis=1), linewidth=0.7)
    ax.set(title="Demanda media diaria", xlabel="Fecha", ylabel="Demanda (unidad del archivo)")
    save_figure(fig, output, "demanda-comercial.png")

    hours = np.arange(1, 25)
    fig, ax = plt.subplots(figsize=(10, 5))
    for cluster in range(best_k):
        ax.plot(hours, model.cluster_centers_[cluster],
                label=f"Grupo {cluster} (n={centers.loc[cluster, 'n_days']})")
    ax.set(title="Perfiles medios por grupo", xlabel="Hora", ylabel="Demanda / media diaria",
           xticks=range(1, 25, 2))
    ax.legend()
    save_figure(fig, output, "demanda-comercial-perfiles.png")

    fig, axes = plt.subplots(best_k, 1, figsize=(10, 3 * best_k), squeeze=False)
    for cluster, ax in enumerate(axes[:, 0]):
        indices = np.flatnonzero(model.labels_ == cluster)
        for index in indices[:3]:
            ax.plot(hours, x[index], alpha=0.6, label=str(train.iloc[index].Fecha.date()))
        ax.plot(hours, model.cluster_centers_[cluster], color="black",
                linestyle="--", label="Centro")
        ax.set(title=f"Ejemplos del grupo {cluster}", xlabel="Hora", ylabel="Demanda relativa")
        ax.legend(fontsize=8)
    save_figure(fig, output, "demanda-comercial-patrones-ejemplo.png")
    return selection


if __name__ == "__main__":
    print(main().to_string(index=False))

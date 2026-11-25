"""Valida los resultados del agrupamiento, ademas de su existencia."""

from pathlib import Path

import matplotlib.image as mpimg
import numpy as np
import pandas as pd


ACTIVITY = Path(__file__).resolve().parents[1]
OUTPUT = ACTIVITY / "submission"
HOURS = [f"H{i:02d}" for i in range(1, 25)]


def test_selection_uses_maximum_silhouette():
    selection = pd.read_csv(OUTPUT / "cluster-selection.csv")
    assert selection.n_clusters.tolist() == list(range(2, 9))
    assert selection.selected.sum() == 1
    assert selection.silhouette.between(-1, 1).all()
    best = selection.sort_values(
        ["silhouette", "n_clusters"], ascending=[False, True]
    ).iloc[0]
    assert best.selected


def test_profiles_match_assigned_days_and_received_is_separate():
    raw = pd.read_csv(ACTIVITY / "data/demanda_comercial.csv.gz").sort_values("Fecha")
    days = pd.read_csv(OUTPUT / "demanda-comercial-dias.csv")
    centers = pd.read_csv(OUTPUT / "demanda-comercial-clusters.csv")
    received = pd.read_csv(OUTPUT / "perfil-recibido.csv")
    assert days.Fecha.tolist() == raw.Fecha.iloc[:-1].tolist()
    pd.testing.assert_frame_equal(days[HOURS], raw.iloc[:-1][HOURS].reset_index(drop=True))
    assert received.Fecha.tolist() == raw.Fecha.iloc[-1:].tolist()
    assert not set(days.Fecha) & set(received.Fecha)
    assert centers.n_days.sum() == len(days)
    values = days[HOURS].to_numpy()
    normalized = values / values.mean(axis=1, keepdims=True)
    for _, center in centers.iterrows():
        assigned = normalized[days.cluster.eq(center.cluster)]
        assert len(assigned) == center.n_days
        np.testing.assert_allclose(assigned.mean(axis=0), center[HOURS].to_numpy(float))
    profile = received[HOURS].to_numpy()
    profile /= profile.mean(axis=1, keepdims=True)
    distances = np.linalg.norm(centers[HOURS].to_numpy() - profile, axis=1)
    assert received.cluster.iloc[0] == centers.cluster.iloc[distances.argmin()]
    np.testing.assert_allclose(received.distance_to_center.iloc[0], distances.min())


def test_figures_are_readable_images():
    for filename in (
        "demanda-comercial.png", "demanda-comercial-perfiles.png",
        "demanda-comercial-patrones-ejemplo.png",
    ):
        image = mpimg.imread(OUTPUT / filename)
        assert image.shape[0] >= 300 and image.shape[1] >= 600

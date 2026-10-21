from datetime import datetime, timezone

import pandas as pd

from src.processing.cleaner import clean_focos
from src.processing.priority import aggregate_by_municipio, calculate_priority

NOW = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)


def test_clean_focos_strips_spaces_and_converts_types():
    raw = pd.DataFrame(
        {
            "id": ["a", "b"],
            "lat": ["  -1.901000", "abc"],
            "lon": [" -52.858000", " -50.0"],
            "data_hora_gmt": ["2026-10-21 00:00:00", "2026-10-21 01:00:00"],
            "municipio": [" PORTO DE MOZ ", "X"],
            "frp": ["108.5", ""],
        }
    )
    df = clean_focos(raw)

    assert len(df) == 1  # linha com lat inválida removida
    assert df.loc[0, "lat"] == -1.901
    assert df.loc[0, "municipio"] == "PORTO DE MOZ"
    assert str(df["data_hora_gmt"].dt.tz) == "UTC"


def _focos(municipio, n, horas_atras, frp=50.0):
    ts = pd.Timestamp(NOW) - pd.Timedelta(hours=horas_atras)
    return [
        {"id": f"{municipio}-{horas_atras}-{i}", "estado": "PA", "municipio": municipio,
         "data_hora_gmt": ts, "frp": frp, "risco_fogo": 1.0, "lat": -1.0, "lon": -50.0}
        for i in range(n)
    ]


def test_aggregate_respects_window():
    df = pd.DataFrame(_focos("A", 3, 2) + _focos("A", 5, 30))
    assert aggregate_by_municipio(df, 24, now=NOW).loc[0, "focos"] == 3
    assert aggregate_by_municipio(df, 48, now=NOW).loc[0, "focos"] == 8


def test_single_hot_foco_does_not_beat_many_focos():
    df = pd.DataFrame(
        _focos("GRANDE", 100, 2, frp=30.0)
        + _focos("GRANDE", 20, 30, frp=30.0)
        + _focos("ISOLADO", 1, 2, frp=300.0)
        + _focos("ISOLADO", 1, 30, frp=300.0)
    )
    ranking = calculate_priority(aggregate_by_municipio(df, 24, now=NOW), aggregate_by_municipio(df, 48, now=NOW))

    assert ranking.loc[0, "municipio"] == "GRANDE"
    assert ranking["prioridade"].max() <= 100


def test_persistence_bonus():
    df = pd.DataFrame(_focos("A", 10, 2) + _focos("A", 5, 30) + _focos("B", 10, 2))
    ranking = calculate_priority(aggregate_by_municipio(df, 24, now=NOW), aggregate_by_municipio(df, 48, now=NOW))
    scores = ranking.set_index("municipio")["score_persistencia"]

    assert scores["A"] == 15
    assert scores["B"] == 0

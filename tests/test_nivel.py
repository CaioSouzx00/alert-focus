from datetime import datetime, timezone

import pandas as pd

from src.processing.priority import aggregate_by_municipio, calculate_priority, classify_nivel

NOW = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)


def _focos(municipio, n, horas_atras):
    ts = pd.Timestamp(NOW) - pd.Timedelta(hours=horas_atras)
    return [
        {"id": f"{municipio}-{i}", "estado": "PA", "municipio": municipio,
         "data_hora_gmt": ts, "frp": 50.0, "risco_fogo": 1.0, "lat": -1.0, "lon": -50.0}
        for i in range(n)
    ]


def test_classify_nivel_thresholds():
    assert classify_nivel(100) == "Crítico"
    assert classify_nivel(99) == "Alto"
    assert classify_nivel(40) == "Alto"
    assert classify_nivel(39) == "Médio"
    assert classify_nivel(15) == "Médio"
    assert classify_nivel(14) == "Baixo"
    assert classify_nivel(0) == "Baixo"


def test_ranking_has_nivel_and_centroid():
    df = pd.DataFrame(_focos("GRANDE", 120, 2) + _focos("PEQUENO", 3, 2))
    ranking = calculate_priority(aggregate_by_municipio(df, 24, now=NOW), aggregate_by_municipio(df, 48, now=NOW))
    by_muni = ranking.set_index("municipio")

    assert by_muni.loc["GRANDE", "nivel"] == "Crítico"
    assert by_muni.loc["PEQUENO", "nivel"] == "Baixo"
    assert by_muni.loc["GRANDE", "lat"] == -1.0

"""Pipeline completo: baixa os últimos dias, limpa, agrega e calcula prioridade."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.ingestion.inpe_downloader import download_recent_csvs
from src.processing.cleaner import load_and_clean_many
from src.processing.priority import aggregate_by_municipio, calculate_priority

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main() -> None:
    raw_dir = ROOT / "data" / "raw"
    processed_dir = ROOT / "data" / "processed"

    paths = download_recent_csvs(raw_dir, days_back=3)
    if not paths:
        logging.error("Nenhum CSV disponível. Pipeline abortado.")
        sys.exit(1)

    df = load_and_clean_many(paths)
    agg_24 = aggregate_by_municipio(df, hours=24)
    agg_48 = aggregate_by_municipio(df, hours=48)
    ranking = calculate_priority(agg_24, agg_48)

    if ranking.empty:
        logging.error("Ranking vazio (sem focos nas últimas 24h).")
        sys.exit(1)

    processed_dir.mkdir(parents=True, exist_ok=True)
    out = processed_dir / "ranking_municipios.csv"
    ranking.to_csv(out, index=False, encoding="utf-8")
    logging.info("Ranking salvo em %s (%d municípios)", out, len(ranking))

    cols = ["estado", "municipio", "focos", "focos_48h", "frp_medio", "prioridade"]
    pd.set_option("display.width", 160)
    print(ranking[[c for c in cols if c in ranking.columns]].head(15).to_string())


if __name__ == "__main__":
    main()

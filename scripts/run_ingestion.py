"""Ponto de entrada da ingestão de dados do INPE (download dos últimos dias)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Garante que o pacote src seja encontrado
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ingestion.inpe_downloader import download_recent_csvs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def main() -> None:
    raw_dir = ROOT / "data" / "raw"
    paths = download_recent_csvs(raw_dir, days_back=3)

    if not paths:
        logging.error("Ingestão falhou.")
        sys.exit(1)

    logging.info("Ingestão OK → %d arquivo(s): %s", len(paths), ", ".join(p.name for p in paths))


if __name__ == "__main__":
    main()

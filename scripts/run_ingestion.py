"""Ponto de entrada da ingestão de dados do INPE."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Garante que o pacote src seja encontrado
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ingestion.inpe_downloader import download_latest_csv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def main() -> None:
    raw_dir = ROOT / "data" / "raw"
    path = download_latest_csv(raw_dir)

    if path is None:
        logging.error("Ingestão falhou.")
        sys.exit(1)

    logging.info("Ingestão OK → %s", path)


if __name__ == "__main__":
    main()

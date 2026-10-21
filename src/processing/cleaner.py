"""
Limpeza e padronização dos CSVs de focos do INPE.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Colunas que queremos manter e seus tipos esperados
USEFUL_COLUMNS = [
    "id",
    "lat",
    "lon",
    "data_hora_gmt",
    "satelite",
    "municipio",
    "estado",
    "bioma",
    "frp",
    "risco_fogo",
    "numero_dias_sem_chuva",
    "precipitacao",
]

TEXT_COLUMNS = ("id", "satelite", "municipio", "estado", "bioma")
NUMERIC_COLUMNS = ("frp", "risco_fogo", "numero_dias_sem_chuva", "precipitacao")


def read_inpe_csv(path: Path) -> pd.DataFrame:
    """
    Lê um CSV do INPE tratando encoding.
    Tenta utf-8 primeiro (formato atual do INPE); se falhar, usa cp1252/latin-1.
    """
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            df = pd.read_csv(
                path,
                encoding=encoding,
                dtype=str,          # lê tudo como string primeiro
                low_memory=False,
            )
            logger.info("Lido %s com encoding %s (%d linhas)", path.name, encoding, len(df))
            return df
        except UnicodeDecodeError:
            continue

    raise ValueError(f"Não consegui ler {path} com encodings comuns")


def clean_focos(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza colunas, remove espaços e converte tipos."""
    # Normaliza nomes de colunas (remove espaços extras)
    df.columns = df.columns.str.strip().str.lower()

    # Mantém só as colunas úteis que existem
    available = [c for c in USEFUL_COLUMNS if c in df.columns]
    df = df[available].copy()

    # Texto: remove espaços nas pontas
    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].str.strip()

    # Remove espaços em lat/lon e converte
    for col in ("lat", "lon"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.strip(), errors="coerce")

    # data_hora_gmt → datetime (UTC)
    if "data_hora_gmt" in df.columns:
        df["data_hora_gmt"] = pd.to_datetime(df["data_hora_gmt"], errors="coerce", utc=True)

    # Números
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.strip(), errors="coerce")

    # Remove linhas sem lat/lon válidos
    before = len(df)
    df = df.dropna(subset=["lat", "lon"])
    after = len(df)
    if before != after:
        logger.info("Removidas %d linhas sem coordenadas válidas", before - after)

    return df


def load_and_clean_many(paths: list[Path]) -> pd.DataFrame:
    """Lê e limpa vários CSVs e concatena."""
    frames = []
    for path in paths:
        raw = read_inpe_csv(path)
        clean = clean_focos(raw)
        frames.append(clean)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    # Remove duplicatas pelo id (caso o mesmo foco apareça em mais de um arquivo)
    if "id" in df.columns:
        df = df.drop_duplicates(subset=["id"], keep="last")

    logger.info("Total de focos após limpeza: %d", len(df))
    return df

"""
Agregação por município e cálculo de score de prioridade.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import pandas as pd

logger = logging.getLogger(__name__)

# Pesos do score (ADR 002) — somam 100
PESO_FOCOS = 60
PESO_FRP = 25
PESO_PERSISTENCIA = 15
# Focos mínimos para o bônus de FRP valer por inteiro (evidence factor)
MIN_FOCOS_FRP = 10

# Níveis por limiares ABSOLUTOS de focos em 24h (ADR 002), do mais alto ao mais baixo.
# Cada tupla é (mínimo de focos, nome do nível).
LIMIARES_NIVEL = ((100, "Crítico"), (40, "Alto"), (15, "Médio"))
NIVEL_PADRAO = "Baixo"
ORDEM_NIVEIS = [NIVEL_PADRAO, "Médio", "Alto", "Crítico"]  # do menor para o maior


def classify_nivel(focos_24h: float) -> str:
    """Classifica um município pelo número de focos em 24h (limiares absolutos)."""
    for minimo, nome in LIMIARES_NIVEL:
        if focos_24h >= minimo:
            return nome
    return NIVEL_PADRAO


def aggregate_by_municipio(
    df: pd.DataFrame, hours: int = 24, now: datetime | None = None
) -> pd.DataFrame:
    """
    Conta focos por município nas últimas `hours` horas.
    `now` existe para tornar o cálculo testável (padrão: agora, em UTC).
    """
    if df.empty or "data_hora_gmt" not in df.columns:
        return pd.DataFrame()

    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours)
    recent = df[df["data_hora_gmt"] >= cutoff].copy()

    if recent.empty:
        logger.warning("Nenhum foco nas últimas %d horas", hours)
        return pd.DataFrame()

    agg = (
        recent.groupby(["estado", "municipio"], dropna=False)
        .agg(
            focos=("id", "count"),
            frp_medio=("frp", "mean"),
            frp_max=("frp", "max"),
            risco_medio=("risco_fogo", "mean"),
            ultimo_foco=("data_hora_gmt", "max"),
            lat=("lat", "mean"),  # centróide dos focos (usado no mapa)
            lon=("lon", "mean"),
        )
        .reset_index()
    )

    return agg


def calculate_priority(agg_24h: pd.DataFrame, agg_48h: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Score simples e explicável (0–100).

    Fórmula atual (ADR 002):
    - Base: quantidade de focos em 24h (até 60 pontos, relativo ao município com mais focos)
    - Bônus: FRP médio (até 25 pontos, relativo ao maior FRP médio)
    - Bônus: persistência, 15 pontos se também houve focos entre 24h e 48h atrás
    """
    if agg_24h.empty:
        return agg_24h

    df = agg_24h.copy()

    # Normalização simples (relativa ao máximo do dia; pode ajustar depois)
    max_focos = df["focos"].max()
    max_focos = max_focos if max_focos and max_focos > 0 else 1
    df["score_focos"] = (df["focos"] / max_focos) * PESO_FOCOS

    # FRP (se existir). NaN não pode virar divisor, por isso fillna antes do max.
    # O bônus é proporcional à evidência: min(focos / MIN_FOCOS_FRP, 1). Assim, um único
    # foco com FRP alto não ultrapassa municípios com centenas de focos.
    # O máximo de referência considera só municípios com evidência suficiente.
    if "frp_medio" in df.columns:
        frp = df["frp_medio"].fillna(0)
        elegiveis = frp[df["focos"] >= MIN_FOCOS_FRP]
        max_frp = elegiveis.max() if not elegiveis.empty else frp.max()
        max_frp = max_frp if max_frp > 0 else 1
        confianca = (df["focos"] / MIN_FOCOS_FRP).clip(upper=1)
        df["score_frp"] = (frp / max_frp).clip(upper=1) * PESO_FRP * confianca
    else:
        df["score_frp"] = 0

    # Persistência: houve focos no período 24h–48h (focos_48h inclui os de 24h)
    if agg_48h is not None and not agg_48h.empty:
        persist = agg_48h[["estado", "municipio", "focos"]].rename(columns={"focos": "focos_48h"})
        df = df.merge(persist, on=["estado", "municipio"], how="left")
        df["focos_48h"] = df["focos_48h"].fillna(df["focos"])
        df["score_persistencia"] = (df["focos_48h"] > df["focos"]).astype(int) * PESO_PERSISTENCIA
    else:
        df["score_persistencia"] = 0

    df["prioridade"] = (df["score_focos"] + df["score_frp"] + df["score_persistencia"]).round(1)
    df["nivel"] = df["focos"].map(classify_nivel)
    df = df.sort_values(["prioridade", "focos"], ascending=False).reset_index(drop=True)

    return df

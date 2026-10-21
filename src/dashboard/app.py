"""
Dashboard do AlertFocus (Streamlit).

Lê os arquivos gerados por `scripts/run_pipeline.py`:
  - data/processed/ranking_municipios.csv
  - data/processed/meta.json

Rodar:  streamlit run src/dashboard/app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.processing.priority import (  # noqa: E402
    LIMIARES_NIVEL,
    MIN_FOCOS_FRP,
    ORDEM_NIVEIS,
    PESO_FOCOS,
    PESO_FRP,
    PESO_PERSISTENCIA,
)

PROCESSED_DIR = ROOT / "data" / "processed"
RANKING_PATH = PROCESSED_DIR / "ranking_municipios.csv"
META_PATH = PROCESSED_DIR / "meta.json"
LOCAL_TZ = "America/Sao_Paulo"
STALE_AFTER_HOURS = 6

NIVEL_COR = {"Crítico": "#e5383b", "Alto": "#ff8c42", "Médio": "#f4c430", "Baixo": "#4caf50"}
NIVEL_EMOJI = {"Crítico": "🔴", "Alto": "🟠", "Médio": "🟡", "Baixo": "🟢"}

st.set_page_config(page_title="AlertFocus – Focos de calor", page_icon="🔥", layout="wide")

st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem;}
      .alert-card {background:#1a1f2b;border-radius:12px;padding:14px 16px;
                   border-left:5px solid var(--c);height:100%;}
      .alert-card .rank {font-size:.75rem;opacity:.6;}
      .alert-card .name {font-size:1.05rem;font-weight:700;line-height:1.2;}
      .alert-card .uf {font-size:.8rem;opacity:.7;margin-bottom:6px;}
      .alert-card .num {font-size:1.6rem;font-weight:800;color:var(--c);}
      .alert-card .sub {font-size:.75rem;opacity:.7;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_ranking(mtime: float) -> pd.DataFrame:  # mtime só invalida o cache
    df = pd.read_csv(RANKING_PATH, encoding="utf-8")
    df["ultimo_foco"] = pd.to_datetime(df["ultimo_foco"], utc=True, errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_meta(mtime: float) -> dict:
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def fmt_local(iso: str) -> str:
    return pd.Timestamp(iso).tz_convert(LOCAL_TZ).strftime("%d/%m/%Y %H:%M")


# ---------------------------------------------------------------- dados
st.title("🔥 AlertFocus")
st.caption("Focos de calor oficiais do INPE, priorizados por município.")

if not RANKING_PATH.exists() or not META_PATH.exists():
    st.error("Nenhum dado processado encontrado. **Rode o pipeline primeiro:**")
    st.code("python scripts/run_pipeline.py", language="bash")
    st.stop()

ranking = load_ranking(RANKING_PATH.stat().st_mtime)
meta = load_meta(META_PATH.stat().st_mtime)

# ---------------------------------------------------------------- frescor dos dados
idade_h = (pd.Timestamp.now(tz="UTC") - pd.Timestamp(meta["gerado_em_utc"])).total_seconds() / 3600
st.caption(
    f"🕒 Atualizado em **{fmt_local(meta['gerado_em_utc'])}** (horário de Brasília) · "
    f"último foco detectado em **{fmt_local(meta['ultimo_foco_utc'])}**"
)
if idade_h > STALE_AFTER_HOURS:
    st.warning(
        f"Os dados têm {idade_h:.0f}h. Rode `python scripts/run_pipeline.py` para atualizar "
        "(se o INPE estiver fora do ar, o pipeline reaproveita o último arquivo válido)."
    )

# ---------------------------------------------------------------- métricas
n_critico = int((ranking["nivel"] == "Crítico").sum())
n_alto = int((ranking["nivel"] == "Alto").sum())
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Focos nas últimas 24h", f"{meta['focos_24h']:,}".replace(",", "."))
c2.metric("Focos nas últimas 48h", f"{meta['focos_48h']:,}".replace(",", "."))
c3.metric("Municípios com focos (24h)", f"{len(ranking):,}".replace(",", "."))
c4.metric("🔴 Nível Crítico", n_critico)
c5.metric("🟠 Nível Alto", n_alto)
st.caption(
    f"{meta['total_focos_processados']:,} focos processados de {len(meta['arquivos'])} arquivos do INPE."
    .replace(",", ".")
)

# ---------------------------------------------------------------- filtros
st.sidebar.header("Filtros")
estados = sorted(ranking["estado"].dropna().unique())
sel_estados = st.sidebar.multiselect("Estado", estados, placeholder="Todos os estados")
nivel_min = st.sidebar.select_slider("Nível mínimo", options=ORDEM_NIVEIS, value=ORDEM_NIVEIS[0])
busca = st.sidebar.text_input("Buscar município")

filtrado = ranking[ranking["nivel"].map(ORDEM_NIVEIS.index) >= ORDEM_NIVEIS.index(nivel_min)]
if sel_estados:
    filtrado = filtrado[filtrado["estado"].isin(sel_estados)]
if busca:
    filtrado = filtrado[filtrado["municipio"].str.contains(busca, case=False, na=False)]

st.sidebar.caption(f"{len(filtrado)} de {len(ranking)} municípios")

# ---------------------------------------------------------------- alertas prioritários
st.subheader("🚨 Alertas prioritários")
top = filtrado.head(5)
if top.empty:
    st.info("Nenhum município com os filtros selecionados.")
else:
    cols = st.columns(len(top))
    for i, (col, (_, r)) in enumerate(zip(cols, top.iterrows()), start=1):
        col.markdown(
            f"""<div class="alert-card" style="--c:{NIVEL_COR[r['nivel']]}">
                  <div class="rank">#{i} · {NIVEL_EMOJI[r['nivel']]} {r['nivel']}</div>
                  <div class="name">{r['municipio'].title()}</div>
                  <div class="uf">{r['estado'].title()}</div>
                  <div class="num">{int(r['focos'])} focos</div>
                  <div class="sub">prioridade {r['prioridade']:.1f}</div>
                </div>""",
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------- abas
tab_rank, tab_mapa, tab_info = st.tabs(["🏆 Ranking", "🗺️ Mapa", "ℹ️ Como funciona"])

with tab_rank:
    tabela = filtrado.assign(
        nivel_txt=filtrado["nivel"].map(lambda n: f"{NIVEL_EMOJI[n]} {n}")
    )[["estado", "municipio", "focos", "focos_48h", "frp_medio", "prioridade", "nivel_txt"]]

    st.dataframe(
        tabela,
        hide_index=True,
        width="stretch",
        height=520,
        column_config={
            "estado": st.column_config.TextColumn("Estado"),
            "municipio": st.column_config.TextColumn("Município"),
            "focos": st.column_config.NumberColumn("Focos 24h", format="%d"),
            "focos_48h": st.column_config.NumberColumn("Focos 48h", format="%d"),
            "frp_medio": st.column_config.NumberColumn("FRP médio (MW)", format="%.1f"),
            "prioridade": st.column_config.ProgressColumn(
                "Prioridade", min_value=0, max_value=100, format="%.1f"
            ),
            "nivel_txt": st.column_config.TextColumn("Nível"),
        },
    )
    st.download_button(
        "⬇️ Baixar ranking filtrado (CSV)",
        filtrado.to_csv(index=False).encode("utf-8"),
        file_name="ranking_municipios_filtrado.csv",
        mime="text/csv",
    )

with tab_mapa:
    limite = st.slider("Municípios no mapa (top por prioridade)", 10, 300, 60, step=10)
    pontos = filtrado.dropna(subset=["lat", "lon"]).head(limite)

    if pontos.empty:
        st.info("Nenhum município para mostrar no mapa.")
    else:
        mapa = folium.Map(location=[-14.5, -52.0], zoom_start=4, tiles="OpenStreetMap")
        for _, r in pontos.iterrows():
            folium.CircleMarker(
                location=[r["lat"], r["lon"]],
                radius=max(4, min(30, r["focos"] ** 0.5 * 1.2)),
                color=NIVEL_COR[r["nivel"]],
                fill=True,
                fill_opacity=0.55,
                weight=1.5,
                tooltip=(
                    f"<b>{r['municipio'].title()}</b> ({r['estado'].title()})<br>"
                    f"{int(r['focos'])} focos em 24h · {r['nivel']}<br>"
                    f"prioridade {r['prioridade']:.1f}"
                ),
            ).add_to(mapa)
        st_folium(mapa, height=560, use_container_width=True, returned_objects=[])
        st.caption(
            "Cada círculo é o **centro dos focos do município** (média das coordenadas), "
            "com tamanho proporcional ao nº de focos e cor pelo nível."
        )

with tab_info:
    niveis_md = "\n".join(
        f"| {NIVEL_EMOJI[nome]} {nome} | ≥ {minimo} focos |" for minimo, nome in LIMIARES_NIVEL
    )
    st.markdown(
        f"""
### De onde vêm os dados
CSVs diários oficiais do **INPE / Programa Queimadas**, sem alterar os focos: só organizamos por município.
Os horários são UTC; as janelas de 24h e 48h são contadas a partir do momento da atualização.

### Prioridade (0–100)
Serve para **ordenar** o ranking do dia:

| Componente | Máx. | Regra |
|---|---|---|
| Focos | {PESO_FOCOS} | proporcional ao nº de focos em 24h (relativo ao município com mais focos) |
| FRP | {PESO_FRP} | intensidade média (FRP); só vale por inteiro com ≥ {MIN_FOCOS_FRP} focos |
| Persistência | {PESO_PERSISTENCIA} | município também teve focos entre 24h e 48h atrás |

### Nível (limiar absoluto)
Baseado só no nº de focos em 24h, portanto comparável entre dias:

| Nível | Focos em 24h |
|---|---|
{niveis_md}
| 🟢 Baixo | abaixo disso |

> Limiares e pesos são pontos de partida, não calibrados com histórico. Veja os ADRs em `docs/adr/`.
"""
    )

"""Smoke test do dashboard: roda o app headless e confere o que ele renderiza.

Precisa de data/processed/ (gerado por scripts/run_pipeline.py); sem isso, é ignorado.
"""

from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "src" / "dashboard" / "app.py"
RANKING = APP.parents[2] / "data" / "processed" / "ranking_municipios.csv"

pytestmark = pytest.mark.skipif(not RANKING.exists(), reason="rode scripts/run_pipeline.py antes")


def _run():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(APP), default_timeout=30)
    at.run()
    return at


def test_dashboard_renders_without_exception():
    at = _run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.title[0].value.endswith("AlertFocus")
    assert len(at.metric) == 5


def test_nivel_filter_reduces_rows():
    at = _run()
    total = at.sidebar.caption[-1].value  # "N de M municípios"
    at.sidebar.select_slider[0].set_value("Crítico").run()
    assert not at.exception
    assert at.sidebar.caption[-1].value != total

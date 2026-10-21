"""
Download dos focos diários oficiais do INPE (Programa Queimadas).
Fonte: https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/Brasil/
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/Brasil/"
DEFAULT_TIMEOUT = 30
USER_AGENT = "AlertFocus/0.1 (https://github.com/CaioSouzx00/alert-focus)"


def _candidate_dates(days_back: int = 2) -> list[str]:
    """Retorna datas YYYYMMDD para tentar (hoje, ontem, anteontem...)."""
    today = datetime.now(timezone.utc).date()
    return [(today - timedelta(days=i)).strftime("%Y%m%d") for i in range(days_back + 1)]


def build_url(date_str: str) -> str:
    return f"{BASE_URL}focos_diario_br_{date_str}.csv"


def download_latest_csv(output_dir: Path, days_back: int = 2) -> Path | None:
    """
    Tenta baixar o CSV diário mais recente disponível.
    Retorna o caminho do arquivo salvo ou None se falhar.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": USER_AGENT}

    for date_str in _candidate_dates(days_back):
        url = build_url(date_str)
        logger.info("Tentando baixar: %s", url)

        try:
            response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            if response.status_code == 404:
                logger.warning("Arquivo ainda não disponível para %s", date_str)
                continue
            response.raise_for_status()

            # Arquivo vazio ou só cabeçalho? (às vezes o INPE publica arquivo mínimo)
            if len(response.content) < 100:
                logger.warning("Arquivo muito pequeno para %s (%d bytes)", date_str, len(response.content))
                continue

            filename = f"focos_diario_br_{date_str}.csv"
            output_path = output_dir / filename
            output_path.write_bytes(response.content)

            logger.info("Download concluído: %s (%d bytes)", output_path, len(response.content))
            return output_path

        except requests.RequestException as exc:
            logger.error("Erro ao baixar %s: %s", url, exc)
            continue

    logger.error("Não foi possível baixar nenhum CSV dos últimos %d dias", days_back)
    return None

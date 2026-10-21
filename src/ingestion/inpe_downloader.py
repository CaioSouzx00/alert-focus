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


# Arquivos das últimas N datas são sempre rebaixados: o do dia corrente é parcial
# e o do dia anterior pode ser completado depois da virada UTC.
REFRESH_LAST_DAYS = 2


def download_recent_csvs(output_dir: Path, days_back: int = 3) -> list[Path]:
    """
    Baixa os CSVs dos últimos `days_back` dias (incluindo hoje).
    Retorna lista dos arquivos disponíveis (baixados agora ou já existentes),
    do mais antigo para o mais recente.

    - Dias já fechados e presentes em disco não são baixados de novo.
    - Hoje e ontem são sempre rebaixados (arquivos podem estar incompletos).
    - Se o download falhar e existir cópia local, a cópia é usada (último dado bom).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    available: list[Path] = []

    for idx, date_str in enumerate(_candidate_dates(days_back - 1)):
        url = build_url(date_str)
        output_path = output_dir / f"focos_diario_br_{date_str}.csv"
        has_local = output_path.exists() and output_path.stat().st_size > 100

        if has_local and idx >= REFRESH_LAST_DAYS:
            logger.info("Já existe: %s", output_path.name)
            available.append(output_path)
            continue

        logger.info("Tentando baixar: %s", url)
        try:
            response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=DEFAULT_TIMEOUT)
            if response.status_code == 404:
                logger.warning("Não disponível: %s", date_str)
            else:
                response.raise_for_status()
                if len(response.content) < 100:
                    logger.warning("Arquivo muito pequeno para %s (%d bytes)", date_str, len(response.content))
                else:
                    output_path.write_bytes(response.content)
                    logger.info("Salvo: %s (%d bytes)", output_path.name, len(response.content))
                    available.append(output_path)
                    continue
        except requests.RequestException as exc:
            logger.error("Erro %s: %s", date_str, exc)

        if has_local:
            logger.warning("Usando cópia local anterior de %s", output_path.name)
            available.append(output_path)

    available.reverse()  # _candidate_dates vai de hoje para trás
    logger.info("%d de %d arquivos disponíveis", len(available), days_back)
    return available

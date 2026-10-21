"""Ponto de entrada da ingestão de focos de calor do INPE.

Esqueleto: a lógica de download/limpeza será implementada em src/ingestion/.
"""
import logging

INPE_DAILY_CSV_URL = (
    "https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/Brasil/"
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("alertfocus.ingestion")


def main() -> None:
    log.info("Fonte: %s", INPE_DAILY_CSV_URL)
    log.info("Ingestão ainda não implementada (esqueleto do MVP).")


if __name__ == "__main__":
    main()

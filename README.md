# 🔥 AlertFocus

> Turns Brazil's official INPE daily wildfire hotspot data into prioritized, municipality-level alerts with a simple dashboard.
>
> *Focos de calor oficiais do INPE, organizados por município e priorizados para quem precisa agir rápido.*

## Problema

O INPE publica diariamente os focos de calor detectados por satélite no Brasil, mas os dados saem em arquivos CSV brutos, com milhares de linhas, sem uma visão pronta de "onde olhar primeiro". Defesa Civil, brigadas, jornalistas e pesquisadores precisam abrir planilhas, filtrar por município e comparar períodos na mão. O **AlertFocus** automatiza esse caminho: baixa o dado oficial, padroniza, agrega por município/estado e calcula um nível de prioridade simples e explicável, exibindo tudo num dashboard claro.

## O que o MVP faz (v1)

- [x] Baixa automaticamente o CSV diário de focos do INPE (Brasil), últimos 3 dias
- [x] Limpa e padroniza os dados (lat/lon, data/hora, satélite, município, estado, bioma)
- [x] Conta focos por município nas últimas 24h e 48h
- [x] Calcula um score de prioridade (0–100) e um nível por limiares absolutos de focos ([ADR 002](docs/adr/002-modelo-prioridade.md))
- [x] Dashboard web (Streamlit) com:
  - mapa por município (centro dos focos, cor pelo nível)
  - ranking dos municípios mais críticos, com filtros por estado e nível
  - lista de alertas prioritários

### Fora do escopo do MVP

Machine Learning avançado · integração real com Defesa Civil · SMS/push · multi-região complexa · processamento a cada 10 min em produção (começamos com download diário + polling simples).

## Metas de qualidade (não-funcionais)

| Requisito | Meta do MVP |
|---|---|
| Latência | Alerta visível < 15 min após o dado aparecer no INPE (polling) |
| Disponibilidade | Se o download falhar, usa o último dado válido e registra o erro |
| Custo | Roda local ou em free tier (Railway, Render, Fly.io) |
| Consistência | Mesmos focos do INPE, apenas reorganizados |
| Observabilidade | Logs claros + indicação de "última atualização" |

## Como rodar localmente

> O pipeline é executado manualmente por enquanto (sem agendamento automático).

```bash
# 1. Clonar
git clone https://github.com/CaioSouzx00/alert-focus.git
cd alert-focus

# 2. Ambiente virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# 3. Dependências
pip install -r requirements.txt

# 4. Baixar, limpar e calcular o ranking (gera data/processed/)
python scripts/run_pipeline.py

# 5. Abrir o dashboard (http://localhost:8501)
streamlit run src/dashboard/app.py

# Testes
pytest
```

## Estrutura do repositório

```
alert-focus/
├── docs/            # arquitetura e ADRs (decisões)
├── src/
│   ├── ingestion/   # baixar e limpar dados do INPE
│   ├── processing/  # agregar e calcular prioridade
│   ├── api/         # (depois) endpoints
│   └── dashboard/   # (depois) interface
├── data/raw/        # CSVs baixados (não versionados)
├── tests/
└── scripts/         # pontos de entrada (run_ingestion.py)
```

## Fontes de dados oficiais (INPE)

- CSV diário Brasil: <https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/Brasil/>
- (futuro) CSVs de 10 minutos, para tempo quase real

Dados do Programa Queimadas / INPE. Este projeto **não é oficial** e não substitui os canais do INPE.

## Decisões de arquitetura

Veja [`docs/adr/`](docs/adr/):

- [001 – Escolha da fonte de dados](docs/adr/001-escolha-fonte-dados.md)
- [002 – Modelo de prioridade](docs/adr/002-modelo-prioridade.md) *(rascunho)*

## Licença

A definir.

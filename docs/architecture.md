# Arquitetura (visão geral do MVP)

Pipeline simples, de ponta a ponta, sem serviços extras:

```
INPE (CSV diário) → ingestion → data/raw → processing → dados agregados → dashboard
```

| Etapa | Pasta | Responsabilidade |
|---|---|---|
| Ingestão | `src/ingestion/` | Baixar o CSV, validar, padronizar colunas. Em falha, manter o último dado bom e registrar o erro. |
| Processamento | `src/processing/` | Contar focos por município (24h/48h) e calcular o score de prioridade. |
| API | `src/api/` | *(depois)* Expor os dados agregados. |
| Dashboard | `src/dashboard/` | *(depois)* Mapa, ranking e alertas. |

## Observabilidade

- Logs claros em cada etapa.
- Registro de "última atualização bem-sucedida" exibido no dashboard.

## Decisões

Ver [`adr/`](adr/).

# ADR 002 – Modelo de prioridade

- **Status:** Rascunho
- **Data:** 2026-10-21

## Contexto

Precisamos ordenar os municípios por criticidade de forma simples e explicável, sem Machine Learning.

## Decisão (proposta inicial)

Score por município, calculado sobre as janelas de 24h e 48h:

```
score = focos_24h + 0.5 * focos_24h_a_48h + bonus_concentracao
```

- `bonus_concentracao`: valor fixo adicionado se uma fração alta dos focos ocorreu nas últimas 6h (ex.: > 50%).
- Níveis: **baixo / médio / alto / crítico**, por limites de score a calibrar com dados reais.

> Os pesos e limites acima são pontos de partida e serão ajustados após olhar dados reais.

## Consequências

- (+) Fácil de explicar e de testar.
- (−) Não considera bioma, área, vegetação ou clima (fica para versões futuras).

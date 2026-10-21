# ADR 002 – Modelo de prioridade

- **Status:** Aceito (v1, pode evoluir)
- **Data:** 2026-10-21

## Contexto

Precisamos ordenar os municípios por criticidade de forma **simples e explicável**, sem Machine Learning. Qualquer pessoa deve conseguir olhar um município no ranking e entender por que ele está ali.

## Decisão

Score de 0 a 100 por município, calculado a partir dos focos das janelas de 24h e 48h (relativas ao momento da execução, em UTC):

```
prioridade = score_focos + score_frp + score_persistencia
```

| Componente | Máx. | Regra |
|---|---|---|
| `score_focos` | 60 | `60 × focos_24h / max(focos_24h entre municípios)` |
| `score_frp` | 25 | `25 × min(frp_medio / max_frp_ref, 1) × min(focos_24h / 10, 1)` |
| `score_persistencia` | 15 | 15 se houve focos também entre 24h e 48h atrás (`focos_48h > focos_24h`), senão 0 |

- **FRP** (*Fire Radiative Power*) é a potência radiativa do fogo informada pelo INPE; é um indicador de intensidade.
- `max_frp_ref` é o maior FRP médio entre municípios com pelo menos 10 focos.
- O fator `min(focos_24h / 10, 1)` evita que poucos focos com FRP muito alto (ou um único foco) dominem o ranking. Sem ele, na primeira execução um município com 1 foco (FRP 289,6) ficou à frente de outro com 149 focos.
- Desempate: maior número de focos em 24h.

Constantes em [`src/processing/priority.py`](../../src/processing/priority.py): `PESO_FOCOS`, `PESO_FRP`, `PESO_PERSISTENCIA`, `MIN_FOCOS_FRP`.

### Nível (limiares absolutos)

O score acima serve para **ordenar** o ranking do dia (é relativo). Para a lista de alertas existe uma coluna separada, `nivel`, baseada apenas no número **absoluto** de focos em 24h do município, o que a torna comparável entre dias:

| Nível | Focos em 24h |
|---|---|
| Crítico | ≥ 100 |
| Alto | 40 – 99 |
| Médio | 15 – 39 |
| Baixo | < 15 |

Os limiares são um ponto de partida e serão ajustados depois de ver o dashboard com dados reais (constante `LIMIARES_NIVEL`). Não consideram o tamanho do município.

## Consequências

- (+) Fácil de explicar, testar e ajustar (todas as colunas `score_*` ficam no resultado).
- (−) **Score relativo:** `score_focos` depende do município com mais focos no dia. A prioridade compara municípios entre si em um mesmo dia; não é comparável entre dias. Para comparação entre dias e alertas absolutos usa-se o `nivel`.
- (−) Não considera bioma, área do município, vegetação, clima nem `risco_fogo`.
- (−) Janela de 24h pode estar incompleta em horários próximos da virada UTC, pois o arquivo do dia é parcial.

## Evolução possível

Pesos e limites foram escolhidos como ponto de partida, não calibrados com dados históricos. Próximos passos: normalização absoluta (por limiares), uso de `risco_fogo`/bioma e níveis (baixo/médio/alto/crítico).

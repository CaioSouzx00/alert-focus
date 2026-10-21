# ADR 001 – Escolha da fonte de dados

- **Status:** Aceito
- **Data:** 2026-10-21

## Contexto

O FocoAlerta precisa de dados de focos de calor para o Brasil que sejam oficiais, gratuitos e estáveis, para que os números do dashboard batam com os do INPE.

## Decisão

Usar o **CSV diário oficial do INPE (Programa Queimadas)**:
<https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/Brasil/>

Motivos: é estável, gratuito e atualizado diariamente.

## Alternativas consideradas

| Alternativa | Por que não agora |
|---|---|
| API não documentada oficialmente | Sem garantia de contrato; pode mudar ou sumir sem aviso |
| NASA FIRMS | Dado global e não é a fonte nacional oficial; exige chave de API e pode divergir dos números do INPE |
| CSVs de 10 minutos do INPE | Ótimo para tempo quase real, mas fica para depois do MVP |

## Consequências

- (+) Simples de baixar (HTTP) e de testar.
- (+) Consistência com o INPE.
- (−) Latência limitada à frequência de publicação do arquivo diário.
- (−) Se o INPE ficar fora do ar, usamos o último dado válido e registramos o erro.

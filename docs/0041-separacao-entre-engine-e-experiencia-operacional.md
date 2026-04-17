# 0041 - Separação entre engine e experiência operacional

## Tese

O `cvg-harness` tem duas camadas legítimas e complementares:

1. engine interna de governança
2. camada de experiência operacional no terminal

Misturar essas duas coisas como se fossem a mesma superfície gera confusão. A engine precisa continuar modular. A operação precisa parecer produto.

## Engine interna

A engine é responsável por:
- classificação
- research
- PRD
- SPEC
- lint
- sprint planning
- guardian
- evaluator
- drift
- release readiness
- ledger
- métricas
- runtime
- `FlowOrchestrator`

Essa camada existe para:
- governar
- validar
- rastrear
- compor fluxos
- sustentar automação controlada

## Camada de UX / CLI

A camada de UX existe para:
- reduzir atrito de uso
- dar uma entrada principal clara
- expor o próximo passo operacional
- tornar retomada e inspeção óbvias
- separar operação diária de primitives internas

Hoje essa camada é implementada principalmente em:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`

## Por que essa separação importa

Sem essa separação, o produto parece apenas um toolkit técnico:
- o usuário vê `classify`, `lint`, `guard`, `drift`
- não fica claro qual é o comando principal
- não fica claro como uma demanda anda até o final
- a percepção vira “framework” em vez de “orquestrador operacional”

Com a separação, a experiência muda:
- o operador entra com `cvg run`
- acompanha com `status` e `inspect`
- decide com `approve`, `continue`, `pause`, `replan`
- a engine continua trabalhando por baixo

## O que foi preservado

A evolução para CLI canônico não removeu:
- `FlowOrchestrator`
- os agentes internos
- os gates
- os contratos de artefatos
- os comandos avançados
- a rastreabilidade do ledger
- a possibilidade de uso como toolkit técnico

## O que mudou

Mudou a entrada do produto:
- antes: foco quase todo nos subcomandos granulares
- agora: foco explícito em operação de demanda

Mudou também a estrutura de uso:
- antes: primitives isoladas
- agora: run canônica com estado operacional próprio

## Princípio de preservação de governança

A separação não pode virar simplificação irresponsável.

A camada de UX só é válida se:
- continuar usando a engine existente
- continuar produzindo artefatos e gates
- continuar persistindo estado
- continuar respeitando os limites de execução segura

## Regra prática

Se um comportamento é de governança, ele deve continuar na engine.

Se um comportamento é de experiência operacional, ele deve subir para a CLI canônica.

Exemplo:
- classificar uma demanda: engine
- iniciar uma run canônica no terminal: UX
- verificar drift entre camadas: engine
- mostrar “próximo passo” para o operador: UX

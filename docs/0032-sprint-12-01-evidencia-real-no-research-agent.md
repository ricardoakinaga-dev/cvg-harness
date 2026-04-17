# 0032. Sprint 12.1 — Evidência real no ResearchAgent

## Objetivo
Fechar o próximo item pendente da sprint anterior com escopo mínimo:
transformar a saída do `ResearchAgent` em um misto explícito de evidência observada do repositório + inferência, em vez de depender apenas de heurísticas textuais.

## Estado de partida
- `0031-sprint-12-profundidade-dos-motores-de-planning.md` está com itens de planejamento abertos.
- No ciclo corrente, o `ResearchAgent` ainda está orientado por inferência por texto e faltam sinais explícitos do workspace no `system-map`.
- A trilha de validação da execução real permanece estável:
  - `pytest -q` ✅ (`176/176`)
  - `python3 examples/demo_complete_flow.py` ✅ (`Release: APPROVED`)

## Itens do sprint (execução limitada a este bloco)

### 1) Levantar evidência observável antes de inferir módulos
**Status:** `done` (implementação e casos de teste adicionados)

Arquivos alvo:
- `src/cvg_harness/research/research_agent.py`
- `tests/test_agents.py`
- `tests/test_pr02_canonical_artifacts.py`
- `tests/test_pr03_flow_orchestrator.py`

Entregáveis:
- Identificar diretórios e arquivos candidatos com base em estruturas reais do projeto.
- Popular `system_map.arquivos_area`, `system_map.modulos` e `system_map.boundaries` com entradas observadas.
- Separar no documento de pesquisa o que é `sinal observado` e o que é `inferência` quando não há sinal suficiente.
- Evitar alteração estrutural de contrato de fluxo (sem tocar release/gates/lifecycle).

Critérios de saída:
- Quando houver evidência de módulos/arquivos, a seção de research do output deixa de depender apenas de palavras-chave da feature.
- A diferença entre evidência observável e inferência está rastreável no output.
- `tests/test_agents.py` passa a validar o caminho de pesquisa por código local.

### 2) Cobertura mínima de regressão para a mudança de research
**Status:** `done` (cobertura de presença e ausência de evidência local adicionada)

Arquivos alvo:
- `tests/test_agents.py`
- `tests/test_pr02_canonical_artifacts.py`
- `tests/test_pr03_flow_orchestrator.py`

Entregáveis:
- Um caso de teste garantindo que o research preencha `system-map` com pelo menos um caminho concreto do workspace quando disponível.
- Um caso de teste de fallback cobrindo cenário em que não há sinais estruturais suficientes e a inferência textual é aceita como contingência documentada.
- Um caso de integração garantindo que `run_research()` propaga o workspace do fluxo e ainda usa evidência do repositório quando o workspace operacional não contém código-fonte.

Critérios de saída:
- suíte de testes não reduz a cobertura de decisões de pesquisa.
- suíte cobre comportamento de presença/ausência de evidência local.

## Validação
```bash
pytest -q
python3 examples/demo_complete_flow.py
pytest -q tests/test_agents.py tests/test_pr02_canonical_artifacts.py tests/test_pr03_flow_orchestrator.py
rg -n "system_map\\.arquivos_area|modulos_impactados|infer|evidência|evidencia|system-map|research-notes" src/cvg_harness/research docs tests -g '!**/__pycache__/**'
```

## Critério de encerramento
- `ResearchAgent` passa a preencher `system-map` com sinais de workspace quando existirem.
- fallback textual permanece explícito e não é o caminho padrão quando dados reais estiverem acessíveis.
- sprint mantém escopo pequeno e não altera contratos de fluxo, release ou telemetria já estabilizados.

### Validação executada
- Focada: `pytest -q tests/test_agents.py tests/test_pr02_canonical_artifacts.py tests/test_pr03_flow_orchestrator.py` -> verde.
- Completa: `pytest -q` -> `176/176`.
- Demo: `python3 examples/demo_complete_flow.py` -> `Fluxo: completed`, `Release: APPROVED`.

Próximo ciclo documentado em:
- `docs/0033-sprint-13-observabilidade-event-log-canonicidade.md`

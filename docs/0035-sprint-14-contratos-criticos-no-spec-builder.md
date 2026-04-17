# 0035. Sprint 14 - Contratos críticos no SpecBuilderAgent

## Objetivo
Executar uma rodada curta para aumentar a densidade e a criticidade dos contratos gerados pelo `SpecBuilderAgent`, tornando a SPEC menos genérica em cenários sensíveis sem reabrir o fluxo, gates ou release já estabilizados.

## Estado de partida
- Projeto segue aprovado e estável após a Sprint 12.
- Auditoria mais recente em `docs/0034-relatorio-de-auditoria-pos-sprint-12.md` elevou `Spec Builder` para `81/100`, mas apontou o próximo espaço de melhoria como profundidade adicional de contratos.
- O estado validado antes desta sprint permanece:
  - `pytest -q` -> `184/184`
  - `python3 examples/demo_complete_flow.py` -> `Fluxo: completed`, `Release: APPROVED`
- O `SpecBuilderAgent` já gera contratos mínimos por contexto, mas ainda há espaço para:
  - diferenciar melhor contratos críticos de contratos auxiliares;
  - explicitar severidade/criticidade por contrato;
  - enriquecer observabilidade e rollback em cenários `auth`, `api`, `release` e `database`.

## Foco da sprint
Atacar apenas profundidade contratual da SPEC e sua cobertura de regressão.

## Itens do sprint

### 1. Classificar contratos por criticidade e superfície
**Status:** `done`

Objetivo:
- fazer a SPEC distinguir contratos centrais dos contratos auxiliares.

Arquivos alvo:
- `src/cvg_harness/spec_builder/spec_builder.py`
- `tests/test_agents.py`
- `tests/test_pr02_canonical_artifacts.py`

Mudanças esperadas:
- adicionar nos contratos campos como `criticidade`, `superficie`, `evidencia_minima` ou equivalente curto e consistente;
- marcar contratos de auth/release/api críticos com severidade mais alta;
- manter compatibilidade com o linter e o fluxo atual.

Resultado desta rodada:
- `SpecBuilderAgent` passou a enriquecer contratos com `criticidade`, `superficie` e `evidencia_minima`;
- contratos de `auth`, `api`, `database` e `release/gates` agora nascem priorizados por risco conforme o contexto observado;
- a suíte ganhou cobertura para esse metadata tanto no nível do agente quanto no artefato canônico `spec.json`.

Critérios de saída:
- `spec.json` passa a diferenciar contratos centrais e auxiliares em cenários não triviais;
- a cobertura prova que contratos críticos são gerados quando o contexto pede isso.

### 2. Tornar observabilidade e rollback mais específicos por contexto
**Status:** `done`

Objetivo:
- reduzir respostas genéricas de `observabilidade` e `rollback`.

Arquivos alvo:
- `src/cvg_harness/spec_builder/spec_builder.py`
- `tests/test_agents.py`
- `tests/test_linter.py`

Mudanças esperadas:
- enriquecer observabilidade para auth/api/release/database com saídas mais orientadas a operação real;
- tornar rollback mais contextual ao tipo de módulo impactado;
- evitar textos vagos como resposta padrão quando já existe contexto suficiente.

Observação: o código atual já contém respostas mais específicas para `observabilidade` e `rollback`, mas esta rodada ainda não consolidou a cobertura e a trilha documental desse item.

Resultado desta rodada:
- `SpecBuilderAgent` passou a gerar observabilidade mais específica para auth/api/release/database;
- `rollback` passou a ser contextual ao tipo de módulo impactado;
- a cobertura prova esses textos no agente e no fluxo real.

Critérios de saída:
- SPEC fica mais próxima de um handoff operacional real em cenários sensíveis;
- os testes capturam a diferença entre contexto simples e contexto crítico.

### 3. Consolidar cobertura e trilha documental da criticidade contratual
**Status:** `done`

Objetivo:
- garantir que o ganho de profundidade contratual fique registrado e auditável.

Arquivos alvo:
- `tests/test_pr03_flow_orchestrator.py`
- `docs/0007-contratos-dos-artefatos.md`
- `docs/0034-relatorio-de-auditoria-pos-sprint-12.md`

Mudanças esperadas:
- adicionar teste de integração para contratos críticos gerados via `build_spec()` no fluxo real;
- alinhar a doc de contratos ao modelo mais rico da SPEC;
- registrar na auditoria histórica que o próximo gap atacado passou a ser criticidade contratual, não planning básico.

Resultado desta rodada:
- `tests/test_pr03_flow_orchestrator.py` já valida no fluxo real que `build_spec()` produz contratos críticos e critérios derivados do contexto observado;
- `docs/0007-contratos-dos-artefatos.md` foi alinhado para explicitar contratos com criticidade, superfície e evidência mínima;
- `docs/0034-relatorio-de-auditoria-pos-sprint-12.md` passou a registrar que o próximo gap atacado é criticidade contratual, não planning básico.

Critérios de saída:
- a trilha documental deixa claro que o upstream avançou de “contrato mínimo” para “contrato minimamente priorizado por risco”; 
- a suíte cobre esse avanço no fluxo real.

## Validação
```bash
pytest -q
python3 examples/demo_complete_flow.py
pytest -q tests/test_agents.py tests/test_pr02_canonical_artifacts.py tests/test_pr03_flow_orchestrator.py tests/test_linter.py
rg -n "criticidade|superficie|evidencia_minima|observabilidade|rollback|contratos" src docs tests -g '!**/__pycache__/**'
```

## Critério de encerramento
- `SpecBuilderAgent` produz contratos mais ricos e priorizados por risco quando o contexto justificar;
- `observabilidade` e `rollback` ficam menos genéricos em cenários críticos;
- a cobertura e a documentação deixam esse avanço explícito;
- o escopo permanece incremental, sem reabrir fluxo, release ou planejamento já estabilizados.

### Validação executada
- Completa: `pytest -q` -> `189/189`.
- Demo: `python3 examples/demo_complete_flow.py` -> `Fluxo: completed`, `Release: APPROVED`.

Próximo ciclo documentado em:
- `docs/0036-sprint-15-metricas-operacionais-canônicas.md`

## Encadeamento
- Continuidade após esta sprint: `docs/0036-sprint-15-metricas-operacionais-canônicas.md`.
- Auditoria de saída consolidada em `docs/0037-relatorio-de-auditoria-pos-sprint-15.md`.

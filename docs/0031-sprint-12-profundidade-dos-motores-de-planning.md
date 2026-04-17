# 0031. Sprint 12 - Profundidade dos motores de planning

## Objetivo
Executar uma rodada curta para aumentar a profundidade operacional de `ResearchAgent`, `PRDAgent` e `SpecBuilderAgent`, reduzindo a distância entre a arquitetura documental e a implementação real sem reabrir o núcleo já estabilizado do fluxo.

## Estado de partida
- Projeto segue aprovado e operacional após a Sprint 10 registrada em `docs/0029-sprint-10-fechamento-de-ciclo-e-coerencia-operacional.md`.
- Validação rápida mais recente:
  - `pytest -q` -> `176/176`
  - `python3 examples/demo_complete_flow.py` -> `Fluxo: completed`, `Release: APPROVED`
- A auditoria de estado real em `docs/0028-relatorio-de-auditoria-do-estado-real.md` deixou um gap estrutural claro:
  - `ResearchAgent` ainda infere módulos principalmente por palavras-chave;
  - `PRDAgent` ainda monta problema/objetivo/escopo com heurísticas genéricas;
  - `SpecBuilderAgent` ainda nasce com contratos quase vazios e critérios derivados de templates simples.

## Foco da sprint
Atacar apenas os motores de planning upstream, sem mexer no contrato de release, gates ou lifecycle terminal já consolidados.

## Itens do sprint

### 1. Tornar o research menos cego ao codebase
**Status:** `done`

Execução detalhada deste item em:
[0032-sprint-12-01-evidencia-real-no-research-agent](/home/ricardo/.openclaw/workspace/cvg-harness/docs/0032-sprint-12-01-evidencia-real-no-research-agent.md)

Observação: item já desdobrado e implementado em [0032-sprint-12-01-evidencia-real-no-research-agent](./0032-sprint-12-01-evidencia-real-no-research-agent.md) e validado com `pytest -q` + demo end-to-end em `examples/demo_complete_flow.py`.

Objetivo:
- fazer `ResearchAgent` usar sinais reais do repositório antes de cair em inferência por keyword.

Arquivos alvo:
- `src/cvg_harness/research/research_agent.py`
- `tests/test_agents.py`
- `tests/test_pr02_canonical_artifacts.py`
- `tests/test_pr03_flow_orchestrator.py`

Mudanças esperadas:
- inspecionar a árvore do projeto/workspace para identificar módulos candidatos, arquivos prováveis e boundaries reais;
- separar claramente fatos observados do repositório de hipóteses inferidas;
- preencher `system_map.arquivos_area`, `modulos`, `dependencias` e `boundaries` com base em evidência local quando disponível;
- manter fallback heurístico só quando o workspace não oferecer sinal suficiente.

Resultado desta rodada:
- `ResearchAgent` agora inspeciona `workspace`/repositório para identificar módulos, áreas e boundaries observáveis antes de cair para heurística;
- `research-notes` passou a separar fatos observados do codebase de hipóteses produzidas por fallback heurístico;
- `run_research()` passou a propagar o workspace do fluxo para o motor de research;
- a suíte ganhou cobertura para evidência local explícita e para fallback ao repositório do projeto.

Critérios de saída:
- `ResearchAgent` deixa de depender apenas do texto da feature para montar `modulos_impactados`;
- `research-notes` e `system-map` passam a registrar evidência observável do codebase quando houver.

### 2. Tornar o PRD derivado do research real, não só de templates
**Status:** `done`

Observação: alteração executada e validada com suíte unitária + markdown coverage em `tests/test_agents.py` e `tests/test_pr02_canonical_artifacts.py`.

Objetivo:
- fazer `PRDAgent` refletir melhor riscos, restrições e escopo levantados no research.

Arquivos alvo:
- `src/cvg_harness/prd/prd_agent.py`
- `docs/0006-agentes-e-responsabilidades.md`
- `tests/test_agents.py`
- `tests/test_pr02_canonical_artifacts.py`

Mudanças esperadas:
- derivar `problema`, `objetivo`, `escopo`, `fora_de_escopo` e `criterios_aceite` a partir de `research_notes` e `classification`, em vez de frases genéricas repetidas;
- propagar riscos e restrições reais do research para o PRD;
- tornar user stories e KPIs minimamente coerentes com o tipo de mudança e o modo operacional.

Resultado desta rodada:
- `PRDAgent` passou a derivar problema e objetivo a partir de fatos, riscos, restrições e módulos observados no research;
- `escopo`, `fora_de_escopo`, `KPIs`, `user_stories` e `criterios_aceite` agora variam materialmente conforme o contexto real dos módulos afetados;
- o markdown do PRD passou a refletir restrições e critérios vindos do research, não só texto genérico de template.

Critérios de saída:
- PRD deixa de soar como template neutro para features distintas;
- mudanças em `research_notes` passam a alterar materialmente o PRD gerado.

### 3. Enriquecer a SPEC com contratos e lacunas explícitas
**Status:** `done`

Observação: item executado com:
- contratos API/auth/integration gerados quando o contexto da pesquisa indica esses módulos;
- critérios não testáveis marcados como `definido_como_lacuna`;
- cobertura de regressão em `tests/test_agents.py` e `tests/test_linter.py`.

Objetivo:
- fazer `SpecBuilderAgent` produzir uma SPEC mais executável e menos vazia no eixo de contratos e critérios.

Arquivos alvo:
- `src/cvg_harness/spec_builder/spec_builder.py`
- `docs/0005-arquitetura-operacional-corrigida.md`
- `docs/0007-contratos-dos-artefatos.md`
- `tests/test_agents.py`
- `tests/test_linter.py`
- `tests/test_pr02_canonical_artifacts.py`

Mudanças esperadas:
- preencher `contratos` a partir de research/PRD quando houver API, auth, banco ou integrações externas envolvidas;
- diferenciar critérios realmente testáveis de critérios que precisam nascer marcados como lacuna;
- tornar `limite_escopo`, `observabilidade` e `rollback` mais específicos ao contexto levantado no research.

Critérios de saída:
- `spec.json` nasce com mais densidade operacional em cenários não triviais;
- o linter consegue validar uma SPEC menos genérica e mais próxima do que a doc fundacional descreve.

### 4. Consolidar testes e contrato vivo dos motores de planning
**Status:** `done`

Observação: item fechado com cobertura em `tests/test_pr03_flow_orchestrator.py`, amarrando `research -> PRD -> spec` ao contexto real do workspace e validando contratos/critérios derivados do cenário observado.

Objetivo:
- garantir que a melhoria de profundidade não fique só implícita no código.

Arquivos alvo:
- `tests/test_agents.py`
- `tests/test_pr02_canonical_artifacts.py`
- `tests/test_pr03_flow_orchestrator.py`
- `docs/0028-relatorio-de-auditoria-do-estado-real.md`

Mudanças esperadas:
- criar cenários que diferenciem claramente output heurístico de output enriquecido por evidência real;
- adicionar cobertura para derivação de boundaries, contratos e critérios a partir de módulos reais;
- registrar no `0028` ou no encerramento desta sprint o fechamento parcial do gap estrutural apontado na auditoria.

Critérios de saída:
- a suíte prova que `research/prd/spec` reagem ao contexto real do repositório;
- a próxima auditoria consegue medir avanço objetivo nesses três motores.

## Validação
```bash
pytest -q
python3 examples/demo_complete_flow.py
pytest -q tests/test_agents.py tests/test_pr02_canonical_artifacts.py tests/test_linter.py tests/test_pr03_flow_orchestrator.py
rg -n "infer_modules|contratos=\[\]|lacuna|boundaries|modulos_impactados|criterios_aceite" src docs tests -g '!**/__pycache__/**'
```

## Critério de encerramento
- `ResearchAgent` passa a usar evidência real do workspace quando disponível;
- `PRDAgent` deixa de gerar PRDs quase idênticos para entradas semanticamente diferentes;
- `SpecBuilderAgent` produz SPEC mais densa em contratos, critérios e lacunas explícitas;
- a mudança permanece incremental, sem reabrir fluxo, gates ou release.

## Encerramento
**Sprint 12 concluída — 2026-04-16.**

Evidência consolidada desta sprint:
- `pytest -q` com sucesso (`184/184`).
- `python3 examples/demo_complete_flow.py` com `Fluxo: completed` e `Release: APPROVED`.
- cobertura explícita em `tests/test_agents.py`, `tests/test_pr02_canonical_artifacts.py`, `tests/test_pr03_flow_orchestrator.py` e `tests/test_linter.py` para provar que `research -> PRD -> spec` reage ao contexto real do repositório.

Resultado consolidado:
- `ResearchAgent` passou a usar evidência real do codebase antes de fallback heurístico;
- `PRDAgent` passou a derivar problema, objetivo, escopo e critérios a partir de research real;
- `SpecBuilderAgent` já opera com contratos mínimos, critérios marcados como lacuna e maior densidade operacional;
- a trilha de testes agora prova o contrato vivo desses três motores no fluxo principal.

## Encadeamento
- Auditoria histórica de entrada: `docs/0028-relatorio-de-auditoria-do-estado-real.md`.
- Desdobramento do item 1: `docs/0032-sprint-12-01-evidencia-real-no-research-agent.md`.
- Auditoria de saída desta sprint: `docs/0034-relatorio-de-auditoria-pos-sprint-12.md`.
- Continuidade pós-auditoria em `docs/0035-sprint-14-contratos-criticos-no-spec-builder.md`.

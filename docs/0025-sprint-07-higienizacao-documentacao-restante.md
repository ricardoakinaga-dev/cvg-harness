# 0025. Sprint 07 - Higienização de documentação residual

## Objetivo
Fechar resíduos de rastreabilidade documental que não afetam comportamento de produto:
- normalizar referências de artefatos canônicos em documentos históricos fora da trilha principal;
- reduzir ambiguidades em pontos de validação já aprovados.

O objetivo é manter a trilha de aprovação coesa sem reabrir bloqueios de Sprint 02/03.

## Estado de partida
- Projeto aprovado em `0019`.
- `0024` consolidou observabilidade de runtime e testes contratuais.
- Restam documentos históricos que ainda podem sugerir caminhos secundários não alinhados com o modelo canônico atual, principalmente sobre artefato de release.

## Itens do sprint

### 1. Rastrear e corrigir referências divergentes de canonicidade
**Status:** `done`

Objetivo:
- revisar documentos de referência operacional e histórico para deixar claro:
  - artefato canônico operacional: `release-readiness-report.json`;
  - `release-readiness.md` permanece como sidecar opcional para leitura humana.

Arquivos alvo:
- `docs/0017-guia-operacional-para-fechar-divergencias.md`
- `docs/0005-arquitetura-operacional-corrigida.md`

Critério de saída:
- no texto operacional, qualquer menção a `release-readiness.md` fora do contexto de sidecar deve ser removida.

### 2. Encadear sprint com trilha documental mínima
**Status:** `done`

Objetivo:
- registrar a transição explícita de continuidade a partir de `0024` para `0025`,
  sem alterar decisões técnicas.

Arquivos alvo:
- `docs/0016-backlog-executavel-de-correcao.md`
- `docs/0019-checklist-final-de-aprovacao.md`
- `docs/0024-sprint-06-runtime-metrics-e-hooking-operacional.md`

Critério de saída:
- leitura rápida mostra que o próximo ciclo documental está em `0025`.

## Validação
```bash
pytest -q
python3 examples/demo_complete_flow.py
rg -n "release-readiness-report.json|release-readiness\\.md|canônico|sidecar|Sprint 07|0025-sprint-07" docs README.md examples tests -g '!**/__pycache__/**'
```

## Critério de encerramento
- Itens 1 e 2 concluídos com escopo textual e encadeamento documental preservado.
- Nenhum comportamento de produto alterado.
- aprovação já conquistada permanece intacta.

Encerramento (2026-04-16):
- referências de canonicidade em `docs/0005`/`docs/0017` revisadas para refletir `release-readiness-report.json` como canônico e `release-readiness.md` como sidecar opcional;
- encadeamento documental alinhado em `0016`, `0019` e `0024`.

Próximo ciclo recomendado:
- [0026-sprint-08-higienizacao-estado-real-e-rastreabilidade-documental.md](/home/ricardo/.openclaw/workspace/cvg-harness/docs/0026-sprint-08-higienizacao-estado-real-e-rastreabilidade-documental.md)

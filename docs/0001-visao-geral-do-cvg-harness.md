# 0001. Visão geral do CVG-Harness

## Objetivo
O `cvg-harness` é um sistema operacional de engenharia orientado por IA para transformar demandas de software em entregas controladas, auditáveis e progressivas.

## Problema que o sistema resolve
O problema central não é "falta de IA para codar". O problema é falta de estrutura para:
- classificar a demanda corretamente
- reduzir ambiguidade antes da execução
- impedir deriva de escopo e arquitetura
- manter rastreabilidade entre intenção, plano e execução
- definir fallback quando a implementação falha

## Tese operacional
Código só deve nascer depois de uma cadeia mínima de decisão, contrato e validação.

Fluxo-alvo:
`Ideia -> Intake -> Classification -> Research -> PRD -> SPEC -> Spec Lint -> Sprint Plan -> Execution -> Architecture Guard -> Evaluation -> Drift Check -> Release Readiness`

## Resultado esperado
O sistema deve ser:
- menos frágil
- menos dependente de improviso
- menos burocrático para tarefas pequenas
- mais determinístico para tarefas críticas
- preparado para futura automação por agentes

## Modos operacionais
### FAST
Usado para demandas pequenas, reversíveis, de baixo risco e baixo impacto arquitetural.

### ENTERPRISE
Usado para demandas críticas, estruturais, multi-módulo, reguladas ou com alto custo de erro.

## Não objetivos
O `cvg-harness` não deve:
- substituir discernimento de produto
- permitir mudança estrutural sem rastreabilidade
- promover sprint reprovada só para ganhar velocidade
- esconder falhas sob documentação bonita

## Resultado organizacional esperado
Se bem implementado, o sistema cria:
- previsibilidade
- histórico confiável
- base para métricas reais
- evidência para auditoria
- redução de retrabalho e regressão


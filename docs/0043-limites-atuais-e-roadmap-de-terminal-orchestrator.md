# 0043 - Limites atuais e roadmap de terminal orchestrator

## Objetivo

Registrar, sem marketing, o que o `cvg-harness` já faz como terminal orchestrator e o que ainda depende de executor externo, hooks ou aprofundamento futuro.

## O que já existe

Hoje o produto já entrega:
- comando canônico `cvg run`
- estado operacional persistido por run
- comandos de operação (`status`, `inspect`, `continue`, `pause`, `approve`, `replan`, `events`, `metrics`)
- planning inicial governado pela engine
- `FlowOrchestrator` preservado como base
- event log e progress ledger reais
- gates formais persistidos
- avaliação, drift e release readiness no ciclo canônico
- retomada de run a partir do workspace

## O que ainda é simulado ou simplificado

Ainda existem componentes com simplificação controlada:
- partes do planning continuam heurísticas
- evidências podem entrar por `--evidence`, `--evidence-json` e `--evidence-file`, mas ainda não substituem sozinhas execução externa real
- exemplos e demos podem usar evidência descritiva para demonstrar o ciclo
- o runtime padrão continua seguro e não assume hooks reais por padrão

## O que depende de hooks / executor externo

O `cvg-harness` não é, por definição, o executor final.

Depende de integração externa para:
- rodar pipelines reais de build/test/deploy
- invocar agentes externos de coding/execution
- operar CI/CD de verdade
- coletar evidência operacional fora do próprio harness
- disparar comandos de infraestrutura em ambiente real

## O que já está preparado para isso

Já existe base para evolução por adaptadores:
- `RuntimeExecutor`
- `RuntimeAutomation`
- `ExternalExecutorAdapter`, `ExecutionDispatchRequest` e `ExternalExecutorBridge`
- persistência de eventos e métricas
- gates e readiness como contratos de decisão
- separação entre engine e experiência operacional

## Limites atuais mais importantes

### 1. Execução real não é obrigatória no loop canônico
O produto governa a run, mas não impõe executor real por padrão.

### 2. Evidência ainda pode ser humana/descritiva
Isso é útil para demonstração e validação controlada, mas não substitui sempre telemetria ou pipeline real.

### 3. O operador ainda conduz checkpoints críticos
Isso é intencional. O projeto não vende automação cega.

### 4. Alguns motores ainda são mais fortes em governança do que em inferência profunda
A camada de planning evoluiu, mas ainda não substitui análise contextual complexa em todos os cenários.

## Próximos passos recomendados

### Curto prazo
- plugar o hand-off para executor externo ao modo operador sem automação cega
- fazer o evaluator consumir parte do schema estruturado de evidência
- enriquecer `metrics` com sinal vindo de dispatch/execução externa quando existir

### Médio prazo
- integrar o runtime a perfis reais de CI opt-in
- consolidar perfis de hooks/adapters de CI sem automação cega
- ampliar contratos de evidência operacional além de texto, arquivo local e sidecars atuais

### Longo prazo
- tornar o harness um terminal orchestrator completo com execução delegada, observabilidade rica e contratos de integração mais rígidos
- sem perder a governança, a rastreabilidade e os checkpoints humanos

## Regra de honestidade

Qualquer evolução futura precisa preservar esta distinção:
- o harness governa e orquestra
- o executor pode ser interno, externo ou híbrido
- automação só pode ser prometida quando estiver sustentada por código, contrato e validação reais

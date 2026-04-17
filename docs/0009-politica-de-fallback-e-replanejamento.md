# 0009. Política de fallback e replanejamento

## Princípio
Falha repetida não deve gerar mais insistência cega. Deve gerar reavaliação do plano.

## 1. Evaluator falha 1 vez
### Ação
- retornar ao coder com feedback fechado
- não alterar PRD ou classificação ainda
### Resultado esperado
correção local sem replanejamento

## 2. Evaluator falha 2 vezes
### Ação
- acionar revisão de sprint
- verificar se a SPEC é insuficiente ou se a sprint está grande demais
- Architecture Guardian revisa se houve desvio estrutural
### Resultado esperado
correção da sprint ou micro-replan

## 3. Evaluator falha 3 vezes
### Ação
- bloquear promoção
- acionar `Replan Coordinator`
- revisar classificação, SPEC e decomposição da sprint
### Resultado esperado
replanejamento formal obrigatório

## 4. Architecture Guardian reprova
### Ação
- bloquear imediatamente a sprint
- impedir nova avaliação funcional até correção arquitetural
- abrir evento `architecture_guard_failed`
### Resultado esperado
correção arquitetural ou waiver explícito

## 5. Spec Lint reprova
### Ação
- proibir início da execução
- devolver para `Spec Builder`
### Resultado esperado
SPEC corrigida antes do código

## 6. Drift Detector encontra inconsistência grave
### Ação
- congelar promoção da sprint
- identificar origem: intake, PRD, SPEC, sprint plan ou execução
- decidir entre correção documental, correção da implementação ou replan
### Resultado esperado
alinhamento restaurado

## 7. Sprint estoura escopo
### Sinais
- número excessivo de arquivos
- múltiplos domínios inesperados
- rounds acima do estimado
### Ação
- dividir sprint
- reemitir `sprint-plan.json`
### Resultado esperado
sprints menores e controláveis

## 8. Complexidade mal classificada
### Ação
- atualizar `classification.json`
- registrar `replan_requested`
- migrar FAST -> ENTERPRISE quando aplicável
### Resultado esperado
fluxo proporcional ao risco real

## 9. SPEC fica inválida durante execução
### Exemplos
- dependência descoberta no meio
- boundary não mapeado
- contrato de API estava incompleto
### Ação
- pausar sprint
- atualizar SPEC e versão
- rerodar Spec Lint
### Resultado esperado
execução retomada com contrato atualizado

## Política de exceções
Waiver só é aceitável quando:
- tem dono explícito
- tem prazo
- tem risco residual registrado
- não viola segurança ou integridade estrutural crítica

## Responsável pelo replanejamento
O replanejamento formal é coordenado pelo `Replan Coordinator`, com participação mínima de:
- planner técnico
- owner de produto, quando escopo muda
- architecture guardian, quando estrutura muda


# 0003. Princípios operacionais

## 1. Proporcionalidade
Nem toda demanda merece o fluxo completo. O processo deve escalar com o risco.

## 2. Contexto limpo por responsabilidade
Um agente não deve acumular planejamento, codificação, validação e replanejamento no mesmo contexto.

## 3. Artefatos como contratos
Documento no `cvg-harness` não é enfeite. Artefato deve servir como instrução, evidência ou decisão.

## 4. Determinismo acima de eloquência
Preferir regras claras, campos obrigatórios, exemplos concretos e estados explícitos.

## 5. Nenhuma mudança estrutural sem autorização explícita
Toda alteração fora do escopo autorizado precisa ser bloqueada ou formalmente aceita.

## 6. Gate sem critério objetivo não é gate
Aprovação precisa de condição verificável. Se não há condição verificável, não há controle.

## 7. Falha precisa gerar aprendizado operacional
Toda reprovação relevante deve deixar rastro para análise posterior.

## 8. Drift é falha de sistema, não detalhe
Quando intenção, plano e execução se separam, o processo precisa interromper, não ignorar.

## 9. Replanejamento não é improviso
Replanejar é um fluxo formal, com gatilhos, responsável e artefatos de atualização.

## 10. Preparação para execução real
Toda camada documental deve prever futura conexão com testes, lint, typecheck, contratos, CI/CD e coleta de evidências.


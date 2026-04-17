# 0002. Auditoria crítica do planejamento atual

## Escopo da auditoria
Esta auditoria avalia o planejamento previamente documentado para o `cvg-harness` e identifica forças, fragilidades e lacunas estruturais.

## Forças reais identificadas
### 1. Separação por contexto
O plano anterior já reconhece que ideação, PRD, SPEC, execução e validação não devem dividir o mesmo contexto.

### 2. Separação entre PRD e SPEC
O desenho anterior diferencia corretamente intenção de negócio e instrução técnica.

### 3. Foco em artefatos
A proposta já avança além de conversa solta com agente e exige documentação persistente.

### 4. Ledger de progresso
A ideia de `progress.json` é correta como fonte de verdade operacional.

### 5. Evaluator independente
A separação entre quem implementa e quem valida é um acerto importante.

### 6. Visão de governança e métricas
O plano já aponta custo, rounds, qualidade e throughput como dimensões necessárias.

## Fragilidades reais
### 1. Complexidade operacional excessiva para demandas menores
O plano anterior assume o fluxo pesado como padrão. Isso tende a gerar burocracia e rejeição operacional.

### 2. Falta de classificador de demanda
Não existe mecanismo formal para decidir quando usar fluxo leve ou pesado.

### 3. Research subcontratual
O bloco de research existe conceitualmente, mas ainda não tem contrato forte de saída, critérios de suficiência ou tipologia de risco.

### 4. SPEC ainda aberta demais
A SPEC anterior é boa como documento, mas ainda permite interpretação excessiva por parte do coder. Faltam limites proibidos, áreas exatas, contratos de entrada e saída e critérios testáveis completos.

### 5. Evaluator passivo
O evaluator anterior atua no fim. Falta postura ativa de bloqueio, tipologia de falhas e política de escalonamento.

### 6. Ausência de Spec Linter
Não há etapa formal de verificação da SPEC antes da execução. Isso desloca erro de planejamento para a fase de codificação.

### 7. Ausência de Architecture Guardian
O plano anterior valida resultado, mas não protege a arquitetura durante a execução.

### 8. Ausência de Drift Detector
Não existe mecanismo explícito para detectar desalinhamento entre intake, PRD, SPEC, sprint plan, execução, avaliação e documentação final.

### 9. Ausência de política de exceções e fallback
O plano anterior pressupõe fluxo linear. Faltam regras para falha repetida, reclassificação, replan e waiver.

### 10. Baixa conexão com runtime real
O plano descreve documentação e governança, mas ainda não amarra claramente lint, testes, typecheck, validação de contrato, CI e evidência operacional.

## Lacunas estruturais
- falta de matriz de complexidade
- falta de `classification.json`
- falta de contrato de handoff entre agentes
- falta de catálogo de evidências obrigatórias
- falta de tipologia de falhas
- falta de `event-log.jsonl`
- falta de política de versionamento dos artefatos
- falta de estado formal de aprovação por gate

## Diagnóstico final
O plano anterior é forte como blueprint de governança, mas ainda insuficiente como sistema operacional executável. A correção necessária não é abandonar a base, e sim torná-la proporcional, contratual e conectada à execução real.


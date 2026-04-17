# 0015. Relatório final de correção do planejamento

## O que foi corrigido
1. o plano deixou de presumir fluxo pesado como padrão
2. foi introduzido classificador FAST vs ENTERPRISE
3. research passou a ter papel mais contratual
4. SPEC foi endurecida para execução, não só documentação
5. evaluator deixou de ser o único guardião tardio
6. foram adicionados Spec Linter, Architecture Guardian, Drift Detector e Replan Coordinator
7. os gates foram formalizados com estados e critérios
8. foi criada política explícita de fallback, waiver e replanejamento
9. `progress.json` foi fortalecido e `event-log.jsonl` foi introduzido
10. o plano foi preparado para integração futura com runtime real

## O que melhorou
- menos ambiguidade
- menos dependência de improviso
- mais proporcionalidade operacional
- mais determinismo antes da codificação
- mais rastreabilidade entre camadas
- mais capacidade de auditoria
- mais prontidão para escala

## O que ainda é risco residual
- excesso de documentação se o modo FAST for mal usado
- burocracia caso o classificador seja ignorado
- dificuldade de manter `spec.md` e `spec.json` sincronizados sem disciplina
- risco de overfitting de processo antes de validar um ciclo real

## Ordem ideal de implementação
1. adotar a documentação corrigida
2. instituir classificação FAST vs ENTERPRISE
3. fechar contrato de SPEC e sprint plan
4. implantar progress ledger e event log
5. implantar Spec Linter
6. implantar Architecture Guardian e Drift Detector
7. só então conectar execução real

## Maturidade atual
### Estado atual
- maturidade conceitual: boa
- maturidade contratual: moderada após esta correção
- maturidade operacional real: ainda baixa, porque o sistema ainda não executa o fluxo fim a fim

### Conclusão
O `cvg-harness` agora tem um planejamento significativamente mais robusto. Ainda não é uma plataforma pronta, mas deixou de ser apenas um blueprint elegante e passou a ter base de sistema operacional de engenharia orientado por IA.


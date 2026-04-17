# 0004. Matriz FAST vs ENTERPRISE

## Objetivo
Definir critério objetivo para selecionar o modo operacional.

## Dimensões de classificação
Cada demanda recebe pontuação de 0 a 3 por dimensão.

1. impacto arquitetural
2. quantidade de módulos afetados
3. risco de regressão
4. criticidade de negócio
5. sensibilidade de dados e segurança
6. dependência externa ou integração
7. reversibilidade da mudança
8. complexidade de validação

## Regras de pontuação
### 0
impacto mínimo, local, reversível, validável rapidamente

### 1
mudança pequena, baixo risco, sem nova estrutura

### 2
mudança moderada, múltiplas áreas, validação não trivial

### 3
mudança estrutural, crítica, difícil de reverter ou auditar

## Decisão de modo
- **FAST**: soma até 8, sem nenhuma dimensão 3 crítica
- **ENTERPRISE**: soma 9 ou mais, ou qualquer dimensão crítica em segurança, arquitetura, integração ou criticidade operacional

## Critérios de override para ENTERPRISE
Usar ENTERPRISE obrigatoriamente quando houver:
- alteração em múltiplos domínios críticos
- autenticação, autorização ou dados sensíveis
- integração externa relevante
- mudança de arquitetura ou boundary de domínio
- alto custo de erro em produção

## Tabela de decisão
| Cenário | Modo | Justificativa |
|---|---|---|
| ajuste pequeno em UI local | FAST | baixo impacto, reversível |
| correção de bug isolado com testes simples | FAST | escopo local e validação simples |
| novo fluxo de autenticação | ENTERPRISE | segurança e regressão alta |
| refatoração de camada de dados | ENTERPRISE | impacto estrutural |
| integração com API externa crítica | ENTERPRISE | dependência e contrato externo |
| novo componente sem impacto sistêmico | FAST | mudança local |

## Artefato obrigatório
Toda demanda deve gerar `classification.json` contendo:
- score por dimensão
- modo selecionado
- racional da classificação
- responsável pela classificação
- data/hora

## Regra de migração FAST -> ENTERPRISE
A migração é obrigatória se ocorrer qualquer uma das condições:
- sprint estoura escopo planejado
- architecture guardian detecta desvio estrutural
- evaluator reprova duas vezes por deficiência de plano
- drift detector aponta desalinhamento grave


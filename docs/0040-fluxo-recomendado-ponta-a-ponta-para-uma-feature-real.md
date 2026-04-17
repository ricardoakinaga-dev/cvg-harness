# 0040. Fluxo recomendado ponta a ponta para uma feature real

## Objetivo
Mostrar o caminho recomendado para levar uma feature real do pedido inicial até release, usando o `cvg-harness` como controle de processo.

## Exemplo de feature
Vamos usar como exemplo a feature:

**Adicionar autenticação OAuth2**

## Fluxo recomendado

### 1. Classificar a demanda
Defina se a mudança é pequena ou crítica.

Exemplo:
```bash
cvg classify --project meu-projeto --demand "Adicionar autenticação OAuth2" --dimensions '{"impacto_arquitetural":3,"modulos_afetados":3,"risco_de_regressao":3,"criticidade_de_negocio":3,"sensibilidade_de_dados":3,"dependencia_externa":2,"reversibilidade":1,"complexidade_de_validacao":2}' --rationale "mudança crítica de segurança"
```

Resultado esperado:
- a demanda tende a ser marcada como `ENTERPRISE`
- a trilha fica mais rigorosa

### 2. Fazer research
Mapeie o codebase, dependências e riscos.

Saídas esperadas:
- módulos afetados
- boundaries
- arquivos da área
- riscos
- hipóteses

Exemplo de uso:
```python
orch.run_research()
```

### 3. Gerar PRD
Formalize problema, objetivo e escopo.

Saídas esperadas:
- problema claro
- objetivo mensurável
- fora de escopo explícito
- riscos e critérios

Exemplo de uso:
```python
orch.run_prd()
```

### 4. Construir SPEC
Traduzir o PRD em especificação técnica executável.

Saídas esperadas:
- contratos
- edge cases
- observabilidade
- rollback
- áreas autorizadas e proibidas

Exemplo de uso:
```python
orch.build_spec()
```

### 5. Rodar lint
Bloquear ambiguidades e lacunas.

Exemplo de uso:
```python
orch.run_lint()
```

### 6. Planejar sprints
Quebrar a SPEC em unidades executáveis.

Exemplo de uso:
```python
orch.plan_sprints()
```

### 7. Proteger a arquitetura
Validar se a implementação respeita a área autorizada.

Exemplo de uso:
```python
orch.check_guard(["src/auth/oauth2/token.py", "src/auth/session.py"])
```

### 8. Executar e avaliar
A sprint só avança se houver evidência suficiente.

Exemplo de uso:
```python
orch.evaluate_sprint(
    evidence_files=["testes", "logs", "arquivos alterados"],
    round_num=1,
)
```

### 9. Detectar drift
Comparar intenção, plano, execução e release readiness.

Exemplo de uso:
```python
orch.detect_drift()
```

### 10. Checar release readiness
Consolidar a decisão final.

Exemplo de uso:
```python
orch.check_release_readiness()
```

## Resultado esperado

Ao final do fluxo, você deve ter:
- artefatos formais por fase
- estado persistido
- event log auditável
- métricas operacionais
- decisão final de release

## Quando esse fluxo faz diferença

Use esse caminho quando a feature tiver:
- impacto arquitetural
- integração com API ou autenticação
- risco de regressão
- dependência externa
- custo alto de erro

## O que evitar

- codar antes de validar o escopo
- ignorar o research
- pular o PRD
- deixar a SPEC genérica
- liberar release sem evidência
- tratar o event log como detalhe

## Resumo prático

O caminho recomendado é:

`Classify -> Research -> PRD -> SPEC -> Lint -> Sprint Plan -> Guard -> Evaluate -> Drift -> Release`


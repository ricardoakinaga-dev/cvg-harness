# 0045 — Configuração Simples e Gestão de API Keys

## Meta

Padronizar o setup de primeira execução e garantir prioridade clara entre flags, ambiente e arquivos.

## Onboarding no primeiro uso

Quando não há configuração válida, `harness` inicia:

```text
Nenhuma configuração válida encontrada.
Vamos configurar o Harness.
Escolha o provider principal:
1. MiniMax (recomendado)
2. OpenAI
3. OpenRouter
```

Comportamento:

- `MiniMax` é sugerido por padrão.
- Coleta da chave pode ser via input ou variável de ambiente já definida.
- A configuração pode ser salva no escopo global ou local.
- Executa teste de conexão não bloqueante e informa resultado.

## Arquivos e prioridade

Ordem aplicada pelo loader:

1. flags explícitas (`--provider`, `--model`, `--api-key`)
2. variáveis de ambiente (`HARNESS_*` e `*_API_KEY`)
3. config local do projeto (`.harness/project.toml`)
4. config global (`~/.config/harness/config.toml`)

## Estrutura de configuração sugerida

Config global:

```toml
default_provider = "minimax"
default_model = "MiniMax-M2.7"

[providers.minimax]
base_url = "https://api.minimax.io/anthropic"
api_key_env = "ANTHROPIC_API_KEY"
models = [
  "MiniMax-M2.7",
  "MiniMax-M2.7-highspeed",
  "MiniMax-M2.5",
  "MiniMax-M2.5-highspeed",
  "MiniMax-M2.1",
  "MiniMax-M2.1-highspeed",
  "MiniMax-M2",
]
```

Config local:

```toml
default_provider = "minimax"
default_model = "MiniMax-M2.7"
```

## Variáveis esperadas

- `ANTHROPIC_API_KEY` (MiniMax)
- `OPENAI_API_KEY` (OpenAI)
- `OPENROUTER_API_KEY` (OpenRouter)
- `ANTHROPIC_BASE_URL` (MiniMax - sobrescreve base_url do provider)
- `OPENAI_BASE_URL` (OpenAI - sobrescreve base_url do provider)
- `OPENROUTER_BASE_URL` (OpenRouter - sobrescreve base_url do provider)
- `HARNESS_PROVIDER`
- `HARNESS_MODEL`

## Regra de segurança

Sempre que possível:

- armazenar segredo no ambiente;
- evitar `api_key` literal no arquivo;
- persistir somente `api_key_env` no config.

## Exemplos de uso

- Setup guiado:
  - `harness`
- Setup explícito (não interativo):
  - `harness --provider minimax --model MiniMax-M2.7 --api-key "$ANTHROPIC_API_KEY"`
- Reconfigurar:
  - `harness config`
- Health:
  - `harness doctor`

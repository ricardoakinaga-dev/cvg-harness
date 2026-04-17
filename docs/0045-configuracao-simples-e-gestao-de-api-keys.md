# 0045 — Configuração Simples e Gestão de API Keys

## Onboarding no primeiro uso
Ao executar `harness` sem configuração:

```
Nenhuma configuração válida encontrada.
Vamos configurar o Harness.
Escolha o provider principal:
1. MiniMax (recomendado)
2. OpenAI
3. OpenRouter
```

## Prioridade de configuração
1. flags explícitas (`--provider`, `--model`, `--api-key`)
2. variáveis de ambiente
3. config local do projeto (`.harness/project.toml`)
4. config global (`~/.config/harness/config.toml`)

## Arquivo de exemplo
- `~/.config/harness/config.toml`
```toml
default_provider = "minimax"
default_model = "MiniMax-M2.7"

[providers.minimax]
base_url = "https://api.minimax.io/anthropic"
base_url_env = "ANTHROPIC_BASE_URL"
api_key_env = "ANTHROPIC_API_KEY"
models = ["MiniMax-M2.7", "MiniMax-M2.7-highspeed", "MiniMax-M2.5", "MiniMax-M2.5-highspeed", "MiniMax-M2.1", "MiniMax-M2.1-highspeed", "MiniMax-M2"]
```

- `.harness/project.toml`
```toml
default_provider = "minimax"
default_model = "MiniMax-M2.7"
```

## Variáveis esperadas
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`
- `ANTHROPIC_BASE_URL`, `OPENAI_BASE_URL`, `OPENROUTER_BASE_URL`
- `HARNESS_PROVIDER`, `HARNESS_MODEL`

## Segurança
- nunca persistir chave em texto puro por padrão.
- preferir chave em variável de ambiente e salvar apenas referência (`api_key_env`).

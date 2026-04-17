# 0045 — Configuração Simples e Gestão de API Keys

## Onboarding no primeiro uso

Quando não há configuração válida, `harness` inicia:

1. Pergunta o provider principal (MiniMax recomendado).
2. Mostra a variável esperada para a chave.
3. Confirma se o usuário deseja salvar a seleção local/profissional.
4. Executa teste de conexão básico e retorna status.

## Arquivos de configuração

Global:

- `~/.config/harness/config.toml`
- campos principais:
  - `default_provider`
  - `default_model`
  - `providers.<name>.api_key_env`
  - `providers.<name>.base_url`

Projeto:

- `.harness/project.toml`
- overrides para projeto atual

## Prioridade de configuração

1. flags explícitas
2. variáveis de ambiente
3. configuração local do projeto
4. configuração global

Exemplo de override com flags:

```bash
harness --provider openai --model gpt-4o-mini --api-key "$OPENAI_API_KEY"
```

## Variáveis de ambiente esperadas

- `ANTHROPIC_API_KEY` (MiniMax)
- `OPENAI_API_KEY` (OpenAI)
- `OPENROUTER_API_KEY` (OpenRouter)
- `HARNESS_PROVIDER`
- `HARNESS_MODEL`

## Recomendações

- Preferir guardar chaves em `*_API_KEY` no ambiente e evitar valores literais no arquivo.
- O config guarda apenas o nome da variável de ambiente.

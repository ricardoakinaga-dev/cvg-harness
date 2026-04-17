# CVG Harness — Agent Terminal Prompt-First

## Visão geral

`harness` é o novo modo principal do projeto: conversa com o terminal em português e decide automaticamente o fluxo interno de engenharia.

A engine de governança existente (classificação, research, PRD, SPEC, lint, sprint, guard, drift, evaluator, release readiness, metrics, replan) foi preservada e passou a ficar **atrás** do agente.

## Instalação

```bash
pip install -e .
```

### Flags explícitas

Você também pode iniciar com override de sessão:

```bash
harness --provider minimax --model MiniMax-M2.7 --api-key SUA_CHAVE
```

## Primeira execução

```bash
harness
```

Sem configuração, o agente entra em onboarding:

1. escolhe provider (MiniMax recomendado),
2. solicita API key (ou variável de ambiente),
3. salva configuração principal e segue para o loop.

Exemplo esperado:

```text
Harness iniciado.
Workspace detectado: /caminho/do/projeto
Provider: minimax | MiniMax-M2.7
Digite sua instrução.
> criar módulo de permissões por setor
```

## Uso principal

```bash
> criar módulo de permissões por setor por perfil
> status
> continue
> retome
> inspect
> replaneje com menos risco
> por que você escolheu enterprise?
> o que você alterou?
> config
> doctor
> debug status
> sair
```

## Configuração e chaves de API

- Arquivo global: `~/.config/harness/config.toml`
- Projeto: `.harness/project.toml`
- Variáveis de ambiente:
- `ANTHROPIC_API_KEY` (MiniMax)
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`
- `HARNESS_PROVIDER`
- `HARNESS_MODEL`
- `--provider`
- `--model`
- `--api-key`

Prioridade usada pelo agente:

1. flags explícitas
2. variáveis de ambiente
3. config local do projeto
4. config global

MiniMax é o padrão sugerido e compatível com API Anthropic (`https://api.minimax.io/anthropic`).

## Estrutura persistida no workspace

`harness` grava estado em `.harness/`:

```text
.harness/
  runs/
  artifacts/
  reports/
  logs/
  ledgers/
  session/
```

Isso permite:

- retomada automática,
- inspeção de sessão,
- trilha de events/logs por run ativa.

## Modo técnico (debug)

O modo técnico permanece disponível e segue separado do fluxo principal:

```bash
harness debug status
harness debug run "demand test"
harness debug continue
```

ou usando o CLI legado:

```bash
cvg status
cvg continue
```

Comandos técnicos continuam úteis para automação e integração, sem dominar a UX principal.

## Limitações atuais

- A conversão de texto livre para evidência técnica ainda é conservadora (semântica inicial).
- O front-agent prioriza governança e decisão, não substitui todo o patching automático por padrão.
- O modo headless/gRPC ainda está preparado estruturalmente, mas não é padrão ainda.
- O agente ainda não opera em autonomia irrestrita: há pontos de confirmação e aprovação quando há gating/human action ativo.

## Estrutura do projeto

```text
src/cvg_harness/
  app/               # front agent / sessão
  session/           # estado de conversa
  routing/           # roteador de intenções
  providers/         # MiniMax / OpenAI / OpenRouter
  workspace/         # state dir e gestão de workspace
  adapters/          # camada de integração futura
  runtime/           # utilitários de execução
  operator/          # engine operacional preservada
  cli/               # harness (novo) e cvg (técnico)
```

## Comandos úteis

- `harness` → inicia loop principal.
- `harness status` → status da run ativa.
- `harness resume` → retoma a run atual.
- `harness history` → histórico dos últimos turnos da sessão.
- `harness doctor` → health básico do agente.
- `harness config` → inicia onboarding novamente.
- `harness debug` → namespace técnico antigo.

Flags úteis para automação:

- `--json` : saída estruturada em `status`, `resume` e `history`.

## Validação recomendada

```bash
pytest -q
harness
```

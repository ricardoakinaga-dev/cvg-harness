# 0049 — Arquitetura Reconstruída no Padrão OpenClaude

## Princípios incorporados

- Interface única de terminal (`harness`) com conversa natural.
- Setup inicial guiado no primeiro uso.
- Separação entre front-end conversacional e serviços de execução.
- Router declarativo de intenção.
- Configuração persistida e workspace-aware.
- Fundação para headless (futuro: serviço local/gRPC).

## O que foi adotado

- `cli/harness.py`: ponto de entrada orientado a produto.
- `app/agent.py`: loop conversacional e controle do fluxo.
- `routing/`: detecção de intenção (`status`, `resume`, `continue`, etc.).
- `session/`: estado local de sessão por workspace.
- `providers/`: camada plugável (MiniMax/OpenAI/OpenRouter) com defaults e factory.
- `workspace/`: gerenciamento de diretório `.harness`.
- `cli/cli.py`: comandos técnicos isolados no namespace `debug`.
- `operator/` e módulos de governança: lógica de negócio preservada.

## O que foi adaptado para identidade própria

- Não houve cópia de brand, mensagens e termos de UX foram alinhados ao `Harness`.
- `minimax` passa a ser o provider padrão recomendado e já usa URL Anthropic-compatible (`https://api.minimax.io/anthropic`).
- Estrutura de estado mantém nomenclatura do projeto e contratos existentes de `run`, `ledger`, `event-log`, `artifacts`.

## Benefícios dessa estrutura

- Reduz acoplamento da antiga CLI técnica ao fluxo do usuário final.
- Permite evolução para headless sem destruir `cvg` legado.
- Mantém compatibilidade com automações que dependem de comandos antigos.

## Separação futura para core headless

A arquitetura já está segmentada de modo que, no futuro:

- `app/*` vira cliente/transport;
- `operator/*` e serviços de governança viram core persistível;
- `providers/*` e `adapters/*` podem ser expostos por canal local (HTTP/gRPC).

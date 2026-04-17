# 0048 — Limites Atuais do Agente e Roadmap

## O que já funciona no estado atual

- Agente conversacional principal com `harness`.
- Onboarding guiado e resolução de provider por prioridade.
- Persistência de sessão e resumibilidade (`.harness/session`, `current-run.txt`).
- Execução da engine original de governança sem reescrita.
- Namespace técnico preservado em `harness debug` e `cvg`.
- Registro de eventos/ledger/metrics conforme contratos existentes.

## Limitações reais

- O fluxo ainda opera com decisões majoritariamente heurísticas para transições de fase; não é um agente “multi-model autonomamente criativo”.
- Geração de código automático (patch) ainda não é o padrão por segurança; a rotina padrão prioriza planejamento e governança.
- A integração com runtime externo (CI, execução real, evidência externa) existe via adapters/execução opcional, mas não é mandatória no caminho padrão.
- A escolha de ferramenta é feita por contratos e estado de run; não há ainda seleção por otimização de custo em tempo real.
- Não há serviço headless publicado neste release (só estrutura preparada).

## Roadmap curto (próximos ciclos)

1. Ativar executor de alterações em modo controlado por policy.
2. Expandir `resume` para reconciliação de conversação com histórico completo de turns.
3. Expor serviços de sessão/estado em gRPC local para automação.
4. Melhorar observabilidade de custo/latência por provider.
5. Adicionar telemetria por modelo com feedback de qualidade de decisão.

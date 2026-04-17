# 0048 — Limites Atuais e Roadmap

## O que já está pronto

- Modo de agente terminal com loop conversacional (`harness`).
- Onboarding guiado e gestão de provider/model.
- Sessão persistida e retomada por workspace.
- Execução do core atual de governança sem reescrita (wrap de `OperatorService`).
- Namespace técnico preservado em `debug`.

## Limitações atuais (simulação/homologação)

- Conversão de texto livre para evidências ainda é limitada a padrão simples.
- O front-agent não cria e aplica patches de código sozinho por padrão (só executa fluxo de planejamento e validação da engine existente).
- A justificativa automática usa o contexto de classification disponível na artefatos atuais.

## Dependências futuras

- Headless gRPC:
  - separar entrada de CLI de serviços internos,
  - expor sessão de run e eventos via stream.
- Auto-execução de mudanças a partir de prompts ainda pode evoluir para modo executor opcional por política de segurança.

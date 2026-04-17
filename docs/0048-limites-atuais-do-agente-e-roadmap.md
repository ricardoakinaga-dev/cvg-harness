# 0048 — Limites Atuais do Agente e Roadmap

## O que funciona bem
- loop conversacional em português
- onboarding guiado
- execução da engine de governança preservada
- workspace-aware com persistência de estado
- retomada (`resume`) e inspeção (`inspect`)
- namespace técnico isolado (`harness debug ...`)

## Limitações atuais
- criação/promoção automática de patches ainda não é padrão (por segurança, confirmação humana em pontos críticos)
- decisão de execução ainda combina heurísticas e política de projeto
- autonomia total depende de evidência/human feedback em gates
- não existe ainda serviço headless oficial publicado (estrutura pronta para separar app/core)

## Próximos passos
1. endurecer runtime real de execução (shell/tool actions) com controles adicionais de política
2. aprimorar custo/latência por provider
3. evoluir modo headless (API local/gRPC) mantendo sessão e logs atuais
4. ampliar seleção de adapters externos via política de projeto sem sacrificar transparência

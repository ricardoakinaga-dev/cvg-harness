"""
Exemplo: Lint de SPEC
"""

from cvg_harness.linter.spec_linter import lint_spec

# SPEC válida
spec = {
    "version": "v1",
    "criterios": [
        {"descricao": "API retorna 200 OK", "testavel": True},
        {"descricao": "Erro retorna JSON válido", "testavel": True},
    ],
    "modulos": ["auth", "api", "middleware"],
    "edge_cases": ["token expirado", "payload vazio", "rate limit"],
    "limite_escopo": "apenas módulo auth",
    "areas_proibidas": ["legacy", "v1/deprecated"],
    "contratos": [
        {
            "nome": "login",
            "tipo": "api",
            "method": "POST",
            "path": "/api/auth/login",
            "exemplo_payload": {"email": "string", "password": "string"},
        }
    ],
    "fluxo_critico": True,
    "rollback": "reverter migração do banco",
    "observabilidade": "logs de auth + métricas de login",
}

report = lint_spec(spec, mode="ENTERPRISE")
print(f"Resultado: {report.result}")
print(f"Score: {report.score}")
print(f"Falhas bloqueantes: {report.blocking_issues}")
print(f"Warnings: {report.warnings}")
for f in report.findings:
    print(f"  [{f['severity']}] {f['rule']}: {f['message']}")

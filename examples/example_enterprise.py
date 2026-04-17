"""
Exemplo: Classificação de demanda ENTERPRISE
"""

from cvg_harness.classification.classifier import classify

# Nova integração de autenticação - alto impacto
dimensions = {
    "impacto_arquitetural": 3,
    "modulos_afetados": 2,
    "risco_de_regressao": 3,
    "criticidade_de_negocio": 3,
    "sensibilidade_de_dados": 3,
    "dependencia_externa": 2,
    "reversibilidade": 1,
    "complexidade_de_validacao": 2,
}

result = classify(
    project="cvg-harness",
    demand="novo fluxo de autenticação OAuth2",
    dimensions=dimensions,
    rationale="autenticação é crítica para segurança e afeta múltiplos módulos",
)

print(f"Modo: {result.mode}")
print(f"Score: {result.total_score}")
print(f"Dimensões: {result.dimensions}")
print(f"Override: {result.override_applied}")

"""
Exemplo: Classificação de demanda como FAST
"""

from cvg_harness.classification.classifier import classify, save_classification

# Demanda simples de ajuste em UI local
dimensions = {
    "impacto_arquitetural": 1,
    "modulos_afetados": 1,
    "risco_de_regressao": 1,
    "criticidade_de_negocio": 0,
    "sensibilidade_de_dados": 0,
    "dependencia_externa": 0,
    "reversibilidade": 1,
    "complexidade_de_validacao": 1,
}

result = classify(
    project="cvg-harness",
    demand="ajuste de cor em botão da UI",
    dimensions=dimensions,
    rationale="mudança local, baixo impacto, reversível",
)

print(f"Modo: {result.mode}")
print(f"Score: {result.total_score}")
print(f"Override: {result.override_applied}")
print(f"Timestamp: {result.timestamp}")
print(f"Rationale: {result.rationale}")

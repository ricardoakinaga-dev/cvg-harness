#!/usr/bin/env python3
"""
Exemplo: Evaluator e Release Readiness
Valida sprint e decide prontidão para release.
"""

from cvg_harness.evaluator.evaluator import Evaluator
from cvg_harness.release.release_readiness import ReleaseReadinessEngine

# SPEC
spec = {
    "meta": "adição de autenticação",
    "criterios": [
        {"descricao": "login com credenciais retorna token", "testavel": True},
        {"descricao": "token expirado retorna 401", "testavel": True},
        {"descricao": "refresh token funciona", "testavel": True},
    ],
}

# Avaliação da sprint
evaluator = Evaluator()

# Cenário 1: Aprovado
print("=== CENÁRIO 1: Sprint Aprovada ===")
report = evaluator.evaluate(
    sprint_id="SPRINT-1",
    spec=spec,
    evidence_files=["implementação dos arquivos", "testes unitários", "logs de execução"],
    guard_report={"result": "PASS"},
)
print(f"Resultado: {report.result}")
print(f"Próxima ação: {report.next_action}")
print(f"Round: {report.round}")
print()

# Cenário 2: Falhou - evidências faltando
print("=== CENÁRIO 2: Evidências Faltando ===")
report2 = evaluator.evaluate(
    sprint_id="SPRINT-1",
    spec=spec,
    evidence_files=["implementação"],  # faltam evidências
)
print(f"Resultado: {report2.result}")
print(f"Evidências faltando: {report2.evidence_missing}")
print(f"Próxima ação: {report2.next_action}")
print()

# Cenário 3: Architecture Guardian reprovou
print("=== CENÁRIO 3: Guard Reprova ===")
report3 = evaluator.evaluate(
    sprint_id="SPRINT-1",
    spec=spec,
    evidence_files=["implementação dos arquivos", "testes unitários", "logs de execução"],
    guard_report={"result": "FAIL", "violations": [{"rule": "prohibited_area_touched"}]},
)
print(f"Resultado: {report3.result}")
for cr in report3.criterion_results:
    if cr["status"] == "failed":
        print(f"  Falhou: {cr['criterion']} - {cr.get('notes', '')}")
print()

# Release Readiness
print("=== RELEASE READINESS ===")
engine = ReleaseReadinessEngine()
gate_results = [
    {"gate": "GATE_0", "state": "approved", "blockers": []},
    {"gate": "GATE_1", "state": "approved", "blockers": []},
    {"gate": "GATE_3", "state": "approved", "blockers": []},
    {"gate": "GATE_4", "state": "approved", "blockers": []},
    {"gate": "GATE_7", "state": "approved", "blockers": []},
]
evaluation = {"result": "PASSED"}
drift = {"result": "CLEAN", "findings": []}

readiness = engine.assess("projeto-x", "adição de auth", gate_results, evaluation, drift)
print(f"Decisão: {readiness.decision}")
print(f"Riscos residuais: {readiness.residual_risks}")
print(f"Exceções: {readiness.exceptions}")

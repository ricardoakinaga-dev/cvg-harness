#!/usr/bin/env python3
"""
Exemplo: Fallback e rejeição de release
Simula cenários de falha de avaliação e release com trilha operacional explícita.

Este exemplo é demonstrativo e não altera fluxo/código de produção.
"""

from cvg_harness.evaluator.evaluator import Evaluator
from cvg_harness.fallback.fallback_policy import FallbackPolicy
from cvg_harness.release.release_readiness import ReleaseReadinessEngine


def print_section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


spec = {
    "meta": "adição de autenticação",
    "criterios": [
        {"descricao": "login com credenciais retorna token", "testavel": True},
        {"descricao": "token expirado retorna 401", "testavel": True},
        {"descricao": "refresh token funciona", "testavel": True},
    ],
}

evaluator = Evaluator()
policy = FallbackPolicy()
release_engine = ReleaseReadinessEngine()

# Cenário 1 — aprovação limpa
print_section("CENÁRIO A: AVALIAÇÃO APROVADA")
report = evaluator.evaluate(
    sprint_id="SPRINT-1",
    spec=spec,
    evidence_files=["implementação dos arquivos", "testes unitários", "logs de execução"],
    guard_report={"result": "PASS"},
)
print(f"Resultado: {report.result}")
print(f"next_action: {report.next_action}")  # esperado vazio
print(f"Round: {report.round}")

# Cenário 2 — falha com fallback (round 1 e round 2)
print_section("CENÁRIO B: EVIDÊNCIAS INSUFICIENTES (ROUND 1 / ROUND 2)")
for round_count in (1, 2):
    report_fail = evaluator.evaluate(
        sprint_id="SPRINT-1",
        spec=spec,
        evidence_files=["implementação"],  # faltam evidências esperadas
    )
    fallback = policy.evaluate_evaluator_failure(
        round_count=round_count,
        spec=spec,
        sprint={"id": "SPRINT-1"},
    )
    print(f"Round {round_count} -> resultado: {report_fail.result}")
    print(f"  next_action: {report_fail.next_action}")
    print(f"  fallback: {fallback.action} ({fallback.details})")

# Cenário 3 — release rejeitado por condição objetiva
print_section("CENÁRIO C: RELEASE REJEITADO")
gate_results = [
    {"gate": "GATE_0", "state": "approved", "blockers": []},
    {"gate": "GATE_1", "state": "approved", "blockers": []},
    {"gate": "GATE_5", "state": "rejected", "blockers": ["especificação incompleta"]},
]
evaluation = {"result": "FAILED"}
drift = {"result": "CLEAN", "findings": []}

readiness = release_engine.assess(
    project="projeto-x",
    feature="adição de auth",
    gate_results=gate_results,
    evaluation_report=evaluation,
    drift_report=drift,
)
print(f"Decisão: {readiness.decision}")
print(f"Residual risks: {readiness.residual_risks}")
print(f"Missing gates: {readiness.missing_gates}")

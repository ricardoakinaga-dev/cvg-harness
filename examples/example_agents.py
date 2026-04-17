#!/usr/bin/env python3
"""
Exemplo: Agentes (Coder Worker, Replan Coordinator, Metrics Aggregator)
"""

from cvg_harness.coder.coder_worker import CoderWorker
from cvg_harness.replan.replan_coordinator import ReplanCoordinator, ReplanTrigger
from cvg_harness.metrics_agg.metrics_aggregator import MetricsAggregator

# === Coder Worker ===
print("=== CODER WORKER ===")
coder = CoderWorker(
    authorized_areas=["src/auth", "src/api"],
    prohibited_areas=["src/legacy", "src/v1/deprecated"],
)

# Teste 1: Arquivo válido
is_valid, violations = coder.validate_scope(["src/auth/login.py", "src/api/users.py"])
print(f"Scope válido: {is_valid}")

# Teste 2: Arquivo proibido
is_valid, violations = coder.validate_scope(["src/legacy/old_login.py"])
print(f"Scope válido (proibido): {is_valid}")
print(f"Violações: {violations}")

# Teste 3: Deliverable
deliverable = coder.deliver(
    sprint_id="SPRINT-1",
    arquivos_alterados=["src/auth/token.py"],
    racional="implementou refresh token",
    evidencias=["implementação", "testes unitários", "logs"],
    testes_passaram=True,
    lint_passou=True,
)
print(f"Entrega: {deliverable.sprint_id}, issues: {len(deliverable.issues)}")
print()

# === Replan Coordinator ===
print("=== REPLAN COORDINATOR ===")
coordinator = ReplanCoordinator()

# Cenário 1: 3 falhas do evaluator
decision = coordinator.evaluate(
    trigger=ReplanTrigger.EVALUATOR_FAILURES.value,
    context={"failures": 3},
)
print(f"3 falhas: ação={decision.action}, artifacts={decision.affected_artifacts}")

# Cenário 2: Architecture guard failure
decision = coordinator.evaluate(
    trigger=ReplanTrigger.ARCHITECTURE_GUARD_FAILURES.value,
    context={},
)
print(f"Arch guard fail: ação={decision.action}")

# Cenário 3: Sprint overflow
decision = coordinator.evaluate(
    trigger=ReplanTrigger.SPRINT_OVERFLOW.value,
    context={},
)
print(f"Sprint overflow: ação={decision.action}")

# Cenário 4: Misclassification
decision = coordinator.evaluate(
    trigger=ReplanTrigger.MISCLASSIFICATION.value,
    context={},
    current_classification={"mode": "FAST"},
)
print(f"Misclassification: ação={decision.action}")
print()

# === Metrics Aggregator ===
print("=== METRICS AGGREGATOR ===")
agg = MetricsAggregator()

# Sem dados
metrics = agg.aggregate("projeto-x", "feature de auth", "ENTERPRISE")
print(f"Projeto: {metrics.project}")
print(f"Mode: {metrics.mode}")
print(f"Pass rate: {metrics.pass_rate}")
print(f"Sprints: {metrics.sprints_count}")
print(f"Gate blocks: {metrics.gates_blocked_count}")
print(f"Falhas por tipo: {metrics.failures_by_type}")

# Agregação por agente
print("\nAgregação por agente:")
for agent, am in metrics.agent_metrics.items():
    print(f"  {agent}: completed={am.tasks_completed}, failed={am.tasks_failed}")

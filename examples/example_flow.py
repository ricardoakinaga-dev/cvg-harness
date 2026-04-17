"""
Exemplo: Fluxo completo de uma sprint
"""

from pathlib import Path
import tempfile
import os

from cvg_harness.classification.classifier import classify, save_classification, load_classification
from cvg_harness.linter.spec_linter import lint_spec
from cvg_harness.guardian.architecture_guardian import ArchitectureGuardian
from cvg_harness.drift.drift_detector import DriftDetector
from cvg_harness.ledger.progress_ledger import ProgressLedger, save_progress, load_progress
from cvg_harness.ledger.event_log import Event, EventLog
from cvg_harness.fallback.fallback_policy import FallbackPolicy

# 1. Classificar demanda
dimensions = {
    "impacto_arquitetural": 1,
    "modulos_afetados": 1,
    "risco_de_regressao": 1,
    "criticidade_de_negocio": 1,
    "sensibilidade_de_dados": 0,
    "dependencia_externa": 0,
    "reversibilidade": 1,
    "complexidade_de_validacao": 1,
}

result = classify("projeto-x", "adição de campo", dimensions, "low impact change")
print(f"Classificado: {result.mode}")

# 2. Architecture Guardian
guardian = ArchitectureGuardian(
    authorized_areas=["src/features/auth", "src/api"],
    prohibited_areas=["src/legacy", "src/v1"],
)
guard_report = guardian.check(
    changed_files=["src/features/auth/login.py"],
    new_dependencies=[],
)
print(f"Architecture Guard: {guard_report.result}")

# 3. Drift Detector
detector = DriftDetector(sprint_id="SPRINT-1")
drift_report = detector.detect(
    intake={"problema": "autenticação lenta"},
    prd={"problema": "autenticação lenta"},
    spec={"meta": "otimizar autenticação"},
    sprint_plan={"sprints": [{"modulos": ["auth"]}]},
)
print(f"Drift: {drift_report.result}")

# 4. Progress Ledger
ledger = ProgressLedger.new("projeto-x", "adição de campo", "FAST")
ledger.update_gate("GATE_0", "approved")
ledger.update_gate("GATE_1", "approved")
ledger.current_sprint = "SPRINT-1"
print(f"Gate atual: {ledger.current_gate}")

# 5. Event Log
tmpdir = tempfile.mkdtemp()
log_path = Path(tmpdir) / "event-log.jsonl"
event_log = EventLog(log_path)
event_log.append(Event.create("demand_classified", "intake-classifier", "classification.json"))
event_log.append(Event.create("sprint_started", "orchestrator", "SPRINT-1"))
print(f"Eventos no log: {event_log.count()}")

# 6. Fallback Policy
policy = FallbackPolicy()
fallback = policy.evaluate_evaluator_failure(round_count=1, spec={}, sprint={})
print(f"Fallback: {fallback.action}")

# Cleanup
import shutil
shutil.rmtree(tmpdir)

print("\nFluxo completo executado com sucesso!")

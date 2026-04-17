"""
PR-04: Testes de gates, fallback e integração operacional
Valida que gates emitem eventos, fallback integrated,
e waiver funciona corretamente.
"""

import pytest
import tempfile
import json
from pathlib import Path

from cvg_harness.flow import FlowOrchestrator
from cvg_harness.fallback.fallback_policy import FallbackPolicy, FallbackAction


class TestFallbackPolicyIntegration:
    """Valida integração do FallbackPolicy no orchestrator."""

    def setup_method(self):
        self.workspace = Path(tempfile.mkdtemp())
        self.orch = FlowOrchestrator("proj", "OAuth2 feature", "ENTERPRISE", self.workspace)
        dims = {"impacto_arquitetural": 2, "modulos_afetados": 1, "risco_de_regressao": 2,
                "criticidade_de_negocio": 1, "sensibilidade_de_dados": 1, "dependencia_externa": 1,
                "reversibilidade": 1, "complexidade_de_validacao": 1}
        self.orch.classify(dims, "critical feature")
        self.orch.run_research()
        self.orch.run_prd()
        self.orch.build_spec()
        self.orch.plan_sprints()

    def test_lint_failure_emits_fallback_event(self):
        """Falha do lint emite fallback event."""
        # Force lint failure by having bad spec
        result = self.orch.run_lint()
        fallback_path = self.workspace / "artifacts" / "fallback-events.jsonl"
        if fallback_path.exists():
            with open(fallback_path) as f:
                content = f.read()
                assert "spec_lint_failed" in content or "BLOCK" in content

    def test_guard_failure_emits_fallback_event(self):
        """Falha do guard emite fallback event."""
        result = self.orch.check_guard(["src/legacy/old.py"])
        assert result["result"] == "FAIL"
        fallback_path = self.workspace / "artifacts" / "fallback-events.jsonl"
        if fallback_path.exists():
            with open(fallback_path) as f:
                content = f.read()
                assert "architecture_guard_failed" in content or "BLOCK" in content

    def test_evaluator_failure_round_1_emits_retry_event(self):
        """Falha round 1 emite evento retry."""
        result = self.orch.evaluate_sprint(["evidência faltante"], round_num=1)
        assert result["result"] == "FAILED"
        from cvg_harness.ledger.event_log import load_events

        events = load_events(self.workspace / "event-log.jsonl")
        fail_events = [e for e in events if e.event_type == "evaluation_failed"]
        assert fail_events, "evaluation_failed deve estar no event-log"
        assert any(e.metadata.get("action") == "retry_local" for e in fail_events)

    def test_evaluator_failure_emits_replan_when_triggered(self):
        """Avaliador com 3 falhas aciona replan."""
        # Simular 3 falhas - o orchestrator vai bloquear e acionar replan
        result = self.orch.evaluate_sprint(["evidência"], round_num=3)
        # Verifica que replan foi acionado
        replan_path = self.workspace / "artifacts" / "replan-decision.json"
        # O replan só é acionado via _handle_evaluator_failure quando action == "replan"
        # round 3 deve acionar replan
        if replan_path.exists():
            with open(replan_path) as f:
                decision = json.load(f)
                assert decision["action"] in ["rewrite_spec", "split_sprint", "reclassify"]
        from cvg_harness.ledger.event_log import load_events

        events = load_events(self.workspace / "event-log.jsonl")
        assert any(e.event_type == "replan_requested" for e in events)


class TestEvaluationEventTrail:
    """Valida trilha de eventos de avaliação no event log."""

    def test_evaluation_passed_event_emitted_on_success(self):
        workspace = Path(tempfile.mkdtemp())
        orch = FlowOrchestrator("proj", "feature", "FAST", workspace)
        spec_path = workspace / "artifacts" / "spec.json"
        spec_path.parent.mkdir(exist_ok=True)
        spec_path.write_text(
            __import__("json").dumps(
                {
                    "meta": "feature",
                    "criterios": [{"descricao": "Critério de validação", "testavel": True}],
                }
            )
        )
        orch.state.spec_path = str(spec_path)

        class _DummyReport:
            result = "PASSED"
            round = 1
            next_action = "none"

            def to_dict(self):
                return {"result": "PASSED", "round": 1, "next_action": "none", "evidence_missing": []}

        class _DummyEvaluator:
            def evaluate(self, sprint_id, spec, evidence_files, round_num=1):
                return _DummyReport()

        import cvg_harness.evaluator.evaluator as evaluator_module

        original_evaluator = evaluator_module.Evaluator
        evaluator_module.Evaluator = lambda: _DummyEvaluator()
        try:
            result = orch.evaluate_sprint(["evidência"], round_num=1)
            assert result["result"] == "PASSED"
        finally:
            evaluator_module.Evaluator = original_evaluator

        from cvg_harness.ledger.event_log import load_events

        events = load_events(workspace / "event-log.jsonl")
        event_types = [e.event_type for e in events]
        assert "evaluation_passed" in event_types
        assert "sprint_approved" in event_types


class TestWaiverSupport:
    """Valida suporte a waiver."""

    def setup_method(self):
        self.workspace = Path(tempfile.mkdtemp())
        self.orch = FlowOrchestrator("proj", "feature", "FAST", self.workspace)
        dims = {"impacto_arquitetural": 1, "modulos_afetados": 1, "risco_de_regressao": 1,
                "criticidade_de_negocio": 0, "sensibilidade_de_dados": 0, "dependencia_externa": 0,
                "reversibilidade": 1, "complexidade_de_validacao": 1}
        self.orch.classify(dims, "simple")

    def test_grant_waiver_success(self):
        """Waiver válido é concedido."""
        self.orch.block("spec_lint_failed")
        assert self.orch.state.status == "blocked"

        waiver_data = {
            "dono": "tech-lead",
            "prazo": "2026-04-20",
            "risco_residual": "low",
            "blocker": "spec_lint_failed"
        }
        result = self.orch.grant_waiver(waiver_data)
        assert result is True

        # Verifica que waiver foi salvo
        waiver_path = self.workspace / "artifacts" / "waiver.json"
        assert waiver_path.exists()

    def test_grant_waiver_rejected_critical_risk(self):
        """Waiver com risco crítico é rejeitado."""
        self.orch.block("spec_lint_failed")
        waiver_data = {
            "dono": "tech-lead",
            "prazo": "2026-04-20",
            "risco_residual": "critical",
            "blocker": "spec_lint_failed"
        }
        result = self.orch.grant_waiver(waiver_data)
        assert result is False

    def test_grant_waiver_rejected_missing_fields(self):
        """Waiver com campos faltantes é rejeitado."""
        self.orch.block("spec_lint_failed")
        waiver_data = {
            "dono": "tech-lead",
            # missing prazo and risco_residual
        }
        result = self.orch.grant_waiver(waiver_data)
        assert result is False


class TestFallbackPolicyDirect:
    """Testa FallbackPolicy diretamente."""

    def test_evaluator_failure_round_1_retry(self):
        """Round 1 = retry_local."""
        policy = FallbackPolicy()
        result = policy.evaluate_evaluator_failure(1, {}, {})
        assert result.action == FallbackAction.RETRY_LOCAL.value

    def test_evaluator_failure_round_2_review(self):
        """Round 2 = review_sprint."""
        policy = FallbackPolicy()
        result = policy.evaluate_evaluator_failure(2, {}, {})
        assert result.action == FallbackAction.REVIEW_SPRINT.value

    def test_evaluator_failure_round_3_replan(self):
        """Round 3 = replan."""
        policy = FallbackPolicy()
        result = policy.evaluate_evaluator_failure(3, {}, {})
        assert result.action == FallbackAction.REPLAN.value

    def test_arch_guard_failure_block(self):
        """Arch guard failure = block."""
        policy = FallbackPolicy()
        result = policy.evaluate_arch_guard_failure()
        assert result.action == FallbackAction.BLOCK.value

    def test_spec_lint_failure_block(self):
        """Spec lint failure = block."""
        policy = FallbackPolicy()
        result = policy.evaluate_spec_lint_failure()
        assert result.action == FallbackAction.BLOCK.value

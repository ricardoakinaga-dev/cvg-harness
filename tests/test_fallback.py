"""
Testes para Fallback Policy.
"""

import pytest
from cvg_harness.fallback.fallback_policy import (
    FallbackPolicy, FallbackAction, can_grant_waiver, Waiver
)


def test_fallback_evaluator_round_1():
    policy = FallbackPolicy()
    event = policy.evaluate_evaluator_failure(round_count=1, spec={}, sprint={})
    assert event.action == FallbackAction.RETRY_LOCAL.value


def test_fallback_evaluator_round_2():
    policy = FallbackPolicy()
    event = policy.evaluate_evaluator_failure(round_count=2, spec={}, sprint={})
    assert event.action == FallbackAction.REVIEW_SPRINT.value


def test_fallback_evaluator_round_3():
    policy = FallbackPolicy()
    event = policy.evaluate_evaluator_failure(round_count=3, spec={}, sprint={})
    assert event.action == FallbackAction.REPLAN.value


def test_fallback_arch_guard_failure():
    policy = FallbackPolicy()
    event = policy.evaluate_arch_guard_failure()
    assert event.action == FallbackAction.BLOCK.value
    assert "architecture_guard_failed" in event.trigger


def test_fallback_spec_lint_failure():
    policy = FallbackPolicy()
    event = policy.evaluate_spec_lint_failure()
    assert event.action == FallbackAction.BLOCK.value


def test_waiver_can_be_granted():
    waiver_data = {
        "dono": "tech-lead",
        "prazo": "2026-04-20",
        "risco_residual": "low",
    }
    assert can_grant_waiver(waiver_data) is True


def test_waiver_critical_rejected():
    waiver_data = {
        "dono": "tech-lead",
        "prazo": "2026-04-20",
        "risco_residual": "critical",
    }
    assert can_grant_waiver(waiver_data) is False


def test_waiver_incomplete_rejected():
    assert can_grant_waiver({"dono": "lead"}) is False
    assert can_grant_waiver({"prazo": "2026-04-20"}) is False

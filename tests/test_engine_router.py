"""Testes de roteamento de engine para garantir pipelines executáveis completas."""

from cvg_harness.routing import decide_route


def test_decide_route_fast_includes_implementation_step() -> None:
    route = decide_route(
        intent="ajustar texto no cabeçalho do sistema",
        supported_models=["MiniMax-M2.7-highspeed", "MiniMax-M2.7"],
    )
    assert route.mode == "FAST"
    assert "implement" in route.pipeline
    assert route.pipeline.index("implement") > route.pipeline.index("sprint_planner")
    assert route.subagents == [
        "research",
        "prd",
        "spec_builder",
        "spec_linter",
        "sprint_planner",
        "implement",
        "evaluator",
        "metrics_aggregator",
    ]


def test_decide_route_enterprise_includes_implementation_and_governance_steps() -> None:
    route = decide_route(
        intent="implementar fluxo de pagamento e faturamento com validação de segurança enterprise",
        supported_models=["MiniMax-M2.7-highspeed", "MiniMax-M2.7"],
    )
    assert route.mode == "ENTERPRISE"
    assert route.require_human_confirmation is True
    assert "implement" in route.pipeline
    assert "architecture_guardian" in route.pipeline
    assert "evaluator" in route.pipeline
    assert "drift_detector" in route.pipeline
    assert "release_readiness" in route.pipeline

"""Auto-router for subagent/tool/model selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from cvg_harness.classification.classifier import calculate_mode
from cvg_harness.operator.service import infer_dimensions_from_demand


@dataclass
class EngineRoute:
    """Resultado de decisão de roteamento interno."""

    intent: str
    mode: str
    model: str
    subagents: list[str]
    tools: list[str]
    pipeline: list[str]
    require_human_confirmation: bool
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "mode": self.mode,
            "model": self.model,
            "subagents": self.subagents,
            "tools": self.tools,
            "pipeline": self.pipeline,
            "require_human_confirmation": self.require_human_confirmation,
            "rationale": self.rationale,
        }


def _is_enterprise_hint(text: str) -> bool:
    lowered = text.lower()
    if "enterprise" in lowered:
        return True
    for hint in [
        "segurança",
        "oauth",
        "payment",
        "fatur",
        "finance",
        "core",
        "api",
        "conflito",
        "integra",
        "regress",
    ]:
        if hint in lowered:
            return True
    return False


def _is_high_risk(dimensions: dict[str, int]) -> bool:
    return any(value >= 3 for value in dimensions.values())


def pick_model_for_mode(mode: str, supported_models: list[str]) -> str:
    mode = (mode or "FAST").upper()
    if not supported_models:
        return ""

    if mode == "FAST":
        for model in supported_models:
            if "highspeed" in model.lower():
                return model
        return supported_models[0]

    for model in supported_models:
        if "highspeed" not in model.lower():
            return model
    return supported_models[0]


def _select_pipeline(mode: str, high_risk: bool) -> list[str]:
    # Ordenado para mapear uma pipeline de governança real.
    pipeline = [
        "classification",
        "research",
        "prd",
        "spec_builder",
        "spec_linter",
        "sprint_planner",
    ]

    if mode == "ENTERPRISE" or high_risk:
        pipeline += [
            "architecture_guardian",
            "evaluator",
            "drift_detector",
            "release_readiness",
        ]
        if high_risk:
            pipeline += ["replan_coordinator"]
    else:
        pipeline.append("evaluator")

    pipeline.append("metrics_aggregator")
    return pipeline


def decide_route(
    intent: str,
    supported_models: list[str],
    preferred_model: Optional[str] = None,
) -> EngineRoute:
    """Decide how this demand should be executed."""

    dimensions, rationale = infer_dimensions_from_demand(intent)
    mode = calculate_mode(dimensions)
    high_risk = _is_high_risk(dimensions) or _is_enterprise_hint(intent)
    if preferred_model:
        model = preferred_model
    else:
        model = pick_model_for_mode(mode, supported_models)

    if mode == "FAST":
        subagents = [
            "research",
            "prd",
            "spec_builder",
            "spec_linter",
            "sprint_planner",
            "evaluator",
            "metrics_aggregator",
        ]
        pipeline = _select_pipeline(mode, high_risk)
    else:
        subagents = [
            "research",
            "prd",
            "spec_builder",
            "spec_linter",
            "sprint_planner",
            "architecture_guardian",
            "evaluator",
            "drift_detector",
            "release_readiness",
            "replan_coordinator",
            "metrics_aggregator",
        ]
        pipeline = _select_pipeline(mode, high_risk)

    tools = [
        "filesystem",
        "shell",
        "planning",
        "subagent",
        "context_memory",
    ]

    return EngineRoute(
        intent=intent,
        mode=mode,
        model=model,
        subagents=subagents,
        tools=tools,
        pipeline=pipeline,
        require_human_confirmation=mode == "ENTERPRISE" or high_risk,
        rationale=(
            rationale
            + f" | pipeline={','.join(pipeline)} | high_risk={high_risk}"
        ),
    )


__all__ = ["EngineRoute", "decide_route", "pick_model_for_mode"]

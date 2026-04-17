"""
Testes para o Flow Orchestrator.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path

from cvg_harness.flow import FlowOrchestrator, FlowState


def test_flow_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        orch = FlowOrchestrator("proj", "feature", "FAST", Path(tmpdir))
        assert orch.project == "proj"
        assert orch.feature == "feature"
        assert orch.mode == "FAST"
        assert orch.state.current_phase == "intake"
        assert orch.state.status == "running"


def test_flow_classify():
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        orch = FlowOrchestrator("proj", "feature", "FAST", workspace)
        dims = {"impacto_arquitetural": 1, "modulos_afetados": 1}
        path = orch.classify(dims, "low impact")
        assert Path(path).exists()
        assert orch.state.classification_path == str(path)
        assert orch.state.last_event == "demand_classified"


def test_flow_emits_entry_events():
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        orch = FlowOrchestrator("proj", "feature", "FAST", workspace)
        dims = {"impacto_arquitetural": 1, "modulos_afetados": 1}
        orch.classify(dims, "low impact")
        orch.run_research()

        events = []
        with open(workspace / "event-log.jsonl") as f:
            for line in f:
                events.append(json.loads(line))

        event_types = [event["event_type"] for event in events]
        assert "demand_received" in event_types
        assert "research_started" in event_types
        assert event_types.index("demand_received") < event_types.index("demand_classified")
        assert event_types.index("research_started") < event_types.index("research_approved")


def test_flow_advance_phase():
    with tempfile.TemporaryDirectory() as tmpdir:
        orch = FlowOrchestrator("proj", "feature", "FAST", Path(tmpdir))
        orch.advance_phase("spec")
        assert orch.state.current_phase == "spec"


def test_flow_block():
    with tempfile.TemporaryDirectory() as tmpdir:
        orch = FlowOrchestrator("proj", "feature", "FAST", Path(tmpdir))
        orch.block("spec_lint_failed")
        assert orch.state.status == "blocked"
        assert "spec_lint_failed" in orch.state.blockers


def test_flow_save_and_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        orch1 = FlowOrchestrator("proj", "feature", "ENTERPRISE", workspace)
        orch1.advance_phase("lint")
        orch1.block("arch_guard")

        orch2 = FlowOrchestrator.load(workspace)
        assert orch2.project == "proj"
        assert orch2.state.current_phase == "lint"
        assert orch2.state.blockers == ["arch_guard"]

"""
Testes para Progress Ledger e Event Log.
"""

import pytest
import tempfile
import os
from pathlib import Path

from cvg_harness.ledger.progress_ledger import ProgressLedger, save_progress, load_progress
from cvg_harness.ledger.event_log import Event, EventLog, save_event, load_events
from cvg_harness.ledger.event_log import EVENT_TYPES as EVENT_LOG_EVENT_TYPES
from cvg_harness.types import EVENT_TYPES as CANONICAL_EVENT_TYPES


def test_progress_ledger_new():
    ledger = ProgressLedger.new("proj", "feature", "FAST")
    assert ledger.project == "proj"
    assert ledger.feature == "feature"
    assert ledger.mode == "FAST"
    assert ledger.status == "in_progress"
    assert ledger.current_gate == "GATE_0"


def test_progress_ledger_update_gate():
    ledger = ProgressLedger.new("proj", "feature", "FAST")
    ledger.update_gate("GATE_1", "approved")
    assert ledger.gates["GATE_1"] == "approved"
    assert ledger.current_gate == "GATE_1"


def test_progress_ledger_blocker():
    ledger = ProgressLedger.new("proj", "feature", "FAST")
    ledger.add_blocker("spec_incomplete")
    assert "spec_incomplete" in ledger.blockers
    ledger.clear_blocker("spec_incomplete")
    assert "spec_incomplete" not in ledger.blockers


def test_progress_persistence():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        path = Path(f.name)
    try:
        ledger = ProgressLedger.new("proj", "feature", "ENTERPRISE")
        ledger.add_blocker("test_blocker")
        save_progress(ledger, path)
        loaded = load_progress(path)
        assert loaded.project == "proj"
        assert loaded.mode == "ENTERPRISE"
        assert "test_blocker" in loaded.blockers
    finally:
        os.unlink(path)


def test_event_create():
    event = Event.create("sprint_approved", "evaluator", "sprint-1")
    assert event.event_type == "sprint_approved"
    assert event.actor == "evaluator"
    assert event.artifact_ref == "sprint-1"
    assert event.timestamp is not None


def test_event_log_append():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as f:
        path = Path(f.name)
    try:
        log = EventLog(path)
        e1 = Event.create("demand_classified", "intake-classifier", "demand-1")
        e2 = Event.create("sprint_started", "orchestrator", "sprint-1")
        log.append(e1)
        log.append(e2)
        events = log.query()
        assert len(events) == 2
        assert log.count("sprint_started") == 1
    finally:
        os.unlink(path)


def test_event_type_registry_is_single_source_of_truth():
    assert EVENT_LOG_EVENT_TYPES == CANONICAL_EVENT_TYPES
    assert "architecture_guard_passed" in EVENT_LOG_EVENT_TYPES
    assert "drift_clean" in EVENT_LOG_EVENT_TYPES
    assert "drift_detected" in EVENT_LOG_EVENT_TYPES
    assert "gate_approved" in EVENT_LOG_EVENT_TYPES
    assert "gate_rejected" in EVENT_LOG_EVENT_TYPES

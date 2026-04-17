"""
REPL interativo para o CVG Harness.
Executa comandos de forma interativa em um loop.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from cvg_harness.flow import FlowOrchestrator
from cvg_harness.classification.classifier import classify, save_classification
from cvg_harness.linter.spec_linter import lint_spec
from cvg_harness.guardian.architecture_guardian import ArchitectureGuardian
from cvg_harness.drift.drift_detector import DriftDetector
from cvg_harness.ledger.progress_ledger import ProgressLedger, load_progress
from cvg_harness.ledger.event_log import EventLog
from cvg_harness.metrics.metrics_catalog import DeliveryMetrics


class REPL:
    """REPL interativo para operação do harness."""

    COMMANDS = [
        "classify", "lint", "guard", "drift", "progress",
        "events", "state", "set-phase", "block", "unblock",
        "metrics", "template", "help", "exit",
    ]

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or Path.cwd() / ".cvg-harness"
        self.orchestrator: Optional[FlowOrchestrator] = None
        self.running = True

    def run(self) -> None:
        print("CVG Harness REPL")
        print("Type 'help' for commands, 'exit' to quit.\n")

        while self.running:
            try:
                prompt = self._prompt()
                line = input(prompt).strip()
                if not line:
                    continue
                self._execute(line)
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\n(Use 'exit' to quit)")
            except Exception as e:
                print(f"Error: {e}")

        print("\nGoodbye.")

    def _prompt(self) -> str:
        if self.orchestrator:
            phase = self.orchestrator.state.current_phase
            gate = self.orchestrator.state.current_gate
            status = self.orchestrator.state.status
            return f"[{phase}|{gate}|{status}] cvg> "
        return "cvg> "

    def _execute(self, line: str) -> None:
        parts = line.split()
        cmd = parts[0]

        if cmd == "help":
            self._help()
        elif cmd == "exit":
            self.running = False
        elif cmd == "classify":
            self._cmd_classify(parts)
        elif cmd == "lint":
            self._cmd_lint()
        elif cmd == "guard":
            self._cmd_guard(parts)
        elif cmd == "drift":
            self._cmd_drift()
        elif cmd == "progress":
            self._cmd_progress()
        elif cmd == "events":
            self._cmd_events(parts)
        elif cmd == "state":
            self._cmd_state()
        elif cmd == "set-phase":
            self._cmd_set_phase(parts)
        elif cmd == "block":
            self._cmd_block(parts)
        elif cmd == "unblock":
            self._cmd_unblock(parts)
        elif cmd == "metrics":
            self._cmd_metrics()
        elif cmd == "template":
            self._cmd_template(parts)
        elif cmd == "init":
            self._cmd_init(parts)
        else:
            print(f"Unknown command: {cmd}. Type 'help' for available commands.")

    def _help(self) -> None:
        print("""
Available commands:
  init <project> <feature> <mode>  Initialize a new flow
  classify <json_dims> <rationale>  Classify demand
  lint                              Run spec linter
  guard <files>                     Check architectural adherence
  drift                             Detect drift between layers
  progress                          Show progress ledger
  events [--type <event_type>]      Show event log
  state                             Show current flow state
  set-phase <phase>                 Set current phase
  block <reason>                    Block the flow
  unblock <reason>                  Remove a blocker
  metrics                           Show delivery metrics
  template <type>                   Show template (prd|spec|sprint)
  exit                              Exit REPL
""")

    def _cmd_init(self, parts: list[str]) -> None:
        if len(parts) < 4:
            print("Usage: init <project> <feature> <mode>")
            return
        project, feature, mode = parts[1], parts[2], parts[3]
        self.workspace = Path.cwd() / f".cvg-harness-{feature.replace(' ', '-')}"
        self.orchestrator = FlowOrchestrator(project, feature, mode, self.workspace)
        print(f"Flow initialized: {self.workspace}")
        print(f"Mode: {mode}, Gate: GATE_0, Phase: intake")

    def _cmd_classify(self, parts: list[str]) -> None:
        if not self.orchestrator:
            print("Flow not initialized. Use 'init' first.")
            return
        try:
            dims = json.loads(parts[1]) if len(parts) > 1 else {}
            rationale = parts[2] if len(parts) > 2 else ""
        except json.JSONDecodeError:
            print("Invalid JSON for dimensions")
            return
        path = self.orchestrator.classify(dims, rationale)
        state = self.orchestrator.state
        print(f"Classification saved: {path}")
        print(f"Mode: {state.mode}, Score: check {path}")

    def _cmd_lint(self) -> None:
        if not self.orchestrator:
            print("Flow not initialized.")
            return
        result = self.orchestrator.run_lint()
        print(f"Spec Lint: {result['result']} (score={result['score']})")

    def _cmd_guard(self, parts: list[str]) -> None:
        if not self.orchestrator:
            print("Flow not initialized.")
            return
        files = parts[1].split(",") if len(parts) > 1 else []
        result = self.orchestrator.check_guard(files)
        print(f"Architecture Guard: {result['result']}")

    def _cmd_drift(self) -> None:
        if not self.orchestrator:
            print("Flow not initialized.")
            return
        result = self.orchestrator.detect_drift()
        print(f"Drift Detection: {result['result']}")

    def _cmd_progress(self) -> None:
        path = self.workspace / "progress.json"
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            print(json.dumps(data, indent=2))
        else:
            print("Progress not found. Initialize flow first.")

    def _cmd_events(self, parts: list[str]) -> None:
        log_path = self.workspace / "event-log.jsonl"
        if not log_path.exists():
            print("No events yet.")
            return
        event_type = None
        if len(parts) > 2 and parts[1] == "--type":
            event_type = parts[2]
        from cvg_harness.ledger.event_log import load_events
        events = load_events(log_path, event_type=event_type)
        for e in events:
            print(f"{e.timestamp} {e.event_type} ({e.actor})")

    def _cmd_state(self) -> None:
        if self.orchestrator:
            s = self.orchestrator.state
            print(f"Project: {s.project}")
            print(f"Feature: {s.feature}")
            print(f"Mode: {s.mode}")
            print(f"Phase: {s.current_phase}")
            print(f"Gate: {s.current_gate}")
            print(f"Status: {s.status}")
            print(f"Sprint: {s.sprint_id}")
            print(f"Blockers: {s.blockers}")
            print(f"Last event: {s.last_event}")
        else:
            print("Flow not initialized.")

    def _cmd_set_phase(self, parts: list[str]) -> None:
        if not self.orchestrator:
            print("Flow not initialized.")
            return
        if len(parts) < 2:
            print("Usage: set-phase <phase>")
            return
        self.orchestrator.advance_phase(parts[1])
        print(f"Phase set to: {parts[1]}")

    def _cmd_block(self, parts: list[str]) -> None:
        if not self.orchestrator:
            print("Flow not initialized.")
            return
        reason = parts[1] if len(parts) > 1 else "unknown"
        self.orchestrator.block(reason)
        print(f"Flow blocked: {reason}")

    def _cmd_unblock(self, parts: list[str]) -> None:
        if not self.orchestrator:
            print("Flow not initialized.")
            return
        if len(parts) > 1 and parts[1] in self.orchestrator.state.blockers:
            self.orchestrator.state.blockers.remove(parts[1])
            self.orchestrator.state.status = "running"
            self.orchestrator._save_state()
            print(f"Unblocked: {parts[1]}")

    def _cmd_metrics(self) -> None:
        path = self.workspace / "delivery-metrics.json"
        if path.exists():
            with open(path) as f:
                print(json.dumps(json.load(f), indent=2))
            return

        event_log_path = self.workspace / "event-log.jsonl"
        if event_log_path.exists():
            from cvg_harness.metrics_agg.metrics_aggregator import MetricsAggregator

            progress_path = self.workspace / "progress.json"
            project = self.workspace.name
            feature = self.workspace.name
            mode = "FAST"
            if progress_path.exists():
                progress = load_progress(progress_path)
                project = progress.project
                feature = progress.feature
                mode = progress.mode
            agg = MetricsAggregator()
            metrics = agg.export_delivery_metrics(
                project=project,
                feature=feature,
                mode=mode,
                event_log_path=event_log_path,
                progress_path=progress_path if progress_path.exists() else None,
                output_path=path,
            )
            print(json.dumps(metrics.to_dict(), indent=2))
        else:
            print("Metrics not available yet.")

    def _cmd_template(self, parts: list[str]) -> None:
        if len(parts) < 2:
            print("Usage: template <prd|spec|sprint>")
            return
        from cvg_harness.templates.revised_templates import render_prd, render_spec, render_sprint_plan
        data = {}
        if parts[1] == "prd":
            print(render_prd(data))
        elif parts[1] == "spec":
            print(render_spec(data))
        elif parts[1] == "sprint":
            print(render_sprint_plan(data))


def main():
    workspace = Path.cwd() if len(sys.argv) < 2 else Path(sys.argv[1])
    repl = REPL(workspace=workspace)
    repl.run()


if __name__ == "__main__":
    main()

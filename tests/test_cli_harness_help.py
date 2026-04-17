"""Testes de CLI do comando principal `harness`."""

import subprocess
import sys


def test_harness_help_exposes_prompt_first_flags() -> None:
    output = subprocess.check_output(
        [sys.executable, "-m", "cvg_harness.cli.harness", "--help"],
        text=True,
    )
    assert "--provider" in output
    assert "--model" in output
    assert "--api-key" in output
    assert "--non-interactive" in output
    assert "modo técnico" in output.lower() or "debug" in output.lower()

"""
Testes para Architecture Guardian.
"""

import pytest
from cvg_harness.guardian.architecture_guardian import ArchitectureGuardian


def test_guard_pass_empty_changes():
    guardian = ArchitectureGuardian(
        authorized_areas=["src/a", "src/b"],
        prohibited_areas=["src/legacy"],
    )
    report = guardian.check(changed_files=["src/a/module.py"])
    assert report.result == "PASS"


def test_guard_prohibited_area_blocked():
    guardian = ArchitectureGuardian(
        authorized_areas=["src/a"],
        prohibited_areas=["src/legacy", "src/v1"],
    )
    report = guardian.check(changed_files=["src/legacy/old.py"])
    assert report.result == "FAIL"
    assert any(v["rule"] == "prohibited_area_touched" for v in report.violations)


def test_guard_outside_authorized_area():
    guardian = ArchitectureGuardian(
        authorized_areas=["src/auth", "src/api"],
        prohibited_areas=["src/legacy"],
    )
    report = guardian.check(changed_files=["src/unknown/file.py"])
    assert report.result == "FAIL"


def test_guard_with_dependencies():
    guardian = ArchitectureGuardian(
        authorized_areas=["src/a"],
        prohibited_areas=[],
    )
    report = guardian.check(changed_files=["src/a/module.py"], new_dependencies=[])
    assert report.result == "PASS"

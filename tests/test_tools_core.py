"""Testes para as ferramentas centrais do front-agent."""

from pathlib import Path
import json

import pytest

from cvg_harness.tools import (
    ContextMemoryTool,
    FileSystemTool,
    PlanningTool,
    ShellTool,
    SubagentTool,
)


def test_filesystem_tool_implements_read_write_edit_list_and_glob(tmp_path: Path) -> None:
    tool = FileSystemTool(tmp_path)
    target = tmp_path / "foo.txt"
    result = tool.write_file(target, "linha 1\nlinha 2")
    assert result.path.endswith("foo.txt")
    assert result.operation == "write"
    assert "linha 1" in result.diff

    read = tool.read_file("foo.txt")
    assert read == "linha 1\nlinha 2"

    edited = tool.edit_file("foo.txt", "linha 1\nlinha 2 alterada")
    assert edited.operation == "edit"
    assert "alterada" in edited.diff or edited.diff == ""

    items = tool.list_dir(".")
    assert "foo.txt" in items
    assert any(item.endswith("foo.txt") for item in tool.glob("**/foo.txt"))


def test_filesystem_tool_blocks_out_of_workspace(tmp_path: Path) -> None:
    outside = Path("/tmp")
    tool = FileSystemTool(tmp_path)
    try:
        tool.read_file(outside / "any.txt")
    except ValueError as exc:
        assert "bloqueado" in str(exc).lower()
    else:
        raise AssertionError("deveria bloquear acesso fora do workspace")


def test_shell_tool_runs_command_and_returns_output(tmp_path: Path) -> None:
    tool = ShellTool(tmp_path)
    result = tool.run("echo ferramenta-shell", timeout=2)
    assert result.return_code == 0
    assert "ferramenta-shell" in result.stdout


def test_shell_tool_respects_allow_and_deny_lists(tmp_path: Path) -> None:
    tool = ShellTool(tmp_path, allowed_commands=["echo"], denied_commands=["rm"])
    result = tool.run("echo permitido", timeout=2)
    assert result.return_code == 0
    with pytest.raises(PermissionError):
        tool.run("rm -rf arquivo_inexistente", timeout=2)


def test_shell_tool_parses_quoted_command(tmp_path: Path) -> None:
    tool = ShellTool(tmp_path, allowed_commands=["python3"])
    result = tool.run('python3 -c "print(\'ok\')"', timeout=2)
    assert result.return_code == 0
    assert "ok" in result.stdout


def test_planning_tool_persists_and_updates_steps(tmp_path: Path) -> None:
    tool = PlanningTool(tmp_path)
    tool.create_plan("run-001", ["research", "prd", "spec"])
    payload = tool.serialize_plan("run-001")
    assert payload["count"] == 3
    assert payload["current_step"]["step_id"] == "step-1"

    tool.update_plan("run-001", "step-2", "running", notes="iniciado")
    payload = tool.serialize_plan("run-001")
    assert payload["current_step"]["step_id"] == "step-1"

    tool.mark_done("run-001", "step-1")
    payload = tool.serialize_plan("run-001")
    assert payload["current_step"]["step_id"] == "step-2"


def test_subagent_tool_spawns_and_merges_result(tmp_path: Path) -> None:
    tool = SubagentTool(tmp_path)
    task_id = tool.spawn("research", "testar integração", {"workspace": tmp_path, "project": "demo"}, max_tokens=128)
    merged = tool.merge_result(task_id)
    assert merged["task_id"] == task_id
    assert merged["status"] in {"done", "failed"}

    missing = tool.await_result(task_id)
    assert isinstance(missing, dict)


def test_subagent_tool_runs_implementation_with_sprint_plan(tmp_path: Path) -> None:
    run_ws = tmp_path / ".harness" / "runs" / "run-001"
    artifacts = run_ws / "artifacts"
    artifacts.mkdir(parents=True)

    sprint_plan = {
        "sprints": [
            {
                "sprint_id": "SPRINT-1",
                "objetivo": "Implementar autenticação",
                "acoes": ["Criar endpoint", "Adicionar testes"],
            }
        ]
    }
    (artifacts / "sprint-plan.json").write_text(json.dumps(sprint_plan, ensure_ascii=False), encoding="utf-8")

    tool = SubagentTool(tmp_path)
    task_id = tool.spawn(
        "implement",
        "implementação de autenticação",
        {
            "workspace": str(tmp_path),
            "run_workspace": str(run_ws),
            "project": "cvg-harness",
            "mode": "ENTERPRISE",
        },
        max_tokens=128,
    )
    merged = tool.merge_result(task_id)

    assert merged["status"] == "done"
    assert merged["result"]["status"] == "done"
    plan_path = Path(merged["result"]["report"])
    assert plan_path.exists()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["mode"] == "ENTERPRISE"
    assert plan["steps"][0]["sprint_id"] == "SPRINT-1"
    assert plan["steps"][0]["ações"][0] == "Criar endpoint"


def test_subagent_tool_runs_implementation_without_sprint_plan(tmp_path: Path) -> None:
    run_ws = tmp_path / ".harness" / "runs" / "run-001"
    (run_ws / "artifacts").mkdir(parents=True)

    tool = SubagentTool(tmp_path)
    task_id = tool.spawn(
        "implement",
        "criar módulo permissões por setor",
        {
            "workspace": str(tmp_path),
            "run_workspace": str(run_ws),
            "project": "cvg-harness",
            "mode": "FAST",
        },
        max_tokens=128,
    )
    merged = tool.merge_result(task_id)

    assert merged["status"] == "done"
    plan_path = Path(merged["result"]["report"])
    assert plan_path.exists()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["steps"][0]["status"] == "requires_handoff"
    assert "Aguardando aprovação" in plan["steps"][0]["ações"][0]


def test_context_memory_tool_store_and_load_scopes(tmp_path: Path) -> None:
    tool = ContextMemoryTool(tmp_path, run_id="run-001")
    tool.save("feature", {"nome": "permissoes"}, scope="project")
    tool.save("decision", {"mode": "ENTERPRISE"}, scope="run")
    tool.save("theme", "agente", scope="global")

    assert tool.load("feature")["nome"] == "permissoes"
    tool.set_run("run-001")
    assert tool.load("decision")["mode"] == "ENTERPRISE"
    assert tool.load("theme") == "agente"

    context = tool.load_project_context()
    assert context["feature"]["nome"] == "permissoes"

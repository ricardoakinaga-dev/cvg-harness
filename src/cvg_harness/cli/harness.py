"""Entry point para o modo `harness` (prompt-first)."""

from __future__ import annotations

import argparse
import sys

from cvg_harness.app.agent import FrontAgent, FrontAgentError
from cvg_harness.cli import cli as legacy_cli
from cvg_harness.workspace import WorkspaceManager


def _run_debug(args: list[str]) -> int:
    legacy_cli.main(args)
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="harness", description="Harness terminal agent")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("resume", help="retomar sessão ativa")
    sub.add_parser("status", help="mostrar status atual")
    sub.add_parser("config", help="reconfigurar provider/apikey")
    sub.add_parser("doctor", help="health check do agente")
    sub_debug = sub.add_parser("debug", help="modo técnico; proxy de comandos antigos")
    sub_debug.add_argument("legacy", nargs="*", help="Comando do modo técnico, ex.: status")
    parser.add_argument("--workspace", default=".", help="Diretório do projeto")
    args = parser.parse_args(argv)

    workspace = WorkspaceManager(args.workspace)
    agent = FrontAgent(workspace=workspace.path)

    if args.command == "debug":
        _run_debug(args.legacy)
        return
    if args.command in {"status", "resume", "doctor", "config"}:
        if args.command == "config":
            print("Modo configuração explícita. Abrindo fluxo de setup no modo interativo.")
            agent.non_interactive = False
            agent._run_onboarding()
            return
        if args.command == "doctor":
            agent.boot()
            print(agent._doctor())
            return
        if args.command in {"status", "resume"}:
            agent.boot()
            print(agent._status())
            return

    # sem comando: loop conversacional
    try:
        agent.start()
    except FrontAgentError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

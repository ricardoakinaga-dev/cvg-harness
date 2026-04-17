"""Entry point para o modo `harness` (prompt-first)."""

from __future__ import annotations

import argparse
import sys

from cvg_harness.app.agent import FrontAgent, FrontAgentError
from cvg_harness.cli import cli as legacy_cli
from cvg_harness.workspace import WorkspaceManager


_HELP_EPILOG = """
Fluxo principal:
  harness
      Inicia o agente conversacional no diretório atual.
      O usuário digita instruções em linguagem natural.

Comandos avançados:
  harness status      # consulta status da run ativa
  harness resume      # retoma a demanda ativa
  harness history     # mostra histórico da sessão atual
  harness config      # reexecuta onboarding
  harness doctor      # health check básico
  harness debug ...   # executa comandos técnicos antigos

Exemplos:
  harness
  harness debug status
  harness --provider openai --model gpt-4o-mini status
"""


def _run_debug(args: list[str]) -> int:
    legacy_cli.main(args)
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="harness",
        description="harness — agente terminal conversacional para operações com CVG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_HELP_EPILOG,
    )
    parser.add_argument("--provider", default=None, help="provider explícito para a sessão")
    parser.add_argument("--model", default=None, help="modelo explícito para a sessão")
    parser.add_argument("--api-key", default=None, help="api key explícita para esta sessão")
    parser.add_argument("--state-dir", default=".harness", help="diretório de estado do workspace")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="falhar se configuração estiver incompleta em vez de abrir onboarding",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("resume", help="retomar sessão ativa")
    sub.add_parser("status", help="mostrar status atual")
    sub.add_parser("history", help="mostrar histórico da sessão atual")
    sub.add_parser("config", help="reconfigurar provider/apikey")
    sub.add_parser("doctor", help="health check do agente")
    sub_debug = sub.add_parser("debug", help="modo técnico; proxy de comandos antigos")
    sub_debug.add_argument("legacy", nargs="*", help="Comando do modo técnico, ex.: status")
    parser.add_argument("--workspace", default=".", help="Diretório do projeto")
    args = parser.parse_args(argv)

    workspace = WorkspaceManager(args.workspace)
    agent = FrontAgent(
        workspace=workspace.path,
        state_dir=args.state_dir,
        non_interactive=args.non_interactive,
        explicit_provider=args.provider,
        explicit_model=args.model,
        explicit_api_key=args.api_key,
    )

    if args.command == "debug":
        _run_debug(args.legacy)
        return
    if args.command in {"status", "resume", "doctor", "config", "history"}:
        if args.command == "config":
            print("Modo configuração explícita.")
            agent._run_onboarding(agent.explicit_provider, agent.explicit_model)
            agent.boot()
            print("Configuração atualizada.")
            print(agent._provider_label())
            return
        if args.command == "doctor":
            agent.boot()
            print(agent._doctor())
            return
        if args.command == "status":
            agent.boot()
            print(agent._status())
            return
        if args.command == "resume":
            agent.boot(require_provider=False)
            print(agent._resume())
            return
        if args.command == "history":
            print(agent._history())
            return

    # sem comando: loop conversacional
    try:
        agent.start()
    except FrontAgentError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Entry point para o modo `harness` (prompt-first)."""

from __future__ import annotations

import argparse
import json
import sys

from cvg_harness.app.agent import FrontAgent, FrontAgentError
from cvg_harness.cli import cli as legacy_cli
from cvg_harness.workspace import WorkspaceManager


_HELP_EPILOG = """
Fluxo principal:
  harness
      Inicia o agente conversacional no diretório atual.
      O usuário digita instruções em linguagem natural.

Comandos de produto:
  harness status      # consulta status da run ativa
  harness resume      # retoma a demanda ativa
  harness inspect     # inspeciona artefatos e pendências da run ativa
  harness summary     # resumo da entrega ou situação atual
  harness history     # mostra histórico da sessão atual
  harness config      # reexecuta onboarding
  harness doctor      # health check básico

Comandos técnicos avançados:
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
    argv = list(sys.argv[1:] if argv is None else argv)
    json_flag_requested = "--json" in argv
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
    parser.add_argument(
        "--json",
        action="store_true",
        help="compatibilidade: emitir saída em JSON em alguns comandos não interativos",
    )
    json_parser = argparse.ArgumentParser(add_help=False)
    json_parser.add_argument(
        "--json",
        action="store_true",
        help="emitir saída em JSON para o comando atual",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("resume", help="retomar sessão ativa", parents=[json_parser])
    sub.add_parser("status", help="mostrar status atual", parents=[json_parser])
    sub.add_parser("history", help="mostrar histórico da sessão atual", parents=[json_parser])
    sub.add_parser("inspect", help="inspeção da demanda ativa", parents=[json_parser])
    sub.add_parser("summary", help="resumo da entrega", parents=[json_parser])
    sub.add_parser("config", help="reconfigurar provider/apikey")
    sub.add_parser("doctor", help="health check do agente")
    sub.add_parser("help", help="exibir ajuda do produto no terminal")
    sub_debug = sub.add_parser("debug", help="modo técnico; proxy de comandos antigos")
    sub_debug.add_argument("legacy", nargs="*", help="Comando do modo técnico, ex.: status")
    parser.add_argument("--workspace", default=".", help="Diretório do projeto")
    args = parser.parse_args(argv)
    if json_flag_requested:
        args.json = True

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
    if args.command in {"status", "resume", "doctor", "config", "history", "inspect", "summary", "help"}:
        def _emit(payload: object) -> None:
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print(payload)

        if args.command == "config":
            print("Modo configuração explícita.")
            agent._run_onboarding(agent.explicit_provider, agent.explicit_model)
            agent.boot()
            print("Configuração atualizada.")
            print(agent._provider_label())
            return
        if args.command == "doctor":
            agent.boot()
            _emit(agent._doctor())
            return
        if args.command == "status":
            agent.boot()
            payload = agent._status_payload()
            if args.json:
                _emit(payload)
            else:
                print(agent._status())
            return
        if args.command == "resume":
            agent.boot(require_provider=False)
            payload = agent._resume_payload()
            if args.json:
                _emit(payload)
            else:
                print(agent._resume())
            return
        if args.command == "history":
            payload = agent._history_payload()
            if args.json:
                _emit(payload)
            else:
                print(agent._history())
            return
        if args.command == "inspect":
            if args.json:
                _emit(agent._inspect_payload())
            else:
                print(agent._inspect())
            return
        if args.command == "summary":
            if args.json:
                _emit(agent._summary_payload())
            else:
                print(agent._summary())
            return
        if args.command == "help":
            parser.print_help()
            return

    # sem comando: loop conversacional
    try:
        agent.start()
    except FrontAgentError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

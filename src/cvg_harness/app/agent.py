"""Front-agent de conversa do Harness."""

from __future__ import annotations

from pathlib import Path
import os
import re
from typing import Any

from cvg_harness.classification.classifier import calculate_mode
from cvg_harness.config import (
    GlobalHarnessConfig,
    ProviderConfig,
    LoadedConfig,
    load_config,
    normalize_provider_defaults,
    save_project_config,
    save_global_config,
    validate_model_name,
)
from cvg_harness.operator.service import OperatorService, infer_dimensions_from_demand
from cvg_harness.providers import build_provider
from cvg_harness.providers.base import ProviderError
from cvg_harness.providers.base import Provider
from cvg_harness.routing import RouteType, RoutedRequest, route_request
from cvg_harness.session import SessionManager
from cvg_harness.workspace import WorkspaceManager


class FrontAgentError(RuntimeError):
    """Erro no front-agent."""


class FrontAgent:
    def __init__(
        self,
        workspace: Path | None = None,
        state_dir: str = ".harness",
        non_interactive: bool = False,
    ) -> None:
        self.workspace = Path(workspace or Path.cwd())
        self.state_dir = state_dir
        self.workspace_mgr = WorkspaceManager(self.workspace, state_dir=state_dir)
        self.session = SessionManager(self.workspace_mgr.path, state_dir=state_dir)
        self.non_interactive = non_interactive
        self.config: LoadedConfig | None = None
        self.provider: Provider | None = None
        self.service = OperatorService(self.workspace_mgr.path, state_dir_name=state_dir)
        self._booted = False

    def boot(self) -> None:
        self.config = load_config(self.workspace_mgr.path)
        self.provider = build_provider(self.config)
        if not self.config.explicit_key:
            if self.non_interactive:
                raise FrontAgentError(
                    "Configuração incompleta: defina ANTHROPIC_API_KEY/OPENAI_API_KEY/OPENROUTER_API_KEY."
                )
            self._run_onboarding()
            self.config = load_config(self.workspace_mgr.path)
            self.provider = build_provider(self.config)
        self._booted = True

    def _run_onboarding(self) -> None:
        print("Nenhuma configuração válida encontrada.")
        print("Vamos configurar o Harness.")
        print("Escolha o provider principal:")
        print("1. MiniMax (recomendado)")
        print("2. OpenAI")
        print("3. OpenRouter")
        provider_map = {"1": "minimax", "2": "openai", "3": "openrouter"}
        provider = "1"
        while provider not in provider_map:
            provider = (input("> ").strip() or "1")
            if provider not in provider_map:
                print("Escolha inválida. Use 1, 2 ou 3.")
        chosen = provider_map[provider]

        defaults = normalize_provider_defaults()
        default_model = validate_model_name(chosen, defaults[chosen]["default_model"])
        api_key_env = defaults[chosen]["api_key_env"]
        print(f"Informe a variável {api_key_env} com a API key atual (opcional).")
        api_key = input("Ou cole a API key agora: ").strip()

        if api_key:
            os.environ[api_key_env] = api_key
            print(f"API key recebida para esta sessão e aplicada em {api_key_env}.")
            print("Recomendação de segurança: prefira manter só no shell e não persistir texto de chave em arquivo.")

        if self._ask_yes_no("Salvar configuração global do usuário?", default=True):
            self._save_global_config(chosen, default_model)
        else:
            save_project_config(self.workspace_mgr.path, chosen, default_model)
        self.config = load_config(self.workspace_mgr.path)
        self.provider = build_provider(self.config)

        print("Configuração salva.")
        if self.provider.test_connection():
            print("Teste de conexão: OK")
        else:
            print("Teste de conexão: sem resposta do endpoint. A execução seguirá com validação de chave.")

    def _ask_yes_no(self, prompt: str, default: bool = True) -> bool:
        suffix = " [Y/n]" if default else " [y/N]"
        value = input(f"{prompt}{suffix} ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes", "s", "sim"}:
            return True
        if value in {"n", "no", "nao", "não"}:
            return False
        return default

    def _save_global_config(self, provider: str, model: str) -> None:
        defaults = normalize_provider_defaults()
        providers: dict[str, ProviderConfig] = {}
        for name, payload in defaults.items():
            providers[name] = ProviderConfig(
                name=name,
                base_url=payload["base_url"],
                api_key_env=payload["api_key_env"],
                models=list(payload["models"]),
                default_model=payload["default_model"],
            )
        config = GlobalHarnessConfig(
            default_provider=provider,
            default_model=validate_model_name(provider, model),
            providers=providers,
            workspace_dir=self.state_dir,
        )
        save_global_config(config)

    def _provider_label(self) -> str:
        if not self.config:
            return "minimax (pendente)"
        return f"{self.config.provider} | {self.config.model}"

    def start(self) -> None:
        if not self._booted:
            self.boot()
        self._announce()
        while True:
            try:
                prompt = input("> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nSessão encerrada.")
                break
            if not prompt:
                continue
            state = self.session.current()
            request = route_request(prompt, has_active_run=bool(state.run_id))
            self.session.append_turn("user", prompt, request.route.value, "cli")
            output = self._dispatch(request)
            if output:
                print(output)
            if request.route == RouteType.EXIT:
                break

    def _announce(self) -> None:
        print("Harness iniciado.")
        print(f"Workspace detectado: {self.workspace_mgr.path}")
        print(f"Provider: {self._provider_label()}")
        print("Digite sua instrução.")

    def _dispatch(self, request: RoutedRequest) -> str:
        if request.route == RouteType.HELP:
            return self._help()
        if request.route == RouteType.EXIT:
            return "Até mais."
        if request.route == RouteType.STATUS:
            return self._status()
        if request.route == RouteType.INSPECT:
            return self._inspect()
        if request.route == RouteType.RESUME:
            return self._resume()
        if request.route == RouteType.CONTINUE:
            return self._continue(request.raw)
        if request.route == RouteType.REPLAN:
            return self._replan(request.raw)
        if request.route == RouteType.REASON:
            return self._reason()
        if request.route == RouteType.CONFIG:
            self._run_onboarding()
            return "Configuração atualizada."
        if request.route == RouteType.DOCTOR:
            return self._doctor()
        if request.route == RouteType.DEBUG:
            return self._debug(request.params.get("command", ""))
        return self._new_demand(request.raw)

    def _help(self) -> str:
        return (
            "Uso principal:\n"
            "  - digite uma demanda em linguagem natural\n"
            "  - status\n"
            "  - continue\n"
            "  - inspect / resume\n"
            "  - replaneje <motivo>\n"
            "  - por que você escolheu enterprise?\n"
            "\n"
            "Debug avançado:\n"
            "  - debug <comando técnico antigo>"
        )

    def _active_run(self) -> bool:
        state = self.session.current()
        if not state.run_id:
            return False
        try:
            self.service.load_current_run()
            return True
        except Exception:
            return False

    def _status(self) -> str:
        if not self._active_run():
            return "Sem demanda ativa. Inicie uma demanda em linguagem natural."
        payload = self.service.status()
        return (
            f"Run: {payload['run_id']}\\n"
            f"Projeto: {payload['project']}\\n"
            f"Demanda: {payload['demand']}\\n"
            f"Fase/Gate: {payload['current_phase']} / {payload['current_gate']}\\n"
            f"Status: {payload['operator_status']}\\n"
            f"Pendência humana: {payload['pending_human_action'] or '-'}\\n"
            f"Próximo passo: {payload['next_action']}"
        )

    def _inspect(self) -> str:
        if not self._active_run():
            return "Sem demanda ativa para inspeção."
        payload = self.service.inspect()
        run = payload["run"]
        artifacts = ", ".join(payload.get("artifacts", []))
        reports = ", ".join(payload.get("reports", []))
        return (
            f"Run: {run['run_id']} ({run['operator_status']})\\n"
            f"Demanda: {run['demand']}\\n"
            f"Artefatos: {artifacts}\\n"
            f"Relatórios: {reports}\\n"
            f"Pendência: {run['pending_human_action'] or '-'}\\n"
            f"Próximo passo: {run['next_action']}"
        )

    def _resume(self) -> str:
        if not self._active_run():
            return "Sem run ativa para retomar."
        payload = self.service.status()
        return (
            f"Retoma da run {payload['run_id']}\\n"
            f"Fase/Gate: {payload['current_phase']} / {payload['current_gate']}\\n"
            f"Pendência: {payload['pending_human_action'] or '-'}\\n"
            f"Próximo passo: {payload['next_action']}"
        )

    def _continue(self, text: str) -> str:
        if not self._active_run():
            return "Sem demanda ativa para continuar."
        run = self.service.status()
        if run.get("pending_human_action") == "approve_sprint" and self._looks_like_approval(text):
            result = self.service.approve()
            return self._summarize_run(result, "Sprint aprovada. Envie evidências para continuar.")
        changed_files = self._extract_file_list(text)
        try:
            if changed_files:
                result = self.service.continue_run(changed_files=changed_files, evidence=[text] if text else None, evidence_json=None, evidence_file=None)
            else:
                result = self.service.continue_run(evidence=[text] if text else None)
            return self._summarize_run(result, "Continue executado.")
        except Exception as exc:
            return f"Falha no continue: {exc}"

    def _replan(self, reason: str) -> str:
        if not self._active_run():
            return "Sem demanda ativa para replanejar."
        result = self.service.replan(reason=reason)
        return f"Replanejamento registrado: {result['decision']['action']} ({result['decision']['reason']})"

    def _reason(self) -> str:
        if not self._active_run():
            return "Sem demanda ativa para explicação."
        payload = self.service.inspect()
        decision = None
        if payload.get("causal") and payload["causal"].get("classification"):
            decision = payload["causal"]["classification"]
        run = payload["run"]
        if isinstance(decision, dict):
            return (
                f"Modo decidido: {decision.get('mode', run.get('mode'))}\\n"
                f"score: {decision.get('total_score')}\\n"
                f"rationale: {decision.get('rationale')}"
            )
        return f"Mode atual da run: {run.get('mode', '-')}"

    def _doctor(self) -> str:
        checks = [
            f"workspace: ok ({self.workspace_mgr.path})",
            f"state dir: {'ok' if self.workspace_mgr.state_dir.exists() else 'missing'}",
            f"provider: {self.config.provider if self.config else '-'}",
            f"api key: {'ok' if self.config and self.config.explicit_key else 'faltando'}",
        ]
        if self.provider and self.provider.api_key:
            checks.append(f"provider connection: {'OK' if self.provider.test_connection() else 'pending'}")
        return "doctor\\n- " + "\\n- ".join(checks)

    def _debug(self, command: str) -> str:
        if not command:
            return "debug: use 'debug <comando técnico>'. Ex.: debug status"
        from cvg_harness.cli.cli import main as legacy_main
        print(f"Executando comando técnico: cvg {command}")
        legacy_args = command.split()
        legacy_main(legacy_args)
        return ""

    def _new_demand(self, text: str) -> str:
        if not self.config:
            raise FrontAgentError("Configuração não inicializada.")
        dimensions, rationale = infer_dimensions_from_demand(text)
        mode = calculate_mode(dimensions)
        payload = self.service.start_run(demand=text, mode=mode)
        self.session.set_active_run(payload["run_id"])
        self.session.set_context(self.config.provider, self.config.model)
        return (
            f"Demanda recebida e roteada ({mode}).\\n"
            f"Run: {payload['run_id']}\\n"
            f"Próximo passo: {payload['next_action']}\\n"
            f"Racional inicial: {rationale}"
        ) + (
            "\\nAguardando sua aprovação da sprint: responda 'aprovar'."
            if payload.get("pending_human_action") == "approve_sprint"
            else ""
        )

    def _summarize_run(self, payload: dict[str, Any], prefix: str) -> str:
        run = payload["run"]
        return (
            f"{prefix}\\n"
            f"Run: {run['run_id']}\\n"
            f"Status: {run['operator_status']}\\n"
            f"Fase/Gate: {run['current_phase']} / {run['current_gate']}\\n"
            f"Pendência humana: {run['pending_human_action'] or '-'}\\n"
            f"Próximo passo: {run['next_action']}"
        )

    def _looks_like_approval(self, text: str) -> bool:
        lowered = text.lower()
        return any(word in lowered for word in ["aprovar", "aprovo", "approve", "sim", "ok", "confirmo"])

    def _extract_file_list(self, text: str) -> list[str]:
        files = re.findall(r"[\\w./-]+\\.[A-Za-z0-9]+", text)
        return [item for item in files if "/" in item]

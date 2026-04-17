"""Front-agent de conversa do Harness."""

from __future__ import annotations

import json
from pathlib import Path
import os
import re
from typing import Any

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
from cvg_harness.providers.base import Provider
from cvg_harness.routing import (
    EngineRoute,
    RouteType,
    RoutedRequest,
    decide_route,
    route_request,
)
from cvg_harness.app.activity_renderer import ActivityRenderer
from cvg_harness.tools import (
    ContextMemoryTool,
    FileSystemTool,
    PlanningTool,
    ShellTool,
    SubagentTool,
)
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
        explicit_provider: str | None = None,
        explicit_model: str | None = None,
        explicit_api_key: str | None = None,
    ) -> None:
        self.workspace = Path(workspace or Path.cwd())
        self.state_dir = state_dir
        self.workspace_mgr = WorkspaceManager(self.workspace, state_dir=state_dir)
        self.session = SessionManager(self.workspace_mgr.path, state_dir=state_dir)
        self.non_interactive = non_interactive
        self.explicit_provider = explicit_provider
        self.explicit_model = explicit_model
        self.explicit_api_key = explicit_api_key
        self.config: LoadedConfig | None = None
        self.provider: Provider | None = None
        self.service = OperatorService(self.workspace_mgr.path, state_dir_name=state_dir)
        self.last_model: str | None = None
        self._booted = False
        self._active_route: EngineRoute | None = None
        self._activity = ActivityRenderer()

    def _run_with_activity(self, label: str, action, success_message: str, error_message: str | None = None):
        self._activity.start(label)
        try:
            result = action()
            self._activity.success(success_message)
            return result
        except Exception as exc:  # pragma: no cover
            message = error_message or f"{label} falhou"
            self._activity.error(f"{message}: {exc}")
            return f"{message}: {exc}"

    def boot(self, require_provider: bool = False) -> None:
        self.config = load_config(
            self.workspace_mgr.path,
            explicit_provider=self.explicit_provider,
            explicit_model=self.explicit_model,
            explicit_api_key=self.explicit_api_key,
        )
        self.provider = build_provider(self.config)
        if require_provider and not self.config.explicit_key:
            if self.non_interactive:
                raise FrontAgentError(
                    "Configuração incompleta: defina ANTHROPIC_API_KEY/OPENAI_API_KEY/OPENROUTER_API_KEY."
                )
            self._run_onboarding(preferred_provider=self.explicit_provider, preferred_model=self.explicit_model)
            self.config = load_config(
                self.workspace_mgr.path,
                explicit_provider=self.explicit_provider,
                explicit_model=self.explicit_model,
                explicit_api_key=self.explicit_api_key,
            )
            self.provider = build_provider(self.config)
        self._booted = True

    def _run_onboarding(self, preferred_provider: str | None = None, preferred_model: str | None = None) -> None:
        print("Nenhuma configuração válida encontrada.")
        print("Vamos configurar o Harness.")
        print("Escolha o provider principal:")
        print("1. MiniMax (recomendado)")
        print("2. OpenAI")
        print("3. OpenRouter")
        provider_map = {"1": "minimax", "2": "openai", "3": "openrouter"}
        default_provider_choice = "1"
        if preferred_provider:
            normalized = preferred_provider.strip().lower()
            if normalized in provider_map.values():
                default_provider_choice = {v: k for k, v in provider_map.items()}[normalized]
            elif normalized in {"1", "2", "3"}:
                default_provider_choice = normalized
        provider = default_provider_choice
        while provider not in provider_map:
            provider = (input("> ").strip() or "1")
            if provider not in provider_map:
                print("Escolha inválida. Use 1, 2 ou 3.")
        chosen = provider_map[provider]

        defaults = normalize_provider_defaults()
        default_model = validate_model_name(chosen, defaults[chosen]["default_model"])
        if preferred_model:
            resolved_preferred_model = validate_model_name(chosen, preferred_model)
            if resolved_preferred_model:
                default_model = resolved_preferred_model
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

        print("Configuração salva.")
        onboarded = load_config(
            self.workspace_mgr.path,
            explicit_provider=chosen,
            explicit_model=default_model,
        )
        onboarded_provider = build_provider(onboarded)
        if onboarded_provider.test_connection():
            print("Teste de conexão: OK")
        else:
            print("Teste de conexão: sem resposta do endpoint. A execução seguirá com validação de chave.")

    def _route_for_demand(self, intent: str) -> EngineRoute:
        if not self.config:
            raise FrontAgentError("Configuração não inicializada.")
        preferred_model = self.explicit_model or self.config.model
        return decide_route(intent, self.config.provider_cfg.models, preferred_model=validate_model_name(self.config.provider, preferred_model))

    def _build_toolset(self, run_id: str | None = None) -> dict[str, Any]:
        run_workspace = (
            Path(self.service._run_dir(run_id))
            if run_id
            else self.workspace_mgr.path / self.state_dir
        )
        event_log_path = run_workspace / "logs" / "tool-events.jsonl"
        return {
            "filesystem": FileSystemTool(self.workspace_mgr.path, event_log_path=event_log_path),
            "shell": ShellTool(self.workspace_mgr.path, event_log_path=event_log_path),
            "planning": PlanningTool(self.workspace_mgr.path),
            "subagent": SubagentTool(self.workspace_mgr.path),
            "context_memory": ContextMemoryTool(self.workspace_mgr.path, run_id=run_id),
        }

    def _route_decision_context(self, route: EngineRoute, run_id: str | None, demand: str, run_workspace: str | None) -> dict[str, Any]:
        return {
            "intent": route.intent,
            "mode": route.mode,
            "model": route.model,
            "run_id": run_id,
            "run_workspace": run_workspace or "",
            "project": self.workspace_mgr.path.name,
            "demand": demand,
            "provider": self.config.provider if self.config else "minimax",
            "tools": route.tools,
            "subagents": route.subagents,
        }

    def _execute_autorouter_pipeline(
        self,
        route: EngineRoute,
        demand: str,
        run_id: str,
        run_workspace: str,
    ) -> dict[str, Any]:
        self._activity.update("Planejando")
        tools = self._build_toolset(run_id=run_id)
        planning: PlanningTool = tools["planning"]
        memory: ContextMemoryTool = tools["context_memory"]
        subagent: SubagentTool = tools["subagent"]

        steps = planning.create_plan(run_id, steps=route.pipeline)
        for index, step in enumerate(steps, start=1):
            del index
            step_id = step.step_id if hasattr(step, "step_id") else step["step_id"]
            step_name = step.name if hasattr(step, "name") else step["name"]
            self._activity.update(self._step_status_label(step_name))
            planning.update_plan(run_id, step_id, "running", notes=f"pipeline:auto:{step_name}")
            if step_name == "classification":
                planning.update_plan(run_id, step_id, "done", notes="já aplicado por OperatorService.start_run")
                continue
            if step_name not in route.subagents:
                planning.update_plan(
                    run_id,
                    step_id,
                    "done",
                    notes="sem subagente dedicado; etapa tratada na engine principal",
                )
                continue

            context = self._route_decision_context(route, run_id, demand, run_workspace)
            task_input = {
                "intent": demand,
                "mode": route.mode,
                "rationale": route.rationale,
                "model": route.model,
            }
            try:
                task_id = subagent.spawn(step_name, task_input, context=context, max_tokens=1200)
                payload = subagent.merge_result(task_id)
                notes = payload.get("result", {}).get("status", "done")
                planning.update_plan(run_id, step_id, "done", notes=f"subagent:{step_name}:{notes}")
                memory.append_event(
                    {
                        "event": "subagent_step_done",
                        "step": step_name,
                        "task_id": task_id,
                        "status": payload.get("status"),
                        "result": payload.get("result", {}),
                    }
                )
            except Exception as exc:  # pragma: no cover - proteção operacional
                planning.update_plan(run_id, step["step_id"], "failed", notes=f"erro no subagente: {exc}")
                memory.append_event(
                    {
                        "event": "subagent_step_error",
                        "step": step["name"],
                        "error": str(exc),
                    }
                )

        return {
            "run_id": run_id,
            "plan": planning.serialize_plan(run_id),
            "pipeline": route.pipeline,
            "tools": route.tools,
            "requires_human_confirmation": route.require_human_confirmation,
        }

    def _step_status_label(self, step_name: str) -> str:
        normalized = (step_name or "").lower()
        if "research" in normalized:
            return "Pesquisando"
        if normalized.startswith("prd"):
            return "Escrevendo"
        if "spec" in normalized or "linter" in normalized:
            return "Escrevendo"
        if normalized in {"sprint_planner"}:
            return "Planejando"
        if normalized in {"architecture_guardian", "evaluator", "drift_detector", "release_readiness"}:
            return "Validando"
        if normalized in {"replan_coordinator"}:
            return "Replanejando"
        if normalized in {"metrics_aggregator"}:
            return "Finalizando"
        return "Executando"

    def _provider_label(self) -> str:
        if not self.config:
            return "minimax (pendente)"
        current_model = self.config.model
        return f"{self.config.provider} | {current_model}"

    def _run_context_summary(self) -> str:
        session = self.session.current()
        active_model = session.model or (self.config.model if self.config else "-")
        active_provider = session.provider or (self.config.provider if self.config else "minimax")
        return f"{active_provider} ({active_model})"

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
                base_url_env=payload.get("base_url_env", ""),
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

    def start(self) -> None:
        if not self._booted:
            self.boot(require_provider=True)
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
            if request.route == RouteType.EXIT:
                self._activity.start("Finalizando")
                self._activity.success("Sessão encerrada")
                print("Até mais.")
                break
            output = self._dispatch(request)
            if output:
                print(output)

    def _announce(self) -> None:
        print("Harness iniciado.")
        print(f"Workspace detectado: {self.workspace_mgr.path}")
        print(f"Provider: {self._provider_label()}")
        run_id = self.session.current().run_id
        if run_id:
            print(f"Run ativa: {run_id}")
        print("Digite sua instrução.")

    def _dispatch(self, request: RoutedRequest) -> str:
        if request.route == RouteType.HELP:
            return self._run_with_activity("Analisando", self._help, "Ajuda exibida.")
        if request.route == RouteType.STATUS:
            return self._run_with_activity("Analisando", self._status, "Status exibido.")
        if request.route == RouteType.INSPECT:
            return self._run_with_activity("Analisando", self._inspect, "Inspeção exibida.")
        if request.route == RouteType.RESUME:
            return self._run_with_activity("Analisando", self._resume, "Demanda retomada.")
        if request.route == RouteType.SUMMARY:
            return self._run_with_activity("Analisando", self._summary, "Resumo exibido.")
        if request.route == RouteType.HISTORY:
            return self._run_with_activity("Analisando", self._history, "Histórico exibido.")
        if request.route == RouteType.CONTINUE:
            return self._run_with_activity(
                "Executando",
                lambda: self._continue(request.raw),
                "Continue executado.",
                error_message="Falha no continue",
            )
        if request.route == RouteType.REPLAN:
            return self._run_with_activity(
                "Replanejando",
                lambda: self._replan(request.raw),
                "Replanejamento enviado.",
                error_message="Falha no replanejamento",
            )
        if request.route == RouteType.REASON:
            return self._run_with_activity("Analisando", self._reason, "Explicação exibida.")
        if request.route == RouteType.CONFIG:
            return self._run_with_activity(
                "Planejando",
                self._reconfigure,
                "Configuração atualizada.",
            )
        if request.route == RouteType.DOCTOR:
            return self._run_with_activity("Analisando", self._doctor, "Diagnóstico exibido.")
        if request.route == RouteType.DEBUG:
            return self._run_with_activity(
                "Executando",
                lambda: self._debug(request.params.get("command", "")),
                "Comando técnico concluído.",
                error_message="Falha no comando técnico",
            )
        return self._new_demand_with_activity(request.raw)

    def _reconfigure(self) -> str:
        self._run_onboarding(self.explicit_provider, self.explicit_model)
        self.config = load_config(
            self.workspace_mgr.path,
            explicit_provider=self.explicit_provider,
            explicit_model=self.explicit_model,
            explicit_api_key=self.explicit_api_key,
        )
        self.provider = build_provider(self.config)
        return "Configuração atualizada."

    def _help(self) -> str:
        return (
            "Uso principal:\n"
            "  - digite uma demanda em linguagem natural\n"
            "  - status\n"
            "  - continue\n"
            "  - inspect / resume\n"
            "  - resumo\n"
            "  - histórico\n"
            "  - replaneje <motivo>\n"
            "  - por que você escolheu enterprise?\n"
            "  - sair\n"
            "\n"
            "Debug avançado:\n"
            "  - debug <comando técnico antigo>"
        )

    def _active_run(self) -> bool:
        state = self.session.current()
        try:
            if state.run_id:
                self.service.load_current_run()
                self.session.set_active_run(state.run_id)
                return True
            current_run = self.service.get_current_run_id()
        except Exception:
            return False
        state.run_id = current_run
        self.session.set_active_run(current_run)
        return True

    def _summary(self) -> str:
        if not self._active_run():
            return "Sem demanda ativa para resumir."
        payload = self.service.inspect()
        run = payload["run"]
        if run.get("operator_status") != "completed":
            return (
                f"Demanda não concluída ainda ({run['operator_status']}).\\n"
                f"Próximo passo: {run['next_action']}\\n"
                f"Pendência: {run['pending_human_action'] or '-'}"
            )
        return self._summarize_run({"run": run}, "Resumo final da demanda")

    def _status(self) -> str:
        if not self._active_run():
            return "Sem demanda ativa. Inicie uma demanda em linguagem natural."
        payload = self.service.status()
        active = self.session.current()
        provider_label = self._run_context_summary()
        return (
            f"Run: {payload['run_id']}\\n"
            f"Projeto: {payload['project']}\\n"
            f"Demanda: {payload['demand']}\\n"
            f"Provider: {provider_label}\\n"
            f"Fase/Gate: {payload['current_phase']} / {payload['current_gate']}\\n"
            f"Status: {payload['operator_status']}\\n"
            f"Pendência humana: {payload['pending_human_action'] or '-'}\\n"
            f"Próximo passo: {payload['next_action']}"
        )

    def _status_payload(self) -> dict[str, Any]:
        if not self._active_run():
            return {"status": "no_active_run", "message": "Sem demanda ativa. Inicie uma demanda em linguagem natural."}
        payload = self.service.status()
        payload = dict(payload)
        payload["status"] = "ok"
        payload["provider"] = self._run_context_summary()
        payload["request_provider"] = self.config.provider if self.config else "-"
        payload["request_model"] = self.config.model if self.config else "-"
        payload["workspace"] = str(self.workspace_mgr.path)
        if self.last_model:
            payload["model_used"] = self.last_model
        if self.session.current().model:
            payload["session_model"] = self.session.current().model
        return payload

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

    def _inspect_payload(self) -> dict[str, object]:
        if not self._active_run():
            return {
                "status": "no_active_run",
                "message": "Sem demanda ativa para inspeção.",
            }
        payload = self.service.inspect()
        run = payload["run"]
        return {
            "status": "ok",
            "workspace": str(self.workspace_mgr.path),
            "run_id": run.get("run_id", ""),
            "project": run.get("project", self.workspace_mgr.path.name),
            "demand": run.get("demand", ""),
            "operator_status": run.get("operator_status", ""),
            "mode": run.get("mode", ""),
            "pending_human_action": run.get("pending_human_action"),
            "next_action": run.get("next_action", ""),
            "artifacts": payload.get("artifacts", []),
            "reports": payload.get("reports", []),
            "causal": payload.get("causal", {}),
        }

    def _history(self) -> str:
        history = self.session.current().history or []
        if not history:
            return "Sem histórico de turnos na sessão atual."

        lines = ["Histórico da sessão atual (mais recentes):"]
        for idx, turn in enumerate(history[-10:], start=max(1, len(history) - 9)):
            lines.append(
                f"{idx}. [{turn['role']}] {turn['actor']} - {turn['intent']} | {turn['text']}"
            )
        return "\\n".join(lines)

    def _history_payload(self) -> dict[str, Any]:
        history = self.session.current().history or []
        return {
            "status": "ok",
            "count": len(history),
            "turns": history,
            "workspace": str(self.workspace_mgr.path),
            "run_id": self.session.current().run_id,
        }

    def _resume(self) -> str:
        if not self._active_run():
            return "Sem run ativa para retomar."
        payload = self.service.status()
        self.session.set_active_run(payload["run_id"])
        return (
            f"Retoma da run {payload['run_id']}\\n"
            f"Demanda: {payload['demand']}\\n"
            f"Fase/Gate: {payload['current_phase']} / {payload['current_gate']}\\n"
            f"Pendência: {payload['pending_human_action'] or '-'}\\n"
            f"Próximo passo: {payload['next_action']}"
        )

    def _resume_payload(self) -> dict[str, Any]:
        if not self._active_run():
            return {"status": "no_active_run", "message": "Sem run ativa para retomar."}
        payload = self._status_payload()
        if isinstance(payload, dict):
            payload["status"] = "ok"
            payload["action"] = "resume"
            return payload
        return {"status": "ok", "action": "resume"}

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
        run = payload["run"]
        run_workspace = Path(run["run_workspace"])
        classification = {}
        class_path = run_workspace / "artifacts" / "classification.json"
        if class_path.exists():
            try:
                classification = json.loads(class_path.read_text())
            except Exception:
                classification = {}

        mode = run.get("mode", "-")
        rationale = ""
        total_score = ""
        dimensions = {}
        override = {}

        if isinstance(classification, dict):
            mode = classification.get("mode", mode)
            rationale = str(classification.get("rationale", "") or "")
            total_score = str(classification.get("total_score", ""))
            dimensions = classification.get("dimensions", {}) or {}
            override = {
                "applied": bool(classification.get("override_applied")),
                "reason": classification.get("override_reason"),
            }

        summary = [
            f"Decisão de modo desta demanda: {mode}",
            f"Score: {total_score or '-'}",
            f"Modelo em uso: {self.last_model or (self.config.model if self.config else '-')}",
            f"Próxima ação: {run.get('next_action', '-')}",
            f"Pendência humana: {run.get('pending_human_action') or '-'}",
        ]

        if rationale:
            summary.append(f"Racional da decisão: {rationale}")
        if dimensions:
            ordered = sorted(
                dimensions.items(),
                key=lambda item: (-item[1], item[0]),
            )
            top_dimensions = ordered[:3]
            for key, value in top_dimensions:
                summary.append(f"- {key}: {value}")

        if override["applied"]:
            reason = override["reason"] or "ajuste explícito do operador"
            summary.append(f"Override aplicado: {reason}")

        return "\\n".join(summary)

    def _doctor(self) -> str:
        checks = [
            f"workspace: ok ({self.workspace_mgr.path})",
            f"state dir: {'ok' if self.workspace_mgr.state_dir.exists() else 'missing'}",
            f"provider: {self.config.provider if self.config else '-'}",
            f"api key: {'ok' if self.config and self.config.explicit_key else 'faltando'}",
        ]
        if self.config:
            base_url_env = self.config.provider_cfg.base_url_env
            checks.append(f"provider base_url: {self.config.provider_cfg.base_url}")
            checks.append(
                f"{base_url_env}: {'ok' if base_url_env and os.getenv(base_url_env) else 'padrao' if not base_url_env else 'missing'}"
            )
        if self.provider and self.provider.api_key:
            checks.append(f"provider connection: {'OK' if self.provider.test_connection() else 'pending'}")
        return "doctor\\n- " + "\\n- ".join(checks)

    def _debug(self, command: str) -> str:
        if not command:
            return "debug: use 'debug <comando técnico>'. Ex.: debug status"
        from cvg_harness.cli.cli import main as legacy_main
        self._activity.log(f"Executando comando técnico: cvg {command}")
        legacy_args = command.split()
        legacy_main(legacy_args)
        return ""

    def _new_demand(self, text: str) -> str:
        return self._new_demand_with_activity(text)

    def _new_demand_with_activity(self, text: str) -> str:
        if not self.config:
            raise FrontAgentError("Configuração não inicializada.")
        self._activity.start("Entendendo")
        try:
            route = self._route_for_demand(text)
            self._active_route = route
            self._activity.update("Analisando")
            dimensions, rationale = infer_dimensions_from_demand(text)
            mode = route.mode
            self.last_model = self._select_model(mode, preferred_model=route.model)
            model_hint = f"modelo escolhido: {self.last_model}"
            self._activity.update("Executando")
            payload = self.service.start_run(demand=text, mode=mode)
            self.session.set_active_run(payload["run_id"])
            self.session.set_context(self.config.provider, self.last_model)
            self._activity.update("Executando")
            route_payload = self._execute_autorouter_pipeline(
                route=route,
                demand=text,
                run_id=payload["run_id"],
                run_workspace=payload["run_workspace"],
            )
            self._activity.update("Finalizando")
            plan = route_payload["plan"]["count"]
            self._activity.success("Demanda roteada")
            return (
                f"Demanda recebida e roteada ({mode}).\\n"
                f"{model_hint}\\n"
                f"Run: {payload['run_id']}\\n"
                f"Plano automático: {plan} passos\\n"
                f"Próximo passo: {payload['next_action']}\\n"
                f"Racional inicial: {rationale}"
            ) + (
                "\\nAguardando sua aprovação da sprint: responda 'aprovar'."
                if payload.get("pending_human_action") == "approve_sprint"
                else ""
            )
        except Exception as exc:
            self._activity.error(f"Falha no início da demanda: {exc}")
            raise

    def _select_model(self, mode: str, preferred_model: str | None = None) -> str:
        if not self.config:
            raise FrontAgentError("Configuração não inicializada.")
        provider = self.config.provider
        cfg = self.config.provider_cfg
        if preferred_model and preferred_model in cfg.models:
            return preferred_model
        normalized_mode = (mode or "").upper()
        if cfg.models:
            if normalized_mode == "FAST":
                for model in cfg.models:
                    if "highspeed" in model.lower():
                        return model
            if normalized_mode == "ENTERPRISE":
                for model in cfg.models:
                    if "highspeed" not in model.lower():
                        return model
            if self.config.model in cfg.models:
                return self.config.model
            if normalized_mode and cfg.default_model in cfg.models:
                return cfg.default_model
            return cfg.models[0]
        return self.config.model

    def _summarize_run(self, payload: dict[str, Any], prefix: str) -> str:
        run = payload.get("run") if "run" in payload else payload
        model = self.last_model or (self.session.current().model or "-")
        lines = [
            f"{prefix}",
            f"Run: {run['run_id']}",
            f"Modelo: {model}",
            f"Status: {run['operator_status']}",
            f"Fase/Gate: {run['current_phase']} / {run['current_gate']}",
            f"Pendência humana: {run['pending_human_action'] or '-'}",
            f"Próximo passo: {run['next_action']}",
        ]
        if run.get("operator_status") != "completed":
            return "\\n".join(lines)
        try:
            inspect_payload = self.service.inspect()
            causal = inspect_payload.get("causal", {})
            artifacts = [str(item) for item in inspect_payload.get("artifacts", [])]
            reports = [str(item) for item in inspect_payload.get("reports", [])]
            sprints = inspect_payload.get("sprints", [])
            evidence = causal.get("evidence", {})
            changed_files = causal.get("changed_files", [])
            decisions = causal.get("decisions", {})
            lines.extend(
                [
                    "Resumo da entrega:",
                    f"- classification: {run.get('mode', '-')}",
                    f"- research: {'concluída' if 'research-notes.json' in artifacts else 'pendente'}",
                    f"- SPEC: {'gerada' if 'spec.json' in artifacts else 'pendente'}",
                    f"- spec lint: {'concluída' if ('spec-lint-report.json' in artifacts or 'spec-lint-report.json' in reports) else 'pendente'}",
                    f"- sprints executadas: {len(sprints)}",
                    f"- evaluator: {decisions.get('evaluation', '-')}",
                    f"- drift crítico: {decisions.get('drift', '-')}",
                    f"- release readiness: {decisions.get('release', '-')}",
                    f"- arquivos alterados: {', '.join(changed_files) or '-'}",
                    f"- evidências coletadas: {evidence.get('total_items', 0)}",
                    f"- evidência pendente: {', '.join(evidence.get('missing', [])) or '-'}",
                    f"- artefatos: {', '.join(artifacts or ['-'])}",
                    f"- relatórios: {', '.join(reports or ['-'])}",
                    f"- workspace: {run.get('run_workspace', '-')}",
                ]
            )
        except Exception:
            pass
        return "\\n".join(lines)

    def _looks_like_approval(self, text: str) -> bool:
        lowered = text.lower()
        return any(word in lowered for word in ["aprovar", "aprovo", "approve", "sim", "ok", "confirmo"])

    def _extract_file_list(self, text: str) -> list[str]:
        files = re.findall(r"[\\w./-]+\\.[A-Za-z0-9]+", text)
        return [item for item in files if "/" in item]

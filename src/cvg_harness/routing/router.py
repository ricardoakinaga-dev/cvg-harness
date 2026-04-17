"""Roteador de subagentes e intenções do agente."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class RouteType(str, Enum):
    NEW_DEMAND = "new_demand"
    STATUS = "status"
    INSPECT = "inspect"
    CONTINUE = "continue"
    RESUME = "resume"
    SUMMARY = "summary"
    REPLAN = "replan"
    REASON = "reason"
    DEBUG = "debug"
    CONFIG = "config"
    HELP = "help"
    DOCTOR = "doctor"
    EXIT = "exit"
    UNKNOWN = "unknown"


@dataclass
class RoutedRequest:
    route: RouteType
    intent: str
    raw: str
    params: dict[str, Any]
    agent: str = "front-agent"
    model: str = "auto"

    def payload(self) -> dict[str, Any]:
        return {
            "route": self.route.value,
            "intent": self.intent,
            "raw": self.raw,
            "params": self.params,
            "agent": self.agent,
            "model": self.model,
        }


def _contains(text: str, *phrases: str) -> bool:
    lowered = text.lower()
    return any(phrase.lower() in lowered for phrase in phrases)


def route_request(text: str, has_active_run: bool = False) -> RoutedRequest:
    txt = (text or "").strip()
    if not txt:
        return RoutedRequest(RouteType.UNKNOWN, "vazio", txt, {})

    if _contains(txt, "ajuda", "help"):
        return RoutedRequest(RouteType.HELP, "help", txt, {})
    if _contains(txt, "sair", "quit", "exit", "fechar", "encerrar"):
        return RoutedRequest(RouteType.EXIT, "exit", txt, {})
    if _contains(txt, "doctor", "health", "diagnóstico", "diagnostico"):
        return RoutedRequest(RouteType.DOCTOR, "doctor", txt, {})
    if _contains(txt, "config", "configuração", "chave", "provider", "setup"):
        return RoutedRequest(RouteType.CONFIG, "config", txt, {})
    if _contains(txt, "debug"):
        command = re.sub(r"^\\s*debug\\s*", "", txt, flags=re.IGNORECASE)
        return RoutedRequest(RouteType.DEBUG, "debug", txt, {"command": command.strip()})
    if _contains(txt, "resumo", "conclus", "entrega", "finalização", "encerrar", "encerramento"):
        return RoutedRequest(RouteType.SUMMARY, "summary", txt, {})

    if _contains(
        txt,
        "porque você escolheu",
        "porque escolheu",
        "por que você escolheu",
        "por que escolheu",
        "o porquê",
    ):
        return RoutedRequest(RouteType.REASON, "reason", txt, {})

    if _contains(
        txt,
        "retome de onde parou",
        "onde parou",
        "retomar",
        "retome",
        "retomei",
        "recomeçar corrida",
        "recomece",
        "retomar a corrida",
    ):
        return RoutedRequest(RouteType.RESUME, "resume", txt, {})

    if _contains(txt, "status", "estado", "progresso"):
        return RoutedRequest(RouteType.STATUS, "status", txt, {})

    if _contains(txt, "continue", "prosseguir", "aprovar", "aprovarei", "aprove", "aprovo", "confirmo"):
        return RoutedRequest(RouteType.CONTINUE, "continue", txt, {})
    if _contains(txt, "replaneje", "replano", "replan", "menos risco"):
        return RoutedRequest(RouteType.REPLAN, "replan", txt, {})
    if _contains(txt, "o que alter", "oque alter", "explique", "por que", "por que você", "porque você", "porquê", "por que motivo"):
        return RoutedRequest(RouteType.INSPECT, "inspect", txt, {})

    if has_active_run and _contains(txt, "arquivos", "evidência", "evidencia", "prova", "summary", "resumo"):
        return RoutedRequest(RouteType.INSPECT, "inspect", txt, {})

    return RoutedRequest(RouteType.NEW_DEMAND, "new_demand", txt, {})

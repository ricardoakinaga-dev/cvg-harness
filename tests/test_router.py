"""Testes do roteador de intenção do agente."""

from cvg_harness.routing import RouteType, route_request


def test_router_identifies_resume_intents() -> None:
    assert route_request("retome a demanda anterior").route == RouteType.RESUME
    assert route_request("retomar o ciclo agora").route == RouteType.RESUME
    assert route_request("quero retomar", has_active_run=True).route == RouteType.RESUME
    assert route_request("retome de onde parou", has_active_run=True).route == RouteType.RESUME
    assert route_request("onde parou", has_active_run=True).route == RouteType.RESUME


def test_router_identifies_reason_questions() -> None:
    assert route_request("por que você escolheu enterprise?").route == RouteType.REASON
    assert route_request("porque escolheu esse modo?").route == RouteType.REASON
    assert route_request("o porquê da decisão?").route == RouteType.REASON


def test_router_routes_encerrar_to_exit() -> None:
    assert route_request("encerrar").route == RouteType.EXIT
    assert route_request("quero encerrar").route == RouteType.EXIT


def test_router_identifies_history_intents() -> None:
    assert route_request("mostrar histórico").route == RouteType.HISTORY
    assert route_request("ver histórico da conversa").route == RouteType.HISTORY
    assert route_request("histórico dos turnos").route == RouteType.HISTORY


def test_router_routes_continuation_and_replan() -> None:
    assert route_request("aprovar a próxima sprint", has_active_run=True).route == RouteType.CONTINUE
    assert route_request("replaneje com menos risco", has_active_run=True).route == RouteType.REPLAN
    assert route_request("o que alterou?", has_active_run=True).route == RouteType.INSPECT


def test_router_routes_summary() -> None:
    assert route_request("resumo").route == RouteType.SUMMARY
    assert route_request("qual é o resumo desta demanda?").route == RouteType.SUMMARY

"""Renderer de atividade textual simples para o front-agent.

Mantido como um componente leve (sem animações) para evitar dependências extras no
loop interativo principal.
"""

from __future__ import annotations


class ActivityRenderer:
    """Objeto utilitário para feedback de etapas no terminal.

    A interface é intencionalmente mínima para não mascarar a saída principal do
    agente e evitar acoplamento com bibliotecas de UI.
    """

    def __init__(self) -> None:
        self.current: str | None = None

    def start(self, label: str) -> None:
        self.current = str(label)

    def update(self, label: str) -> None:
        self.current = str(label)

    def success(self, message: str) -> None:
        self.current = None
        if message:
            # O agente já imprime seus próprios resumos; mantenha discreto.
            pass

    def error(self, message: str) -> None:
        self.current = None
        if message:
            # Feedback rápido para logs de operação e telemetria.
            pass

    def log(self, message: str) -> None:
        if message:
            pass

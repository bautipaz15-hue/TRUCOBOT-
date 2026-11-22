"""
Máquina de estado y tracking del progreso de una mano de Truco.
Basado en la implementación más completa (nivel 4).
"""
from typing import List, Tuple, Optional
from .card import Card
from .rules import calcular_envido


class GameState:
    """Rastrea el estado actual de la mano y apuestas (Máquina de Estados)."""

    def __init__(self, cartas_iniciales: Tuple[Card, ...] = (),
                 puntos_bot: int = 0, puntos_rival: int = 0):
        self.cartas_iniciales: Tuple[Card, ...] = cartas_iniciales
        self.cartas_restantes: List[Card] = list(cartas_iniciales)
        self.puntos_bot: int = puntos_bot
        self.puntos_rival: int = puntos_rival

        # Estado de apuestas (0 = no cantado, 1 = envido/truco, 2 = real/retruco, 3 = falta/vale4)
        self.estado_envido: int = 0
        self.estado_truco: int = 0
        self.turno_apuesta_truco: str = "bot"
        self.fase_actual: str = "envido_disponible"
        self.bot_canto_envido_nivel: int = 0

        # Mesa y resultados de rondas
        self.cartas_en_mesa: List[Tuple[str, Card]] = []
        self.resultados_rondas: List[str] = []

        # Puntos de envido auto-calculados
        self.puntos_envido_mano: int = calcular_envido(list(cartas_iniciales)) if cartas_iniciales else 0

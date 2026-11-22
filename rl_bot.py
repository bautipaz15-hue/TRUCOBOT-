import logging
from typing import Optional, Tuple
from truco_core.card import Card
from truco_core.state import GameState
from truco_bots.base import BaseBot

class RLBot(BaseBot):
    """Bot que usa la red neuronal TrucoActorCritic entrenada con PPO."""
    # This is a thin wrapper - the actual RL logic lives in truco_rl/
    # This bot is for use in the Tkinter GUI context
    
    def __init__(self, model_path: Optional[str] = None, logger: Optional[logging.Logger] = None):
        if logger is None:
            self.logger = logging.getLogger("RLBot")
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger = logger
        self.estado_mano: Optional[GameState] = None
        self.model_path = model_path
        
        # Aquí se inicializaría el modelo si se requiere
        
    def set_estado(self, estado: GameState) -> None:
        self.estado_mano = estado
        self.logger.debug(f"Nueva mano RLBot. Cartas: {estado.cartas_iniciales}")

    def evaluar_iniciativa(self) -> Tuple[Optional[str], Optional[Card]]:
        # Implementación delegada al modelo de RL
        return None, None

    def responder_apuesta(self, tipo_apuesta: str, nivel_apuesta: int) -> str:
        # Implementación delegada al modelo de RL
        return "No Quiero"

    def jugar_carta(self, carta: Card) -> None:
        self.estado_mano.cartas_restantes.remove(carta)
        self.estado_mano.cartas_en_mesa.append(("bot", carta))
        self.estado_mano.fase_actual = "juego_cartas"

    def registrar_carta_rival(self, carta: Card) -> None:
        self.estado_mano.cartas_en_mesa.append(("rival", carta))
        self.estado_mano.fase_actual = "juego_cartas"

    def evaluar_ganador_ronda(self) -> Optional[str]:
        if len(self.estado_mano.cartas_en_mesa) == 2:
            jugador1, carta1 = self.estado_mano.cartas_en_mesa[0]
            jugador2, carta2 = self.estado_mano.cartas_en_mesa[1]
            
            p1 = carta1.jerarquia
            p2 = carta2.jerarquia
            
            if p1 > p2:
                ganador = jugador1
            elif p2 > p1:
                ganador = jugador2
            else:
                ganador = "parda"
                
            self.estado_mano.resultados_rondas.append(ganador)
            self.estado_mano.cartas_en_mesa = []
            return ganador
        return None

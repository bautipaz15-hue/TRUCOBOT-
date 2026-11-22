import logging
from typing import Optional, Tuple
from truco_core.card import Card
from truco_core.state import GameState
from truco_bots.base import BaseBot

class HeuristicBotV1(BaseBot):
    """
    Bot simple (Heurística V1).
    - Envido: acepta/canta si puntos >= 26
    - Truco: acepta/canta si alguna carta tiene poder >= 9
    - Jugar carta: mayor disponible, o menor si no puede superar al rival.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        if logger is None:
            self.logger = logging.getLogger("HeuristicBotV1")
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger = logger
        self.estado_mano: Optional[GameState] = None

    def set_estado(self, estado: GameState) -> None:
        """Configura el estado de la mano actual."""
        self.estado_mano = estado
        self.logger.debug(f"Nueva mano V1. Cartas iniciales: {estado.cartas_iniciales}")

    def evaluar_iniciativa(self) -> Tuple[Optional[str], Optional[Card]]:
        """Evalúa si cantar algo o qué carta jugar."""
        estado = self.estado_mano
        
        if not estado.cartas_restantes:
            return None, None

        # 1. Proactividad: Evaluar Envido (Solo Ronda 1)
        if estado.fase_actual == "envido_disponible" and estado.estado_envido == 0:
            if estado.puntos_envido_mano >= 26:
                return "ENVIDO", None
                
        # 2. Proactividad: Evaluar Truco
        if estado.estado_truco == 0:
            tiene_carta_fuerte = any(c.jerarquia >= 9 for c in estado.cartas_restantes)
            if tiene_carta_fuerte:
                return "TRUCO", None

        # 3. Jugar Carta
        carta_a_jugar = None
        estado.cartas_restantes.sort(key=lambda c: c.jerarquia)
        
        if not estado.cartas_en_mesa:
            # Abre con carta alta
            carta_a_jugar = estado.cartas_restantes[-1]
        else:
            # Responde al rival
            rival_carta = estado.cartas_en_mesa[0][1]
            superadoras = [c for c in estado.cartas_restantes if c.jerarquia > rival_carta.jerarquia]
            
            if superadoras:
                carta_a_jugar = superadoras[0]  # Menor de las superadoras
            else:
                carta_a_jugar = estado.cartas_restantes[0]  # No puede matar, tira la más baja
                
        return None, carta_a_jugar

    def responder_apuesta(self, tipo_apuesta: str, nivel_apuesta: int) -> str:
        """Responde a una apuesta del rival."""
        estado = self.estado_mano
        
        if tipo_apuesta == "envido":
            pts = estado.puntos_envido_mano
            if pts >= 26:
                return "Quiero"
            return "No Quiero"
            
        elif tipo_apuesta == "truco":
            tiene_carta_fuerte = any(c.jerarquia >= 9 for c in estado.cartas_restantes)
            if tiene_carta_fuerte:
                return "Quiero"
            return "No Quiero"
            
        return "No Quiero"

    def jugar_carta(self, carta: Card) -> None:
        """Registra que el bot jugó una carta."""
        self.estado_mano.cartas_restantes.remove(carta)
        self.estado_mano.cartas_en_mesa.append(("bot", carta))
        self.estado_mano.fase_actual = "juego_cartas"
        self.logger.debug(f"Bot V1 jugó {carta}")

    def registrar_carta_rival(self, carta: Card) -> None:
        """Registra una carta jugada por el rival."""
        self.estado_mano.cartas_en_mesa.append(("rival", carta))
        self.estado_mano.fase_actual = "juego_cartas"
        self.logger.debug(f"Rival jugó {carta}")

    def evaluar_ganador_ronda(self) -> Optional[str]:
        """Evalúa quién ganó la ronda actual."""
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
            self.logger.debug(f"Fin de ronda. Mesa: {carta1} vs {carta2}. Ganador: {ganador}")
            
            self.estado_mano.cartas_en_mesa = []
            return ganador
        return None

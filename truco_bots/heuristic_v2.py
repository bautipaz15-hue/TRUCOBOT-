import logging
from typing import Optional, Tuple
from truco_core.card import Card
from truco_core.state import GameState
from truco_bots.base import BaseBot

class HeuristicBotV2(BaseBot):
    """
    Bot heurístico de Nivel 2.6.
    - Probabilidad de victoria.
    - Envido dinámico.
    - Truco con umbrales de probabilidad.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        if logger is None:
            self.logger = logging.getLogger("HeuristicBotV2")
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger = logger
        self.estado_mano: Optional[GameState] = None

    def set_estado(self, estado: GameState) -> None:
        self.estado_mano = estado
        self.logger.debug(f"Nueva mano V2. Cartas: {estado.cartas_iniciales}")

    def _calcular_probabilidad_victoria(self) -> float:
        if not self.estado_mano.cartas_restantes:
            return 0.0
            
        poderes = [c.jerarquia for c in self.estado_mano.cartas_restantes]
        
        if len(poderes) == 3:
            if max(poderes) >= 12: return 0.85
            elif max(poderes) >= 10: 
                return 0.70 if sum(poderes) > 20 else 0.5
            return 0.3
        elif len(poderes) == 2:
            if max(poderes) >= 12: return 0.9
            if max(poderes) >= 9: return 0.7
            return 0.4
        else:
            if max(poderes) >= 12: return 0.9
            if max(poderes) >= 10: return 0.8
            return 0.5

    def evaluar_iniciativa(self) -> Tuple[Optional[str], Optional[Card]]:
        estado = self.estado_mano
        
        if not estado.cartas_restantes:
            return None, None
            
        prob = self._calcular_probabilidad_victoria()
        evaluacion = f"Prob victoria: {prob:.2f}. Fase: {estado.fase_actual}"
        
        # 1. Proactividad: Evaluar Envido (Solo Ronda 1)
        if estado.fase_actual == "envido_disponible" and estado.estado_envido == 0:
            if estado.puntos_envido_mano >= 30:
                decision = "REAL ENVIDO"
                estado.bot_canto_envido_nivel = 2
                self.logger.debug(f"[INICIATIVA] Envido alto ({estado.puntos_envido_mano}) -> DECISIÓN: {decision}")
                return decision, None
            elif estado.puntos_envido_mano >= 27:
                decision = "ENVIDO"
                estado.bot_canto_envido_nivel = 1
                self.logger.debug(f"[INICIATIVA] Envido medio ({estado.puntos_envido_mano}) -> DECISIÓN: {decision}")
                return decision, None
                
        # 2. Proactividad: Evaluar Truco
        if prob > 0.80 and estado.estado_truco == 0:
            decision = "TRUCO"
            self.logger.debug(f"[INICIATIVA] {evaluacion} -> DECISIÓN: {decision}")
            return decision, None
        elif estado.estado_truco == 1 and estado.turno_apuesta_truco == "bot":
            if max([c.jerarquia for c in estado.cartas_restantes]) >= 12:
                decision = "RETRUCO"
                self.logger.debug(f"[INICIATIVA] Tengo carta brava -> DECISIÓN: {decision}")
                return decision, None

        # 3. Jugar Carta
        carta_a_jugar = None
        if not estado.cartas_en_mesa:
            estado.cartas_restantes.sort(key=lambda c: c.jerarquia)
            carta_a_jugar = estado.cartas_restantes[0]
            decision = f"Juego carta baja: {carta_a_jugar}"
        else:
            rival_carta = estado.cartas_en_mesa[0][1]
            rival_poder = rival_carta.jerarquia
            
            superadoras = [c for c in estado.cartas_restantes if c.jerarquia > rival_poder]
            if superadoras:
                superadoras.sort(key=lambda c: c.jerarquia)
                carta_a_jugar = superadoras[0]
                decision = f"Juego {carta_a_jugar} superando {rival_carta}"
            else:
                estado.cartas_restantes.sort(key=lambda c: c.jerarquia)
                carta_a_jugar = estado.cartas_restantes[0]
                decision = f"Juego {carta_a_jugar} entregando ronda ante {rival_carta}"
                
        self.logger.debug(f"[INICIATIVA] No canto nada, procedo a jugar carta -> DECISIÓN: {decision}")
        return None, carta_a_jugar

    def responder_apuesta(self, tipo_apuesta: str, nivel_apuesta: int) -> str:
        estado = self.estado_mano
        
        if tipo_apuesta == "envido":
            pts = estado.puntos_envido_mano
            if nivel_apuesta == 1:
                resp = "Quiero" if pts >= 26 else "No Quiero"
            elif nivel_apuesta == 2: 
                resp = "Quiero" if pts >= 28 else "No Quiero"
            elif nivel_apuesta == 3: # Falta Envido
                puntos_propios = estado.puntos_bot
                faltan_rival = 30 - estado.puntos_rival
                
                # Manejar getattr para compatibilidad (por si el GameState de core no tiene atributos extra yet)
                bot_canto_nivel = getattr(estado, 'bot_canto_envido_nivel', 0)
                if bot_canto_nivel >= 2 and pts >= 30:
                    resp = "Quiero"
                elif puntos_propios < 10:
                    resp = "Quiero" if pts >= 28 else "No Quiero" 
                elif puntos_propios < 20:
                    resp = "Quiero" if pts >= 29 else "No Quiero" 
                else:
                    if pts >= 31 or faltan_rival <= 3:
                        resp = "Quiero"
                    else:
                        resp = "No Quiero"
            else:
                resp = "No Quiero"
            self.logger.debug(f"Rival canta {tipo_apuesta} nivel {nivel_apuesta}. Bot responde: {resp} (Puntos: {pts})")
            return resp
            
        elif tipo_apuesta == "truco":
            poderes = [c.jerarquia for c in estado.cartas_restantes]
            max_poder = max(poderes) if poderes else 0
            
            if nivel_apuesta == 1: 
                resp = "Quiero" if max_poder >= 10 and len(poderes) >= 2 else "No Quiero"
            elif nivel_apuesta == 2: 
                resp = "Quiero" if max_poder >= 12 else "No Quiero"
            elif nivel_apuesta == 3: 
                resp = "Quiero" if max_poder >= 13 else "No Quiero"
            else:
                resp = "No Quiero"
            self.logger.debug(f"Rival canta {tipo_apuesta} nivel {nivel_apuesta}. Bot responde: {resp}")
            return resp
        
        return "No Quiero"

    def jugar_carta(self, carta: Card) -> None:
        self.estado_mano.cartas_restantes.remove(carta)
        self.estado_mano.cartas_en_mesa.append(("bot", carta))
        self.estado_mano.fase_actual = "juego_cartas"
        self.logger.debug(f"Bot jugó {carta}")

    def registrar_carta_rival(self, carta: Card) -> None:
        self.estado_mano.cartas_en_mesa.append(("rival", carta))
        self.estado_mano.fase_actual = "juego_cartas"
        self.logger.debug(f"Rival jugó {carta}")

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
            self.logger.debug(f"Fin de ronda. Mesa: {carta1} vs {carta2}. Ganador: {ganador}")
            
            self.estado_mano.cartas_en_mesa = []
            return ganador
        return None

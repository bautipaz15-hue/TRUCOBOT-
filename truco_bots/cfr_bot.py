import logging
import random
from typing import Optional, Tuple
from truco_core.card import Card
from truco_core.state import GameState
from truco_bots.base import BaseBot
from truco_bots.cfr_engine import CFR_Engine, generar_infoset

class CFRBot(BaseBot):
    """
    Bot de Nivel 4 (CFR).
    - Busca en el perfil CFR de estrategia.
    - Usa fallback heurístico de v3 si no encuentra el InfoSet.
    """
    
    def __init__(self, model_path: Optional[str] = None, logger: Optional[logging.Logger] = None):
        if logger is None:
            self.logger = logging.getLogger("CFRBot")
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger = logger
        self.estado_mano: Optional[GameState] = None
        self.cfr = CFR_Engine(model_path)

    def set_estado(self, estado: GameState) -> None:
        self.estado_mano = estado
        self.logger.debug(f"Nueva mano CFR. Cartas: {estado.cartas_iniciales}")

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

    def _buscar_carta_por_shortname(self, short_name: str) -> Card:
        for c in self.estado_mano.cartas_restantes:
            if short_name == f"{c.valor}{c.palo[0]}":
                return c
            if hasattr(c, 'to_short') and short_name == c.to_short():
                return c
        return self.estado_mano.cartas_restantes[0]

    def evaluar_iniciativa(self) -> Tuple[Optional[str], Optional[Card]]:
        estado = self.estado_mano
        
        if not estado.cartas_restantes:
            return None, None
            
        infoset = generar_infoset(estado)
        accion_cfr = self.cfr.get_action(infoset)
        
        if accion_cfr:
            self.logger.debug(f"CFR InfoSet encontrado: {infoset} -> Acción: {accion_cfr}")
            if accion_cfr.startswith("JUGAR_"):
                carta_str = accion_cfr.split("_")[1]
                carta = self._buscar_carta_por_shortname(carta_str)
                return None, carta
            elif accion_cfr.startswith("CANTAR_"):
                canto = accion_cfr.split("_")[1].replace("-", " ")
                return canto, None

        self.logger.debug(f"CFR InfoSet NO encontrado: {infoset}. Ejecutando Fallback Heurístico.")
        
        prob = self._calcular_probabilidad_victoria()
        
        # 1. Proactividad: Evaluar Envido
        if estado.fase_actual == "envido_disponible" and estado.estado_envido == 0:
            if estado.puntos_envido_mano >= 30:
                decision = "REAL ENVIDO"
                setattr(estado, 'bot_canto_envido_nivel', 2)
                return decision, None
            elif estado.puntos_envido_mano >= 27:
                decision = "ENVIDO"
                setattr(estado, 'bot_canto_envido_nivel', 1)
                return decision, None
                
        # 2. Proactividad: Evaluar Truco
        if estado.estado_truco == 0:
            gano_ronda_1 = len(estado.resultados_rondas) > 0 and estado.resultados_rondas[-1] == "bot"
            if prob > 0.80:
                return "TRUCO", None
            elif gano_ronda_1 and prob < 0.40 and random.random() < 0.20:
                return "TRUCO", None
                
        elif estado.estado_truco == 1 and estado.turno_apuesta_truco == "bot":
            if max([c.jerarquia for c in estado.cartas_restantes]) >= 12:
                return "RETRUCO", None

        # 3. Jugar Carta
        carta_a_jugar = None
        if not estado.cartas_en_mesa:
            estado.cartas_restantes.sort(key=lambda c: c.jerarquia)
            poderes = [c.jerarquia for c in estado.cartas_restantes]
            max_poder = max(poderes) if poderes else 0
            
            if max_poder >= 9:
                if max_poder < 13: 
                    carta_a_jugar = estado.cartas_restantes[-1]
                else: 
                    if len(estado.cartas_restantes) >= 2:
                        segunda_mejor = poderes[-2]
                        if segunda_mejor < 6:
                            carta_a_jugar = estado.cartas_restantes[-1]
                        else:
                            carta_a_jugar = estado.cartas_restantes[-2]
                    else:
                        carta_a_jugar = estado.cartas_restantes[-1]
            else:
                carta_a_jugar = estado.cartas_restantes[0]
        else:
            rival_carta = estado.cartas_en_mesa[0][1]
            rival_poder = rival_carta.jerarquia
            
            superadoras = [c for c in estado.cartas_restantes if c.jerarquia > rival_poder]
            if superadoras:
                superadoras.sort(key=lambda c: c.jerarquia)
                carta_a_jugar = superadoras[0]
            else:
                estado.cartas_restantes.sort(key=lambda c: c.jerarquia)
                carta_a_jugar = estado.cartas_restantes[0]
                
        return None, carta_a_jugar

    def responder_apuesta(self, tipo_apuesta: str, nivel_apuesta: int) -> str:
        estado = self.estado_mano
        
        infoset = generar_infoset(estado)
        accion_cfr = self.cfr.get_action(infoset)
        
        if accion_cfr and accion_cfr.startswith("RESPONDER_"):
            respuesta = accion_cfr.split("_")[1].replace("-", " ")
            self.logger.debug(f"CFR responde a apuesta: {respuesta}")
            return respuesta
            
        self.logger.debug(f"CFR InfoSet NO encontrado: {infoset}. Fallback Heurístico para respuesta.")
        
        if tipo_apuesta == "envido":
            pts = estado.puntos_envido_mano
            if nivel_apuesta == 1:
                resp = "Quiero" if pts >= 26 else "No Quiero"
            elif nivel_apuesta == 2: 
                resp = "Quiero" if pts >= 28 else "No Quiero"
            elif nivel_apuesta == 3: 
                puntos_propios = estado.puntos_bot
                faltan_rival = 30 - estado.puntos_rival
                
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
            return resp
            
        elif tipo_apuesta == "truco":
            poderes = [c.jerarquia for c in estado.cartas_restantes]
            max_poder = max(poderes) if poderes else 0
            prob_victoria = self._calcular_probabilidad_victoria()
            
            if nivel_apuesta == 1: 
                if prob_victoria >= 0.80:
                    resp = "Quiero y Retruco"
                else:
                    resp = "Quiero" if max_poder >= 10 and len(poderes) >= 2 else "No Quiero"
            elif nivel_apuesta == 2: 
                if max_poder >= 13:
                    resp = "Quiero y Vale 4"
                else:
                    resp = "Quiero" if max_poder >= 12 else "No Quiero"
            elif nivel_apuesta == 3: 
                resp = "Quiero" if max_poder >= 13 else "No Quiero"
            else:
                resp = "No Quiero"
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

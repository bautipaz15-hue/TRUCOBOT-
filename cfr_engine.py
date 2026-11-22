import json
import random

class CFR_Engine:
    def __init__(self, model_path: str = None):
        self.strategy_profile = {}
        if model_path:
            try:
                with open(model_path, 'r') as f:
                    self.strategy_profile = json.load(f)
            except FileNotFoundError:
                print(f"Modelo no encontrado en {model_path}. Iniciando perfil vacío.")
                
    def get_action(self, infoset: str) -> str:
        """
        Retorna la acción seleccionada según las probabilidades del perfil,
        o None si el infoset no existe (disparando el fallback).
        """
        if infoset in self.strategy_profile:
            strategy = self.strategy_profile[infoset]
            actions = list(strategy.keys())
            probs = list(strategy.values())
            return random.choices(actions, weights=probs, k=1)[0]
        return None

def generar_infoset(estado) -> str:
    """
    Convierte el EstadoMano actual en un string único (InfoSet).
    Ejemplo de hash: [1E,7O,4B]|RivalTiro:3C|Apuesta:E1-T1|Pts:14-14
    """
    def short_name(carta) -> str:
        nombre = carta.obtener_nombre()
        if " " in nombre:
            val, palo = nombre.split(" ")
            return f"{val}{palo[0]}"
        # Si es un número sin palo en el nombre (porque no importa el palo para su jerarquía)
        # obtenemos el palo original.
        return f"{carta.valor}{carta.palo[0]}"

    # Cartas en mano del bot (ordenadas por jerarquía para que sea consistente)
    cartas_mano = sorted(estado.cartas_restantes, key=lambda c: c.obtener_jerarquia(), reverse=True)
    cartas_str = ",".join([short_name(c) for c in cartas_mano])
    
    # Cartas jugadas en la mesa por el rival
    rival_cartas = [short_name(c) for jugador, c in estado.cartas_en_mesa if jugador == "rival"]
    rival_tiro_str = f"RivalTiro:{','.join(rival_cartas)}" if rival_cartas else "RivalTiro:Ninguna"
    
    # Estado de apuestas
    apuesta_str = f"Apuesta:E{estado.estado_envido}-T{estado.estado_truco}"
    
    # Tanteador
    puntos_str = f"Pts:{estado.puntos_bot}-{estado.puntos_rival}"
    
    return f"[{cartas_str}]|{rival_tiro_str}|{apuesta_str}|{puntos_str}"

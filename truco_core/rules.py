"""
Reglas y lógica general para cálculos del Truco.
"""
from typing import List
from .card import Card

# Puntos otorgados por cada canto de envido
PUNTOS_ENVIDO = {
    'no_cantado': 0,
    'envido': 2,
    'envido_envido': 4,
    'real_envido': 3,
    'falta_envido': -1, # Requiere cálculo dinámico según los puntos de los jugadores
    'no_quiero_envido': 1,
    'no_quiero_real_envido': 1,
    'no_quiero_envido_envido': 2,
    'no_quiero_falta_envido': 1 # Generalmente 1, pero depende de qué se haya cantado antes
}

# Puntos otorgados por cada etapa del truco
PUNTOS_TRUCO = {
    'no_cantado': 1,
    'truco': 2,
    'retruco': 3,
    'vale_cuatro': 4,
    'no_quiero': 1 # Si no se quiere el truco, se otorgan los puntos de la apuesta anterior (1 para truco, etc.)
}

def calcular_envido(cartas: List[Card]) -> int:
    """
    Calcula los puntos de envido para una mano dada de cartas.
    """
    if not cartas:
        return 0
        
    palos = {}
    for c in cartas:
        if c.palo not in palos:
            palos[c.palo] = []
        palos[c.palo].append(c.valor_envido)
        
    max_envido = 0
    # Calcular el envido si hay 2 o más cartas del mismo palo
    for palo, valores in palos.items():
        if len(valores) >= 2:
            valores.sort(reverse=True)
            puntos = 20 + valores[0] + valores[1]
            if puntos > max_envido:
                max_envido = puntos
                
    # Si no hay cartas del mismo palo, el envido es el mayor valor individual
    if max_envido == 0:
        for c in cartas:
            if c.valor_envido > max_envido:
                max_envido = c.valor_envido
                
    return max_envido

"""
Paquete principal con la lógica central y modelos del juego de Truco.
"""
from .card import Card
from .deck import Deck
from .rules import calcular_envido, PUNTOS_ENVIDO, PUNTOS_TRUCO
from .state import GameState

__all__ = ['Card', 'Deck', 'calcular_envido', 'PUNTOS_ENVIDO', 'PUNTOS_TRUCO', 'GameState']

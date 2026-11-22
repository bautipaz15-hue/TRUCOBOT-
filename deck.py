"""
Representación del mazo del juego.
"""
import random
from typing import List
from .card import Card, PALOS, VALORES

class Deck:
    """Mazo de cartas españolas (40 cartas, sin ochos ni nueves)."""
    
    def __init__(self):
        """Inicializa el mazo con las 40 cartas y sin mezclar."""
        self.cartas: List[Card] = []
        self._inicializar()
        
    def _inicializar(self) -> None:
        """Genera las cartas del mazo."""
        self.cartas = [Card(valor, palo) for palo in PALOS for valor in VALORES]
        
    def mezclar(self) -> None:
        """Mezcla aleatoriamente las cartas en el mazo."""
        random.shuffle(self.cartas)
        
    def repartir(self, cantidad: int) -> List[Card]:
        """Extrae la cantidad indicada de cartas del mazo."""
        repartidas = []
        for _ in range(cantidad):
            if self.cartas:
                repartidas.append(self.cartas.pop())
        return repartidas

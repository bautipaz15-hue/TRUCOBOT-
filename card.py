"""
Representación unificada de la carta del Truco.
"""
from typing import Optional, Tuple

# Constantes del juego
PALOS = ['Espadas', 'Bastos', 'Oro', 'Copa']
VALORES = ['1', '2', '3', '4', '5', '6', '7', '10', '11', '12']

# Mapping palo -> index para conversión a entero RL (0..39)
PALO_A_IDX = {'Espadas': 0, 'Bastos': 1, 'Oro': 2, 'Copa': 3}
IDX_A_PALO = {v: k for k, v in PALO_A_IDX.items()}

# Mapping valor -> index
VALOR_A_IDX = {v: i for i, v in enumerate(VALORES)}
IDX_A_VALOR = {i: v for v, i in VALOR_A_IDX.items()}

# Jerarquía completa de cartas (poder 1 a 14)
JERARQUIA_TRUCO = {
    '1 Espadas': 14,
    '1 Bastos': 13,
    '7 Espadas': 12,
    '7 Oro': 11,
    '3': 10,
    '2': 9,
    '1 Copa': 8,
    '1 Oro': 8,
    '12': 7,
    '11': 6,
    '10': 5,
    '7 Copa': 4,
    '7 Bastos': 4,
    '6': 3,
    '5': 2,
    '4': 1
}

class Card:
    """Clase que representa una carta del truco."""
    
    def __init__(self, valor: str, palo: str):
        self.valor = str(valor)
        self.palo = palo.capitalize()
        
    @property
    def nombre(self) -> str:
        """Devuelve el nombre de la carta para buscar su jerarquía."""
        nom_unico = f"{self.valor} {self.palo}"
        if nom_unico in JERARQUIA_TRUCO:
            return nom_unico
        return self.valor
            
    @property
    def jerarquia(self) -> int:
        """Devuelve el poder de la carta (1 a 14)."""
        return JERARQUIA_TRUCO[self.nombre]
        
    @property
    def valor_envido(self) -> int:
        """Devuelve el valor de la carta para el envido (0 para figuras, valor para el resto)."""
        v = int(self.valor)
        if v >= 10:
            return 0
        return v
        
    def to_int(self) -> int:
        """Convierte la carta a un entero (0..39) para RL env."""
        return PALO_A_IDX[self.palo] * 10 + VALOR_A_IDX[self.valor]
        
    def to_short(self) -> str:
        """Convierte la carta a nombre corto para CFR (ej: '1E', '7O')."""
        return f"{self.valor}{self.palo[0]}"
        
    def to_tuple(self) -> Tuple[int, str]:
        """Convierte a tupla (valor, palo) para formato legacy de demo."""
        return (int(self.valor), self.palo.lower())
        
    @classmethod
    def from_int(cls, card_int: int) -> 'Card':
        """Crea una carta a partir de un entero de RL (0..39)."""
        palo_idx = card_int // 10
        valor_idx = card_int % 10
        return cls(IDX_A_VALOR[valor_idx], IDX_A_PALO[palo_idx])
        
    @classmethod
    def from_short(cls, short: str) -> 'Card':
        """Crea una carta a partir de un nombre corto de CFR (ej: '1E')."""
        valor = short[:-1]
        palo_inicial = short[-1].upper()
        palo_map = {'E': 'Espadas', 'B': 'Bastos', 'O': 'Oro', 'C': 'Copa'}
        return cls(valor, palo_map[palo_inicial])
        
    @classmethod
    def from_tuple(cls, num: int, palo: str) -> 'Card':
        """Crea una carta a partir de la tupla legacy."""
        return cls(str(num), palo.capitalize())
        
    def __str__(self) -> str:
        return f"{self.valor} de {self.palo}"
        
    def __repr__(self) -> str:
        return f"Card(valor='{self.valor}', palo='{self.palo}')"
        
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return False
        return self.valor == other.valor and self.palo == other.palo
        
    def __hash__(self) -> int:
        return hash((self.valor, self.palo))

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import sys
sys.path.insert(0, '..')
from truco_core.card import Card
from truco_core.state import GameState

class BaseBot(ABC):
    """Interfaz base para todos los bots de Truco."""
    
    @abstractmethod
    def set_estado(self, estado: GameState) -> None:
        """Configura el estado de la mano actual."""
        pass
    
    @abstractmethod
    def evaluar_iniciativa(self) -> Tuple[Optional[str], Optional[Card]]:
        """Evalúa si cantar algo o qué carta jugar. Returns (canto, carta)."""
        pass
    
    @abstractmethod
    def responder_apuesta(self, tipo_apuesta: str, nivel_apuesta: int) -> str:
        """Responde a una apuesta del rival. Returns 'Quiero', 'No Quiero', etc."""
        pass
    
    def jugar_carta(self, carta: Card) -> None:
        """Registra que el bot jugó una carta."""
        pass
    
    def registrar_carta_rival(self, carta: Card) -> None:
        """Registra una carta jugada por el rival."""
        pass
    
    def evaluar_ganador_ronda(self) -> Optional[str]:
        """Evalúa quién ganó la ronda actual."""
        pass

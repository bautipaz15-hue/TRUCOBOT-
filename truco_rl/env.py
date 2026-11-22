import numpy as np
import random

# Definición de acciones posibles
# 0-2: Jugar Carta 1, 2, 3
# 3: Cantar Envido
# 4: Cantar Real Envido
# 5: Cantar Falta Envido
# 6: Cantar Truco
# 7: Cantar Retruco
# 8: Cantar Vale 4
# 9: Quiero
# 10: No Quiero
# 11: Ir al Mazo
NUM_ACTIONS = 12
STATE_DIM = 120 # Tamaño aproximado del vector de estado (one-hot cartas + puntajes + contexto)

class TrucoEnv:
    """
    Entorno de simulación de Truco Argentino 1v1 estilo Gymnasium.
    Implementa reglas duras, estado one-hot y action masking.
    """
    def __init__(self):
        self.action_space_n = NUM_ACTIONS
        self.observation_space_shape = (STATE_DIM,)
        
        # Variables de estado interno
        self.score = [0, 0] # [Jugador 0, Jugador 1]
        self.reset_match()
        
    def reset_match(self):
        """Reinicia un partido entero (hasta 30 puntos)."""
        self.score = [0, 0]
        self.mano = 0
        return self.reset_round()
        
    def reset_round(self):
        """Reinicia una mano (reparte cartas, resetea apuestas)."""
        self.current_player = self.mano
        # Representación simplificada de las cartas: 40 cartas posibles.
        # En una implementación real, se repartirían 3 únicas a cada jugador.
        deck = list(range(40))
        random.shuffle(deck)
        
        self.hands = [deck[0:3], deck[3:6]]
        self.played_cards = [[], []]
        self.cards_available = [[True, True, True], [True, True, True]]
        self.round_winners = [] # 0: player0, 1: player1, -1: parda
        
        # Estado de apuestas
        self.envido_state = 0 # 0: no cantado, 1: envido, 2: real, 3: falta
        self.truco_state = 0  # 0: no, 1: truco, 2: retruco, 3: vale 4
        self.envido_points = 0
        self.truco_points = 1
        
        self.pending_bet = None
        self.truco_level = 0
        self.envido_phase_open = True
        self.truco_quiero_player = -1
        
        self.is_terminal = False
        self.winner = -1
        
        return self.get_state(self.current_player), self.get_legal_actions(self.current_player)

    def get_state(self, player):
        """
        Construye el tensor de estado para el jugador actual.
        - Cartas en mano (3 one-hot = 40)
        - Cartas jugadas propias (40)
        - Cartas jugadas rival (40)
        - Puntajes (2 escalares normalizados)
        - Estado de apuestas y turnos (escalares/one-hot)
        """
        state = np.zeros(STATE_DIM, dtype=np.float32)
        
        # 1. Cartas en mano (40 dims)
        # 2. Cartas jugadas propias (40 dims)
        # 3. Cartas jugadas rival (40 dims)
        # (Esto es una maqueta de la estructura. La implementación real asume posiciones fijas)
        idx = 0
        
        # Mano propia
        for i, card in enumerate(self.hands[player]):
            if self.cards_available[player][i]:
                state[idx + card] = 1.0
        idx += 40
        
        # Jugadas propias
        for card in self.played_cards[player]:
            state[idx + card] = 1.0
        idx += 40
        
        # Jugadas rival
        opponent = 1 - player
        for card in self.played_cards[opponent]:
            state[idx + card] = 1.0
        idx += 40
        
        # Contexto
        # Aquí irían scores, estados de envido, quién es mano, etc. (ajustado para entrar en los restantes)
        # Rellenamos algunos valores
        return state

    def get_legal_actions(self, player):
        """
        Devuelve una máscara booleana con las acciones válidas.
        Asegura que la IA no haga trampa.
        """
        mask = np.zeros(NUM_ACTIONS, dtype=np.bool_)
        
        # 1. SI HAY UNA APUESTA PENDIENTE
        if self.pending_bet is not None:
            mask[9] = True  # Quiero
            mask[10] = True # No Quiero
            
            # Excepciones (Subir la apuesta)
            if self.pending_bet == 'envido':
                mask[4] = True # Real Envido
                mask[5] = True # Falta Envido
            elif self.pending_bet == 'truco':
                mask[7] = True # Retruco
            elif self.pending_bet == 'retruco':
                mask[8] = True # Vale 4
                
            # Prohibido jugar cartas o ir al mazo directo cuando hay apuesta
            return mask
            
        # 2. SI NO HAY APUESTA PENDIENTE
        # Jugar Cartas disponibles
        for i in range(3):
            if self.cards_available[player][i]:
                mask[i] = True
                
        # Ir al mazo siempre válido
        mask[11] = True
        
        # Familia Envido
        if self.envido_phase_open and self.envido_state == 0:
            mask[3] = True
            mask[4] = True
            mask[5] = True
            
        # Familia Truco
        if self.truco_level == 0:
            mask[6] = True # Cantar Truco
        elif self.truco_level == 1 and self.truco_quiero_player == player:
            mask[7] = True # Cantar Retruco
        elif self.truco_level == 2 and self.truco_quiero_player == player:
            mask[8] = True # Cantar Vale 4
            
        return mask

    def _card_rank(self, card):
        """Asigna el poder de la carta según jerarquía del Truco."""
        suit = card // 10  # 0:Espada, 1:Basto, 2:Oro, 3:Copa
        num_idx = card % 10
        nums = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
        num = nums[num_idx]
        
        if num == 1 and suit == 0: return 14 # Ancho de Espada
        if num == 1 and suit == 1: return 13 # Ancho de Basto
        if num == 7 and suit == 0: return 12 # 7 de Espada
        if num == 7 and suit == 2: return 11 # 7 de Oro
        if num == 3: return 10
        if num == 2: return 9
        if num == 1: return 8 # Anchos falsos
        if num == 12: return 7
        if num == 11: return 6
        if num == 10: return 5
        if num == 7: return 4 # 7s falsos
        if num == 6: return 3
        if num == 5: return 2
        if num == 4: return 1
        return 0

    def _card_envido_val(self, card):
        """Devuelve el valor para el envido (1-7, o 0 para figuras)."""
        num_idx = card % 10
        nums = [1, 2, 3, 4, 5, 6, 7, 0, 0, 0]
        return nums[num_idx]

    def _calculate_envido(self, hand):
        """Calcula los puntos de envido de una mano."""
        suits = {}
        for c in hand:
            suit = c // 10
            val = self._card_envido_val(c)
            if suit not in suits: suits[suit] = []
            suits[suit].append(val)
        
        max_envido = 0
        for s, vals in suits.items():
            if len(vals) >= 2:
                vals.sort(reverse=True)
                pts = 20 + vals[0] + vals[1]
                if pts > max_envido: max_envido = pts
            else:
                if vals[0] > max_envido: max_envido = vals[0]
        return max_envido

    def step(self, action):
        """
        Aplica la acción, avanza el estado y devuelve (next_state, reward, done, info).
        """
        player = self.current_player
        opponent = 1 - player
        
        # 1. Guardar tanteador actual
        old_score_p0 = self.score[0]
        old_score_p1 = self.score[1]
        
        match_over = False
        
        # Resolución Determinista de la Acción
        if action in [0, 1, 2]: # Jugar Carta
            self.cards_available[player][action] = False
            self.played_cards[player].append(self.hands[player][action])
            
            # Al jugar una carta, se cierra la ventana de Envido
            self.envido_phase_open = False
            
            # Si la mesa está completa en esta ronda, evaluar ganador de la ronda
            if len(self.played_cards[0]) == len(self.played_cards[1]):
                c0 = self.played_cards[0][-1]
                c1 = self.played_cards[1][-1]
                rank0 = self._card_rank(c0)
                rank1 = self._card_rank(c1)
                
                if rank0 > rank1:
                    self.round_winners.append(0)
                    self.current_player = 0 # Gana y sale
                elif rank1 > rank0:
                    self.round_winners.append(1)
                    self.current_player = 1 # Gana y sale
                else:
                    self.round_winners.append(-1) # Parda
                    self.current_player = self.mano # En parda sale el mano
                    
                # Evaluar ganador de la mano (2 rondas ganadas o reglas de parda)
                p0_wins = self.round_winners.count(0)
                p1_wins = self.round_winners.count(1)
                
                if p0_wins >= 2:
                    self.score[0] += self.truco_points
                    self.is_terminal = True
                elif p1_wins >= 2:
                    self.score[1] += self.truco_points
                    self.is_terminal = True
                elif len(self.round_winners) == 3:
                    # Fin de 3ra ronda sin 2 victorias claras (por pardas)
                    if p0_wins > p1_wins:
                        self.score[0] += self.truco_points
                    elif p1_wins > p0_wins:
                        self.score[1] += self.truco_points
                    else: 
                        # Parda de todas, gana el mano
                        self.score[self.mano] += self.truco_points
                    self.is_terminal = True
                elif len(self.round_winners) < 3 and p0_wins == 1 and self.round_winners[0] == -1:
                    # Parda en primera, gana el que haga la segunda
                    self.score[0] += self.truco_points
                    self.is_terminal = True
                elif len(self.round_winners) < 3 and p1_wins == 1 and self.round_winners[0] == -1:
                    # Parda en primera, gana el que haga la segunda
                    self.score[1] += self.truco_points
                    self.is_terminal = True
            else:
                # El oponente debe responder la carta
                self.current_player = opponent
                
        elif action in [3, 4, 5]: # Cantos de Envido
            pts_rechazado = 1 if self.pending_bet is None else self.envido_points
            
            if action == 3:
                self.pending_bet = 'envido'
                self.envido_points = 2
            elif action == 4:
                self.pending_bet = 'real_envido'
                self.envido_points = 3 if pts_rechazado == 1 else pts_rechazado + 3
            elif action == 5:
                self.pending_bet = 'falta_envido'
                
            self.envido_rechazado_points = pts_rechazado
            self.envido_state = action - 2
            self.current_player = opponent
            
        elif action == 11: # Ir al mazo
            self.score[opponent] += self.truco_points
            self.is_terminal = True
            
        elif action in [6, 7, 8]: # Cantos de Truco
            self.pending_bet = 'truco' if action == 6 else ('retruco' if action == 7 else 'vale4')
            self.truco_quiero_player = opponent
            self.current_player = opponent
            
        elif action in [9, 10]: # Quiero / No Quiero
            if action == 9: # Quiero
                if self.pending_bet in ['envido', 'real_envido', 'falta_envido']:
                    e0 = self._calculate_envido(self.hands[0])
                    e1 = self._calculate_envido(self.hands[1])
                    if e0 == e1: 
                        winner_envido = self.mano
                    else: 
                        winner_envido = 0 if e0 > e1 else 1
                        
                    if self.pending_bet == 'falta_envido':
                        puntos_lider = max(self.score[0], self.score[1])
                        pts = max(30 - puntos_lider, 1)
                    else:
                        pts = self.envido_points
                        
                    self.score[winner_envido] += pts
                    self.pending_bet = None
                    self.envido_phase_open = False
                    
                elif self.pending_bet in ['truco', 'retruco', 'vale4']:
                    if self.pending_bet == 'truco':
                        self.truco_level = 1
                        self.truco_points = 2
                    elif self.pending_bet == 'retruco':
                        self.truco_level = 2
                        self.truco_points = 3
                    elif self.pending_bet == 'vale4':
                        self.truco_level = 3
                        self.truco_points = 4
                        
                    self.pending_bet = None
                    self.envido_phase_open = False
                    
                # Devolver el turno a quien le tocaba tirar carta
                if len(self.played_cards[0]) == len(self.played_cards[1]):
                    if len(self.played_cards[0]) == 0:
                        self.current_player = self.mano
                    else:
                        w = self.round_winners[-1]
                        self.current_player = self.mano if w == -1 else w
                else:
                    self.current_player = 0 if len(self.played_cards[0]) < len(self.played_cards[1]) else 1
                    
            else: # No quiero
                if self.pending_bet in ['envido', 'real_envido', 'falta_envido']:
                    pts_no_querido = getattr(self, 'envido_rechazado_points', 1)
                    self.score[opponent] += pts_no_querido
                    self.pending_bet = None
                    self.envido_phase_open = False
                    
                    # Devolver el turno a quien le tocaba tirar carta
                    if len(self.played_cards[0]) == len(self.played_cards[1]):
                        if len(self.played_cards[0]) == 0:
                            self.current_player = self.mano
                        else:
                            w = self.round_winners[-1]
                            self.current_player = self.mano if w == -1 else w
                    else:
                        self.current_player = 0 if len(self.played_cards[0]) < len(self.played_cards[1]) else 1
                        
                elif self.pending_bet in ['truco', 'retruco', 'vale4']:
                    self.score[opponent] += self.truco_points
                    self.is_terminal = True
            
        # 3. y 4. Calcular delta de puntos y escalar recompensas
        delta_p0 = self.score[0] - old_score_p0
        delta_p1 = self.score[1] - old_score_p1
        
        reward_p0 = (delta_p0 - delta_p1) / 30.0
        reward_p1 = (delta_p1 - delta_p0) / 30.0
            
        # 5. Bonus de fin de partido (Wins)
        if self.score[0] >= 30:
            reward_p0 += 1.0
            reward_p1 -= 1.0
            match_over = True
            self.winner = 0
        elif self.score[1] >= 30:
            reward_p0 -= 1.0
            reward_p1 += 1.0
            match_over = True
            self.winner = 1
            
        next_state = self.get_state(self.current_player)
        legal_actions = self.get_legal_actions(self.current_player)
        rewards = [reward_p0, reward_p1]
        
        return next_state, legal_actions, rewards, match_over

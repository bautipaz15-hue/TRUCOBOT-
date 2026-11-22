import os
import torch
import numpy as np
from truco_rl.env import TrucoEnv, STATE_DIM, NUM_ACTIONS
from truco_rl.network import TrucoActorCritic

class HeuristicTrucoBot:
    """
    Un bot tradicional basado en reglas fijas y heurísticas del Truco Argentino.
    Juega de forma lógica: valora sus cartas, canta envido si tiene buen tanto, 
    y defiende o ataca según la jerarquía de sus naipes.
    """
    def __init__(self, player_id):
        self.player_id = player_id

    def select_action(self, env):
        mask = env.get_legal_actions(self.player_id)
        valid_actions = [i for i, legal in enumerate(mask) if legal]
        
        if not valid_actions:
            return 11 # Ir al mazo por seguridad si no hay opciones

        # 1. Prioridad absoluta: Responder a apuestas pendientes (Quiero / No Quiero / Subir)
        if env.pending_bet is not None:
            if 9 in valid_actions: # Si puede decir "Quiero"
                # Heurística simple: si es truco o envido, acepta la mayoría de las veces
                return 9
            return valid_actions[0]

        # 2. Fase de Envido (en la primera ronda si está abierta)
        if env.envido_phase_open and env.envido_state == 0:
            envido_pts = env._calculate_envido(env.hands[self.player_id])
            if envido_pts >= 25 and 3 in valid_actions:
                return 3 # Cantar Envido si tiene buen tanto

        # 3. Intentar cantar Truco si tiene el nivel en 0 y cartas razonables
        if env.truco_level == 0 and 6 in valid_actions:
            # Evaluar si tiene al menos una carta alta (jerarquía >= 10, ej: 3 o figura alta)
            high_cards = sum(1 for c in env.hands[self.player_id] if env._card_rank(c) >= 10)
            if high_cards >= 1:
                return 6 # Cantar Truco

        # 4. Jugar cartas (Priorizar cartas medias/bajas primero o lanzar la pesada si es necesario)
        card_actions = [a for a in valid_actions if a in [0, 1, 2]]
        if card_actions:
            # Ordenar las cartas disponibles por jerarquía real (de menor a mayor poder)
            available_cards = [(a, env.hands[self.player_id][a]) for a in card_actions]
            # Estrategia heurística: tirar una carta baja para "ver qué pasa" o gastar la alta si es necesario
            # Por simplicidad, elige la de menor jerarquía para guardarse las buenas
            available_cards.sort(key=lambda x: env._card_rank(x[1]))
            return available_cards[0][0]

        # 5. Si no hay otra opción, devuelve una acción válida al azar de las permitidas
        return np.random.choice(valid_actions)


def run_tournament():
    device = torch.device('cpu')
    print("[*] Configurando el Torneo: IA (PPO) vs Bot Heurístico")
    
    # Cargar el modelo entrenado (ajusta el nombre del checkpoint si prefieres otro)
    checkpoint_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'checkpoints', 'truco_cpu_ep4900.pth')
    
    if not os.path.exists(checkpoint_path):
        print(f"[!] No se encontró el checkpoint en {checkpoint_path}. Asegúrate de que exista.")
        return

    network = TrucoActorCritic(state_dim=STATE_DIM, num_actions=NUM_ACTIONS, hidden_size=128).to(device)
    network.load_state_dict(torch.load(checkpoint_path, map_location=device))
    network.eval()
    print(f"[*] Modelo cargado correctamente desde {checkpoint_path}")

    ai_id = 0  # La IA jugará como Jugador 0
    heuristic_id = 1  # El Bot Tradicional jugará como Jugador 1
    
    ai_wins = 0
    heuristic_wins = match_draws = 0
    total_matches = 500

    print(f"\n[*] Iniciando simulación de {total_matches} partidos...")
    print("=" * 50)

    for match_num in range(1, total_matches + 1):
        env = TrucoEnv()
        env.reset_match()
        heuristic_bot = HeuristicTrucoBot(heuristic_id)
        
        match_over = False
        
        # Bucle del partido hasta que alguien llegue a 30 puntos
        while not match_over:
            current_player = env.current_player
            
            if current_player == ai_id:
                # Turno de la IA
                state = env.get_state(ai_id)
                mask = env.get_legal_actions(ai_id)
                
                state_t = torch.FloatTensor(state).unsqueeze(0).to(device)
                mask_t = torch.BoolTensor(mask).unsqueeze(0).to(device)
                
                with torch.no_grad():
                    action_t, _, _, _ = network.get_action_and_value(state_t, mask_t)
                    action = action_t.item()
            else:
                # Turno del Bot Heurístico
                action = heuristic_bot.select_action(env)
            
            # Ejecutar acción en el entorno
            _, _, _, match_over = env.step(action)
            
            # Control de fin de mano para resetear ronda si el partido sigue vivo
            if env.is_terminal and not match_over:
                env.reset_round()

        # Determinar ganador del partido
        score_ai = env.score[ai_id]
        score_heuristic = env.score[heuristic_id]
        
        if score_ai >= 30:
            ai_wins += 1
            winner_str = "🤖 IA (PPO)"
        elif score_heuristic >= 30:
            heuristic_wins += 1
            winner_str = "🧠 Bot Heurístico"
        else:
            # Por si acaso el marcador se pasa por acumulación
            if score_ai > score_heuristic:
                ai_wins += 1
                winner_str = "🤖 IA (PPO)"
            elif score_heuristic > score_ai:
                heuristic_wins += 1
                winner_str = "🧠 Bot Heurístico"
            else:
                match_draws += 1
                winner_str = "🤝 Empate"

        print(f"Partido {match_num:02d} | Ganador: {winner_str:<18} | Marcador final -> IA: {score_ai} vs Heurístico: {score_heuristic}")

    print("=" * 50)
    print("📊 RESULTADOS FINALES DEL TORNEO 📊")
    print(f"Partidos jugados: {total_matches}")
    print(f"Victorias de la IA (Ep 7500): {ai_wins} ({ (ai_wins/total_matches)*100:.1f}%)")
    print(f"Victorias del Bot Heurístico: {heuristic_wins} ({ (heuristic_wins/total_matches)*100:.1f}%)")
    print("=" * 50)

if __name__ == "__main__":
    run_tournament()
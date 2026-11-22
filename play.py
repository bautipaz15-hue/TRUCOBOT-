import os
import torch
import numpy as np
import time
from truco_rl.env import TrucoEnv, STATE_DIM, NUM_ACTIONS
from truco_rl.network import TrucoActorCritic

ACTION_NAMES = {
    0: "Jugar Carta 1",
    1: "Jugar Carta 2",
    2: "Jugar Carta 3",
    3: "Cantar Envido",
    4: "Cantar Real Envido",
    5: "Cantar Falta Envido",
    6: "Cantar Truco",
    7: "Cantar Retruco",
    8: "Cantar Vale 4",
    9: "Quiero",
    10: "No Quiero",
    11: "Ir al Mazo"
}

def get_card_name(card_code):
    """Traduce el código numérico del entorno a 'Número de Palo'."""
    if card_code is None or card_code < 0:
        return "Ninguna"
        
    suit_idx = card_code // 10
    num_idx = card_code % 10
    
    palos = {0: "Espadas", 1: "Bastos", 2: "Oro", 3: "Copa"}
    valores = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
    
    palo = palos.get(suit_idx, "Desconocido")
    valor = valores[num_idx] if 0 <= num_idx < len(valores) else "?"
    
    return f"{valor} de {palo}"

def get_action_string(action, env, player_id):
    """Le da contexto a la acción si es jugar una carta."""
    if action in [0, 1, 2]:
        card = env.hands[player_id][action]
        return f"Juega el {get_card_name(card)}"
    return ACTION_NAMES[action]

def print_state(env, human_id):
    ai_id = 1 - human_id
    
    print("\n" + "="*60)
    print(f"🏆 TANTEADOR -> Vos: {env.score[human_id]} | IA: {env.score[ai_id]}")
    
    apuesta = env.pending_bet if env.pending_bet else "Ninguna"
    truco_strs = {0: "Nada", 1: "Truco", 2: "Retruco", 3: "Vale 4"}
    print(f"🗣️  APUESTAS -> Pendiente: {apuesta.upper()} | Nivel Truco: {truco_strs.get(env.truco_level, env.truco_level)}")
    print("-" * 60)
    
    # Mostrar la Mesa de Juego
    print("🏓 MESA DE JUEGO:")
    rondas_jugadas = max(len(env.played_cards[0]), len(env.played_cards[1]))
    if rondas_jugadas == 0:
        print("  (Mesa vacía)")
    else:
        for i in range(rondas_jugadas):
            c_hum = get_card_name(env.played_cards[human_id][i]) if i < len(env.played_cards[human_id]) else "Esperando..."
            c_ai = get_card_name(env.played_cards[ai_id][i]) if i < len(env.played_cards[ai_id]) else "Esperando..."
            
            ganador_txt = ""
            if i < len(env.round_winners):
                w = env.round_winners[i]
                if w == human_id: ganador_txt = "👈 (Ganaste)"
                elif w == ai_id: ganador_txt = "👉 (Ganó IA)"
                else: ganador_txt = "🤝 (Parda)"
                
            print(f"  Ronda {i+1}: Vos [{c_hum}] vs IA [{c_ai}] {ganador_txt}")
            
    print("-" * 60)
    
    # Mostrar Cartas del Humano
    print("🃏 TUS CARTAS:")
    for i in range(3):
        if env.cards_available[human_id][i]:
            card_str = get_card_name(env.hands[human_id][i])
            print(f"  [Opción {i}] -> Jugar {card_str}")
        else:
            print(f"  [Opción {i}] -> (Ya jugada)")
    print("=" * 60)

def main():
    device = torch.device('cpu')
    print("[*] Inicializando Coliseo...")
    
    network = TrucoActorCritic(state_dim=STATE_DIM, num_actions=NUM_ACTIONS, hidden_size=128).to(device)
    
    # ARCHIVO A CARGAR (Ajustá el nombre al último que te haya tirado la consola)
    checkpoint_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'checkpoints', 'truco_cpu_ep7500.pth')
    
    if os.path.exists(checkpoint_path):
        network.load_state_dict(torch.load(checkpoint_path, map_location=device))
        print(f"[*] Cerebro IA cargado con éxito desde: {checkpoint_path}")
    else:
        print(f"[!] ERROR: No se encontró {checkpoint_path}.")
        return

    network.eval() 
    
    env = TrucoEnv()
    human_id = 0
    ai_id = 1
    
    # Inicializamos el partido (bucle que corre hasta que alguien llegue a 30)
    env.reset_match()
    
    print("\n" + "*"*60)
    print("🔥 ¡COMIENZA LA PARTIDA! 🔥")
    print("*"*60)
    
    match_over = False
    
    while not match_over:
        current_player = env.current_player
        
        if current_player == human_id:
            print_state(env, human_id)
            mask = env.get_legal_actions(human_id)
            
            print("\nAcciones válidas:")
            valid_actions = []
            for action_idx, is_legal in enumerate(mask):
                if is_legal:
                    texto_accion = get_action_string(action_idx, env, human_id)
                    print(f"  [{action_idx}] {texto_accion}")
                    valid_actions.append(action_idx)
            
            action = -1
            while action not in valid_actions:
                try:
                    user_input = input("\n=> Elegí tu acción: ")
                    action = int(user_input)
                    if action not in valid_actions:
                        print("❌ Jugada ilegal. Elegí un número de la lista permitida.")
                except ValueError:
                    print("❌ Por favor, ingresá un número entero.")
                    
            print(f"\n👤 VOS DECIDÍS: {get_action_string(action, env, human_id).upper()}")
            
            # Aplicar acción al entorno
            _, _, _, match_over = env.step(action)
            
            # Si alguien gana mano, reseteamos la ronda
            if env.is_terminal and not match_over:
                print(f"\n--- FIN DE LA MANO --- Puntos actuales -> Vos: {env.score[human_id]} | IA: {env.score[ai_id]}")
                time.sleep(2)
                env.reset_round()
            
        else:
            # Turno de la IA
            print(f"\n🤖 [La IA está calculando probabilidades...]")
            time.sleep(1.5)
            
            state = env.get_state(ai_id)
            mask = env.get_legal_actions(ai_id)
            
            state_t = torch.FloatTensor(state).unsqueeze(0).to(device)
            mask_t = torch.BoolTensor(mask).unsqueeze(0).to(device)
            
            with torch.no_grad():
                action_t, _, _, _ = network.get_action_and_value(state_t, mask_t)
                action = action_t.item()
            
            print(f"🤖 IA DECIDE: {get_action_string(action, env, ai_id).upper()}")
            
            # Aplicar acción al entorno
            _, _, _, match_over = env.step(action)
            
            # Si alguien gana mano, reseteamos la ronda
            if env.is_terminal and not match_over:
                print(f"\n--- FIN DE LA MANO --- Puntos actuales -> Vos: {env.score[human_id]} | IA: {env.score[ai_id]}")
                time.sleep(2)
                env.reset_round()
            
    print("\n" + "="*60)
    print("🏁 ¡PARTIDO TERMINADO! 🏁")
    if env.score[human_id] >= 30:
        print("🏆 ¡Felicidades, domaste a la máquina!")
    else:
        print("💀 LA IA TE DESTROZÓ.")
    print(f"Marcador Final -> Humano: {env.score[human_id]} | IA: {env.score[ai_id]}")
    print("="*60)

if __name__ == "__main__":
    main()
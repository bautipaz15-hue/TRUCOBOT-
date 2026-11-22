import os
import time
import torch
import multiprocessing as mp
import numpy as np
from truco_rl.env import TrucoEnv, NUM_ACTIONS, STATE_DIM
from truco_rl.network import TrucoActorCritic
from truco_rl.trainer import PPOTrainer, RolloutBuffer

def worker(remote, parent_remote):
    """
    Worker function para ejecutar el entorno en un proceso separado.
    """
    parent_remote.close()
    env = TrucoEnv()
    try:
        while True:
            cmd, data = remote.recv()
            if cmd == 'step':
                action = data
                next_state, next_mask, rewards, done = env.step(action)
                winner = env.winner if done else -1
                if done:
                    # Si termina el partido, reseteamos el entorno automáticamente
                    next_state, next_mask = env.reset_match()
                remote.send((next_state, next_mask, rewards, done, env.current_player, winner))
            elif cmd == 'reset':
                state, mask = env.reset_match()
                remote.send((state, mask, env.current_player, -1))
            elif cmd == 'close':
                remote.close()
                break
    except KeyboardInterrupt:
        pass
    finally:
        remote.close()

class VecEnv:
    """
    Gestor de Entornos Vectorizados usando Multiprocessing (Pipes).
    Mantiene múltiples instancias del juego corriendo en paralelo.
    """
    def __init__(self, num_envs):
        self.remotes, self.work_remotes = zip(*[mp.Pipe() for _ in range(num_envs)])
        self.ps = [mp.Process(target=worker, args=(work_remote, remote))
                   for (work_remote, remote) in zip(self.work_remotes, self.remotes)]
        for p in self.ps:
            p.daemon = True
            p.start()
        for remote in self.work_remotes:
            remote.close()
            
    def step_async(self, actions):
        for remote, action in zip(self.remotes, actions):
            remote.send(('step', action))
            
    def step_wait(self):
        results = [remote.recv() for remote in self.remotes]
        next_states, next_masks, rewards, dones, current_players, winners = zip(*results)
        return np.stack(next_states), np.stack(next_masks), np.stack(rewards), np.stack(dones), np.stack(current_players), np.stack(winners)
        
    def reset(self):
        for remote in self.remotes:
            remote.send(('reset', None))
        results = [remote.recv() for remote in self.remotes]
        states, masks, current_players, _ = zip(*results)
        return np.stack(states), np.stack(masks), np.stack(current_players)
        
    def close(self):
        for remote in self.remotes:
            remote.send(('close', None))
        for p in self.ps:
            p.join()

def run_training():
    # 1. FORZAR USO DE CPU Y MÚLTIPLES CORES
    device = torch.device('cpu')
    # Usar todos los cores lógicos disponibles (dejando 1 libre por estabilidad si es posible)
    num_envs = 24
    print(f"[*] Iniciando entrenamiento optimizado en {device} con {num_envs} entornos paralelos.")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    checkpoints_dir = os.path.join(base_dir, "checkpoints")
    historical_dir = os.path.join(checkpoints_dir, "historical")
    
    os.makedirs(checkpoints_dir, exist_ok=True)
    os.makedirs(historical_dir, exist_ok=True)
    
    # Configuración de Oponentes Históricos
    historical_network = TrucoActorCritic(state_dim=STATE_DIM, num_actions=NUM_ACTIONS, hidden_size=128).to(device)
    historical_network.eval()
    
    def load_random_historical():
        import glob
        import random
        checkpoints = glob.glob(os.path.join(historical_dir, "*.pth"))
        if checkpoints:
            ckpt = random.choice(checkpoints)
            historical_network.load_state_dict(torch.load(ckpt, map_location=device))
            historical_network.eval()
            return True
        return False
        
    has_historical_model = False
    
    # 2. Inicialización de Red Liviana (MLP 128 neuronas)
    network = TrucoActorCritic(state_dim=STATE_DIM, num_actions=NUM_ACTIONS, hidden_size=128).to(device)
    
    # Búsqueda y carga del último checkpoint (Auto-Resume)
    import glob
    checkpoints = glob.glob(os.path.join(checkpoints_dir, "truco_cpu_ep*.pth"))
    if checkpoints:
        latest_ckpt = max(checkpoints, key=os.path.getctime)
        network.load_state_dict(torch.load(latest_ckpt, map_location=device))
        print(f"[*] Reanudando entrenamiento desde checkpoint: {latest_ckpt}")
    else:
        print("[*] No se encontraron checkpoints. Arrancando entrenamiento desde cero.")
        
    trainer = PPOTrainer(network, device=device)
    
    vec_env = VecEnv(num_envs)
    
    # Buffers globales donde convergen las transiciones de todos los hilos
    buffer_p0 = RolloutBuffer()
    buffer_p1 = RolloutBuffer()
    
    # Hiperparámetros ajustados para batching en CPU
    STEPS_PER_UPDATE = 8192 # Pasos totales acumulados antes de actualizar la red
    MAX_UPDATES = 10000
    SAVE_EVERY = 50
    LOG_EVERY = 10
    
    wins_p0 = 0
    wins_p1 = 0
    total_steps = 0
    start_time = time.time()
    
    is_historical_opponent = np.random.rand(num_envs) < 0.60
    
    states, masks, current_players = vec_env.reset()
    
    print("[*] Comenzando recolección masiva de datos (Self-Play Multiprocessing)...")
    
    for update in range(1, MAX_UPDATES + 1):
        steps_collected = 0
        has_historical_model = load_random_historical()
        
        # 3. Fase de Recolección Paralela
        while steps_collected < STEPS_PER_UPDATE:
            # Inferencia batchificada para N entornos
            actions = np.zeros(num_envs, dtype=np.int64)
            log_probs = np.zeros(num_envs, dtype=np.float32)
            values = np.zeros(num_envs, dtype=np.float32)
            
            with torch.no_grad():
                states_t = torch.FloatTensor(states).to(device)
                masks_t = torch.BoolTensor(masks).to(device)
                
                if has_historical_model:
                    use_historical = (current_players == 1) & is_historical_opponent
                else:
                    use_historical = np.zeros(num_envs, dtype=bool)
                use_current = ~use_historical
                
                if np.any(use_current):
                    c_states = states_t[use_current]
                    c_masks = masks_t[use_current]
                    c_act, c_log, _, c_val = network.get_action_and_value(c_states, c_masks)
                    actions[use_current] = c_act.cpu().numpy()
                    log_probs[use_current] = c_log.cpu().numpy()
                    values[use_current] = c_val.cpu().numpy().flatten()
                    
                if np.any(use_historical):
                    h_states = states_t[use_historical]
                    h_masks = masks_t[use_historical]
                    h_act, h_log, _, h_val = historical_network.get_action_and_value(h_states, h_masks)
                    actions[use_historical] = h_act.cpu().numpy()
                    log_probs[use_historical] = h_log.cpu().numpy()
                    values[use_historical] = h_val.cpu().numpy().flatten()
            
            # Enviar acciones a los hilos de CPU
            vec_env.step_async(actions)
            next_states, next_masks, rewards, dones, next_players, winners = vec_env.step_wait()
            
            # Guardar transiciones
            for i in range(num_envs):
                player = current_players[i]
                reward = rewards[i][player] # Recompensa correspondiente al jugador activo
                
                if player == 0:
                    buffer_p0.add(states[i], actions[i], log_probs[i], reward, values[i], masks[i], dones[i])
                elif not use_historical[i]:
                    # Solo entrenamos a P1 si está usando la red actual
                    buffer_p1.add(states[i], actions[i], log_probs[i], reward, values[i], masks[i], dones[i])
                    
                if dones[i]:
                    if winners[i] == 0: wins_p0 += 1
                    elif winners[i] == 1: wins_p1 += 1
                    # Re-rollear oponente histórico para el nuevo episodio
                    is_historical_opponent[i] = np.random.rand() < 0.60
            
            states = next_states
            masks = next_masks
            current_players = next_players
            steps_collected += num_envs
            total_steps += num_envs
            
        # 4. Fase de Actualización (Backpropagation)
        loss_p0, pol_p0, val_p0 = trainer.update(buffer_p0)
        loss_p1, pol_p1, val_p1 = trainer.update(buffer_p1)
        
        buffer_p0.clear()
        buffer_p1.clear()
        
        # Logging y Métricas
        if update % LOG_EVERY == 0:
            elapsed = time.time() - start_time
            total_games = max(1, wins_p0 + wins_p1)
            winrate = wins_p0 / total_games
            fps = (LOG_EVERY * steps_collected) / elapsed
            
            print(f"Update: {update:04d} | "
                  f"WinRate P0: {winrate:.2f} | "
                  f"Steps Totales: {total_steps} | "
                  f"FPS (Steps/s): {fps:.0f} | "
                  f"Loss Avg: {(loss_p0+loss_p1)/2:.4f} | "
                  f"Tiempo: {elapsed:.1f}s")
            
            wins_p0 = 0
            wins_p1 = 0
            start_time = time.time()
            
        if update % SAVE_EVERY == 0:
            ckpt_path = os.path.join(checkpoints_dir, f"truco_cpu_ep{update}.pth")
            hist_path = os.path.join(historical_dir, f"truco_cpu_ep{update}.pth")
            state_dict = network.state_dict()
            torch.save(state_dict, ckpt_path)
            torch.save(state_dict, hist_path)
            print(f"[*] Checkpoint guardado en {ckpt_path} y liga histórica")
            
    vec_env.close()

if __name__ == "__main__":
    # Importante para que Multiprocessing en PyTorch no crashee en Linux
    mp.set_start_method("fork", force=True) 
    run_training()

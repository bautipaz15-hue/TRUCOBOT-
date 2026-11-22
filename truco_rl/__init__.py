"""
Módulo de Reinforcement Learning para TrucoBot.
Contiene el entorno Gymnasium, la red neuronal Actor-Critic,
el entrenador PPO, y las herramientas de juego/torneo.
"""
from truco_rl.env import TrucoEnv, NUM_ACTIONS, STATE_DIM
from truco_rl.network import TrucoActorCritic

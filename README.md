# TrucoBot 🃏

Bot de Truco Argentino con múltiples estrategias: desde heurísticas simples hasta Reinforcement Learning (PPO).

## Estructura del Proyecto

```
trucobot/
├── truco_core/          # Núcleo compartido (cartas, reglas, mazo, estado)
├── truco_bots/          # Estrategias de bot intercambiables
├── truco_gui/           # Interfaz Tkinter unificada
├── truco_rl/            # Pipeline de Reinforcement Learning
├── truco_web/           # Interfaz web (FastAPI)
├── checkpoints/         # Modelos entrenados generados (.pth)
└── logs/                # Logs de debug
```

## Módulos

### `truco_core/` — Núcleo del juego
Contiene la representación unificada de cartas, reglas del truco argentino, mazo y máquina de estados.

### `truco_bots/` — Estrategias de bot
- **HeuristicBotV1**: Bot básico con umbrales simples (demo)
- **HeuristicBotV2**: Bot con evaluación de riesgo y probabilidad de victoria
- **HeuristicBotV3**: Bot avanzado con bluffing y contra-apuestas tácticas
- **CFRBot**: Bot con Counterfactual Regret Minimization + fallback heurístico
- **RLBot**: Bot con red neuronal Actor-Critic entrenada con PPO

### `truco_gui/` — Interfaz gráfica
GUI Tkinter unificada que acepta cualquier bot. Incluye entrada rápida por teclado.

```bash
# Ejecutar con bot v3 (default)
python -m truco_gui.main

# Ejecutar con bot específico
python -m truco_gui.main --bot v1
python -m truco_gui.main --bot cfr
```

### `truco_rl/` — Reinforcement Learning
Pipeline completo de entrenamiento PPO con self-play multi-proceso.

```bash
# Entrenar
python -m truco_rl.train

# Jugar contra la IA (CLI)
python -m truco_rl.play

# Torneo IA vs Bot Heurístico
python -m truco_rl.tournament
```

### `truco_web/` — Interfaz Web
Servidor FastAPI para jugar contra el bot RL desde el navegador.

```bash
python -m truco_web.app
```

## Requisitos

```bash
pip install -r requirements.txt
```


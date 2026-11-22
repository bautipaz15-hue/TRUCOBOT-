from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import torch
import os
import uvicorn

from truco_rl.env import TrucoEnv, STATE_DIM, NUM_ACTIONS
from truco_rl.network import TrucoActorCritic
from truco_rl.play import get_card_name, get_action_string

app = FastAPI(title="Truco RL WebApp")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Buscamos dinámicamente el checkpoint más reciente o usamos uno por defecto
def get_latest_checkpoint():
    checkpoints_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'checkpoints')
    if not os.path.exists(checkpoints_dir):
        return None
    files = [f for f in os.listdir(checkpoints_dir) if f.endswith(".pth")]
    if not files:
        return None
    # Elegir el ep más alto, por ejemplo: truco_cpu_ep7500.pth
    files.sort(key=lambda x: int(x.split('ep')[1].split('.pth')[0]) if 'ep' in x else 0, reverse=True)
    return os.path.join(checkpoints_dir, files[0])

class GameState:
    def __init__(self):
        self.device = torch.device('cpu')
        self.network = TrucoActorCritic(state_dim=STATE_DIM, num_actions=NUM_ACTIONS, hidden_size=128).to(self.device)
        
        self.checkpoint_path = get_latest_checkpoint()
        if self.checkpoint_path and os.path.exists(self.checkpoint_path):
            self.network.load_state_dict(torch.load(self.checkpoint_path, map_location=self.device))
            print(f"[*] AI Brain loaded: {self.checkpoint_path}")
        else:
            print("[!] No checkpoint found, using untrained model")
            
        self.network.eval()
        self.env = TrucoEnv()
        self.human_id = 0
        self.ai_id = 1
        self.match_over = False
        self.log = []

game_state = GameState()

class StepRequest(BaseModel):
    action_id: int

def get_current_state_json(game: GameState):
    env = game.env
    human_id = game.human_id
    ai_id = game.ai_id
    
    # format player cards
    player_cards = []
    for i in range(3):
        if env.cards_available[human_id][i]:
            card_code = env.hands[human_id][i]
            player_cards.append({"id": i, "name": get_card_name(card_code), "played": False})
        else:
            player_cards.append({"id": i, "name": "", "played": True})
            
    # table cards
    table_cards = []
    rondas = max(len(env.played_cards[0]), len(env.played_cards[1]))
    for i in range(rondas):
        c_hum = get_card_name(env.played_cards[human_id][i]) if i < len(env.played_cards[human_id]) else None
        c_ai = get_card_name(env.played_cards[ai_id][i]) if i < len(env.played_cards[ai_id]) else None
        winner = None
        if i < len(env.round_winners):
            w = env.round_winners[i]
            if w == human_id: winner = "human"
            elif w == ai_id: winner = "ai"
            else: winner = "tie"
        table_cards.append({"round": i, "human_card": c_hum, "ai_card": c_ai, "winner": winner})
        
    scores = {"human": env.score[human_id], "ai": env.score[ai_id]}
    
    mask = env.get_legal_actions(human_id)
    valid_actions = [i for i, m in enumerate(mask) if m] if env.current_player == human_id and not env.is_terminal and not game.match_over else []
    
    return {
        "player_cards": player_cards,
        "table_cards": table_cards,
        "scores": scores,
        "valid_actions": valid_actions,
        "log": game.log[-15:], # last 15 logs
        "is_terminal": env.is_terminal,
        "match_over": game.match_over,
        "current_player": "human" if env.current_player == human_id else "ai",
        "pending_bet": env.pending_bet
    }

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

def run_ai_turns_if_needed(game: GameState):
    env = game.env
    while env.current_player == game.ai_id and not env.is_terminal and not game.match_over:
        state = env.get_state(game.ai_id)
        mask = env.get_legal_actions(game.ai_id)
        state_t = torch.FloatTensor(state).unsqueeze(0).to(game.device)
        mask_t = torch.BoolTensor(mask).unsqueeze(0).to(game.device)
        with torch.no_grad():
            action_t, _, _, _ = game.network.get_action_and_value(state_t, mask_t)
            action = action_t.item()
        
        action_str = get_action_string(action, env, game.ai_id)
        game.log.append(f"🤖 IA DECIDE: {action_str.upper()}")
        
        _, _, _, match_over = env.step(action)
        game.match_over = match_over

@app.post("/start")
async def start_game():
    game_state.env.reset_match()
    game_state.match_over = False
    game_state.log = ["🔥 ¡COMIENZA LA PARTIDA! 🔥"]
    
    run_ai_turns_if_needed(game_state)
    
    return JSONResponse(get_current_state_json(game_state))

@app.post("/step")
async def step(req: StepRequest):
    if game_state.match_over:
        return JSONResponse(get_current_state_json(game_state))
        
    env = game_state.env
    
    # Custom action to advance round
    if req.action_id == -1 and env.is_terminal and not game_state.match_over:
        env.reset_round()
        game_state.log.append("--- NUEVA MANO ---")
        run_ai_turns_if_needed(game_state)
        return JSONResponse(get_current_state_json(game_state))

    if env.current_player == game_state.human_id and req.action_id in range(12):
        action_str = get_action_string(req.action_id, env, game_state.human_id)
        game_state.log.append(f"👤 VOS DECIDÍS: {action_str.upper()}")
        
        _, _, _, match_over = env.step(req.action_id)
        game_state.match_over = match_over
        
        if env.is_terminal and not match_over:
            game_state.log.append("--- FIN DE LA MANO ---")
            
        run_ai_turns_if_needed(game_state)
        
        if env.is_terminal and not match_over and game_state.log[-1] != "--- FIN DE LA MANO ---":
             game_state.log.append("--- FIN DE LA MANO ---")
             
        if match_over:
             game_state.log.append("🏁 ¡PARTIDO TERMINADO! 🏁")
        
    return JSONResponse(get_current_state_json(game_state))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

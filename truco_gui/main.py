"""Punto de entrada principal para la GUI de Truco."""
import argparse
import tkinter as tk
from truco_gui.app import TrucoGUI
# Import available bots
from truco_bots.heuristic_v1 import HeuristicBotV1
from truco_bots.heuristic_v2 import HeuristicBotV2
from truco_bots.heuristic_v3 import HeuristicBotV3
from truco_bots.cfr_bot import CFRBot

def main():
    parser = argparse.ArgumentParser(description='TrucoBot GUI')
    parser.add_argument('--bot', choices=['v1', 'v2', 'v3', 'cfr'], default='v3',
                        help='Estrategia del bot (default: v3)')
    args = parser.parse_args()
    
    bot_map = {
        'v1': HeuristicBotV1,
        'v2': HeuristicBotV2,
        'v3': HeuristicBotV3,
        'cfr': CFRBot,
    }
    
    bot = bot_map[args.bot]()
    
    root = tk.Tk()
    app = TrucoGUI(root, bot=bot)
    root.mainloop()

if __name__ == '__main__':
    main()

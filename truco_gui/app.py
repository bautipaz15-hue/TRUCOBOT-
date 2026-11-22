"""Aplicación unificada de GUI para el bot de Truco."""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from truco_core.card import Card, PALOS, VALORES
from truco_core.deck import Deck
from truco_core.state import GameState


class TrucoGUI:
    """GUI Tkinter unificada que acepta cualquier bot como estrategia."""

    def __init__(self, root: tk.Tk, bot, logger=None):
        self.root = root
        self.bot = bot
        self.logger = logger

        bot_name = self.bot.__class__.__name__
        self.root.title(f"TrucoBot Argentino - {bot_name}")
        self.root.geometry("650x700")

        self._construir_interfaz()
        self._bind_hotkeys()
        self.iniciar_mano()

    def _construir_interfaz(self):
        # === 1. TANTEADOR ===
        frame_tanteador = ttk.LabelFrame(self.root, text="Tanteador a 30 (Referencia)")
        frame_tanteador.pack(fill=tk.X, padx=10, pady=5)

        inner_tanteador = ttk.Frame(frame_tanteador)
        inner_tanteador.pack(pady=5)

        ttk.Label(inner_tanteador, text="Pts Bot:").grid(row=0, column=0, padx=5)
        self.pts_bot_var = tk.IntVar(value=0)
        tk.Spinbox(inner_tanteador, from_=0, to=30, textvariable=self.pts_bot_var,
                   width=4, font=("Helvetica", 12)).grid(row=0, column=1, padx=5)

        ttk.Label(inner_tanteador, text="Pts Rival:").grid(row=0, column=2, padx=5)
        self.pts_rival_var = tk.IntVar(value=0)
        tk.Spinbox(inner_tanteador, from_=0, to=30, textvariable=self.pts_rival_var,
                   width=4, font=("Helvetica", 12)).grid(row=0, column=3, padx=5)

        self.lbl_puntos = ttk.Label(frame_tanteador, text="Bot: 0 - Rival: 0",
                                     font=("Helvetica", 14, "bold"))
        self.lbl_puntos.pack(pady=2)

        # === 2. CARTAS DEL BOT ===
        frame_cartas_bot = ttk.LabelFrame(self.root, text="Cartas del Bot (Dejar vacío para Random)")
        frame_cartas_bot.pack(fill=tk.X, padx=10, pady=5)

        self.bot_vars = []
        valores_spinbox = ('',) + tuple(VALORES)
        for i in range(3):
            val_var = tk.StringVar()
            pal_var = tk.StringVar()

            tk.Spinbox(frame_cartas_bot, values=valores_spinbox, textvariable=val_var,
                       width=5, font=("Helvetica", 11)).grid(row=0, column=i*2, padx=2, pady=5)
            ttk.Combobox(frame_cartas_bot, textvariable=pal_var, values=[""] + PALOS,
                         state="readonly", width=8).grid(row=0, column=i*2+1, padx=2, pady=5)

            self.bot_vars.append((val_var, pal_var))

        ttk.Button(frame_cartas_bot, text="Nueva Mano con estas cartas",
                   command=self.iniciar_mano).grid(row=1, column=0, columnspan=6, pady=5)

        # === 3. ACCIONES DEL RIVAL ===
        frame_rival = ttk.LabelFrame(self.root, text="Acciones del Rival (Humano)")
        frame_rival.pack(fill=tk.X, padx=10, pady=5)

        # Fila 1: Canto
        ttk.Label(frame_rival, text="Rival cantó:").grid(row=0, column=0, padx=5, pady=5)
        self.canto_rival_var = tk.StringVar(value="Nada")
        cantos_posibles = ["Nada", "Envido", "Real Envido", "Falta Envido",
                           "Truco", "Retruco", "Vale 4", "Quiero", "No Quiero"]
        self.combo_canto = ttk.Combobox(frame_rival, textvariable=self.canto_rival_var,
                                         values=cantos_posibles, state="readonly", width=15)
        self.combo_canto.grid(row=0, column=1, padx=5, pady=5)

        self.btn_registrar_canto = ttk.Button(frame_rival, text="Notificar Canto al Bot",
                                               command=self.notificar_canto_rival)
        self.btn_registrar_canto.grid(row=0, column=2, padx=5, pady=5)

        # Fila 2: Carta del rival
        ttk.Label(frame_rival, text="Rival tiró carta:").grid(row=1, column=0, padx=5, pady=5)

        self.carta_val_var = tk.StringVar()
        tk.Spinbox(frame_rival, values=valores_spinbox, textvariable=self.carta_val_var,
                   width=5, font=("Helvetica", 11)).grid(row=1, column=1, padx=5, pady=5, sticky="W")

        self.carta_pal_var = tk.StringVar()
        ttk.Combobox(frame_rival, textvariable=self.carta_pal_var, values=PALOS,
                     state="readonly", width=8).grid(row=1, column=1, padx=5, pady=5, sticky="E")

        self.btn_registrar_carta = ttk.Button(frame_rival, text="Notificar Carta",
                                               command=self.notificar_carta_rival)
        self.btn_registrar_carta.grid(row=1, column=2, padx=5, pady=5)

        # === 4. CONTROLES DEL BOT ===
        frame_bot = ttk.LabelFrame(self.root, text="Controles del Bot")
        frame_bot.pack(fill=tk.X, padx=10, pady=5)

        self.btn_iniciativa = ttk.Button(frame_bot,
                                          text="Bot: Pedir Iniciativa / Tirar Carta (Space)",
                                          command=self.pedir_iniciativa_bot)
        self.btn_iniciativa.pack(fill=tk.X, padx=50, pady=5)

        self.btn_responder = ttk.Button(frame_bot, text="Bot: Responder a Apuesta",
                                         command=self.responder_apuesta, state=tk.DISABLED)
        self.btn_responder.pack(fill=tk.X, padx=50, pady=5)

        # === 5. CONSOLA ===
        frame_consola = ttk.LabelFrame(self.root, text="Consola Integrada (Razonamientos)")
        frame_consola.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.txt_consola = tk.Text(frame_consola, state=tk.DISABLED, wrap=tk.WORD,
                                    bg="#1e1e1e", fg="#00ff00", height=8,
                                    font=("Consolas", 10))
        self.txt_consola.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # === 6. ENTRADA RÁPIDA ===
        frame_fast = ttk.LabelFrame(self.root, text="Entrada Rápida (ej: 1e, 7o, t, q, nq)")
        frame_fast.pack(fill=tk.X, padx=10, pady=5)

        self.fast_input_var = tk.StringVar()
        self.entry_fast = ttk.Entry(frame_fast, textvariable=self.fast_input_var,
                                     font=("Courier", 12))
        self.entry_fast.pack(fill=tk.X, padx=5, pady=5)

        # === 7. NUEVA MANO RANDOM ===
        ttk.Button(self.root, text="Reanudar / Nueva Mano Random",
                   command=self.iniciar_mano_random).pack(pady=5)

    def _bind_hotkeys(self):
        """Configura atajos de teclado globales."""
        self.root.bind("<space>", lambda e: self.pedir_iniciativa_bot()
                       if str(self.btn_iniciativa['state']) != 'disabled' else None)
        self.root.bind("<Escape>", lambda e: self.fast_input_var.set(""))
        self.entry_fast.bind("<Return>", self.parse_fast_input)

    def parse_fast_input(self, event):
        """Procesa la entrada rápida del teclado (Módulo A del nivel 4)."""
        cmd = self.fast_input_var.get().strip().lower()
        self.fast_input_var.set("")
        if not cmd:
            return

        dic_cantos = {
            't': 'Truco', 'r': 'Retruco', 'v': 'Vale 4',
            'e': 'Envido', 're': 'Real Envido', 'f': 'Falta Envido',
            'q': 'Quiero', 'nq': 'No Quiero', 'n': 'No Quiero'
        }

        # Caso: Canto
        if cmd in dic_cantos:
            canto = dic_cantos[cmd]
            self.canto_rival_var.set(canto)
            self.notificar_canto_rival()
            return

        # Caso: Carta (ej: 1e, 7o, 12c, 4b)
        dic_palos = {'e': 'Espadas', 'b': 'Bastos', 'o': 'Oro', 'c': 'Copa'}
        if len(cmd) >= 2:
            palo_char = cmd[-1]
            val_str = cmd[:-1]

            if palo_char in dic_palos and val_str in VALORES:
                palo_full = dic_palos[palo_char]
                self.carta_val_var.set(val_str)
                self.carta_pal_var.set(palo_full)
                self.notificar_carta_rival()
                return

        self._imprimir(f"[ERROR] Comando rápido no reconocido: '{cmd}'. Usar ej: 1e, t, q, nq.")

    def _imprimir(self, texto: str):
        """Imprime en la consola integrada."""
        self.txt_consola.config(state=tk.NORMAL)
        self.txt_consola.insert(tk.END, texto + "\n")
        self.txt_consola.see(tk.END)
        self.txt_consola.config(state=tk.DISABLED)

    def iniciar_mano_random(self):
        """Limpia los campos de cartas y reparte random."""
        for v, p in self.bot_vars:
            v.set("")
            p.set("")
        self.iniciar_mano()

    def iniciar_mano(self):
        """Inicia una nueva mano (manual o random)."""
        pts_bot = self.pts_bot_var.get()
        pts_rival = self.pts_rival_var.get()

        # Recoger cartas manuales
        cartas_manuales = []
        cartas_vistas = set()

        for v_var, p_var in self.bot_vars:
            v = v_var.get()
            p = p_var.get()
            if v and p:
                c_str = f"{v}-{p}"
                if c_str not in cartas_vistas:
                    cartas_manuales.append(Card(v, p))
                    cartas_vistas.add(c_str)

        mazo = Deck()
        mazo.mezclar()

        if len(cartas_manuales) == 3:
            cartas = tuple(cartas_manuales)
        else:
            cartas_bot_lista = mazo.repartir(3)
            cartas = tuple(cartas_bot_lista)
            for i in range(3):
                self.bot_vars[i][0].set(cartas[i].valor)
                self.bot_vars[i][1].set(cartas[i].palo)

        estado = GameState(cartas, pts_bot, pts_rival)
        self.bot.set_estado(estado)

        self._imprimir("\n" + "=" * 40)
        self._imprimir("NUEVA MANO - El bot recibe sus cartas.")
        self._imprimir(f"Mano: {cartas[0]} | {cartas[1]} | {cartas[2]}")
        self._imprimir(f"Puntos de Envido del Bot: {estado.puntos_envido_mano}")
        self._imprimir("=" * 40)

        self.lbl_puntos.config(text=f"Bot: {pts_bot} - Rival: {pts_rival}")
        self.btn_iniciativa.config(state=tk.NORMAL)
        self.btn_registrar_carta.config(state=tk.NORMAL)
        self.btn_registrar_canto.config(state=tk.NORMAL)
        self.btn_responder.config(state=tk.DISABLED)
        self.entry_fast.focus_set()

    def notificar_canto_rival(self):
        """Procesa el canto del rival."""
        canto = self.canto_rival_var.get()
        if canto == "Nada":
            return

        estado = self.bot.estado_mano

        # Quiero / No Quiero son respuestas, no cantos
        if canto in ["Quiero", "No Quiero"]:
            self._imprimir(f"[RIVAL] Responde: {canto}")
            if canto == "No Quiero":
                self._imprimir(">>> EL RIVAL SE FUE AL MAZO. GANAMOS LA MANO. <<<")

            self.canto_rival_var.set("Nada")
            self.btn_iniciativa.config(state=tk.NORMAL)
            self.btn_registrar_carta.config(state=tk.NORMAL)
            self.btn_registrar_canto.config(state=tk.NORMAL)
            self.btn_responder.config(state=tk.DISABLED)
            return

        self._imprimir(f"[RIVAL] Canta: {canto}")

        # Desactivar botones mientras el bot decide
        self.btn_iniciativa.config(state=tk.DISABLED)
        self.btn_registrar_carta.config(state=tk.DISABLED)
        self.btn_registrar_canto.config(state=tk.DISABLED)
        self.btn_responder.config(state=tk.NORMAL)

        # Actualizar estado según el canto
        if canto in ["Envido", "Real Envido", "Falta Envido"]:
            estado.fase_actual = "envido_disponible"
            if canto == "Envido":
                estado.estado_envido = max(estado.estado_envido, 1)
            elif canto == "Real Envido":
                estado.estado_envido = max(estado.estado_envido, 2)
            elif canto == "Falta Envido":
                estado.estado_envido = max(estado.estado_envido, 3)
        elif canto in ["Truco", "Retruco", "Vale 4"]:
            if canto == "Truco":
                estado.estado_truco = 1
            elif canto == "Retruco":
                estado.estado_truco = 2
            elif canto == "Vale 4":
                estado.estado_truco = 3
            estado.turno_apuesta_truco = "bot"

    def responder_apuesta(self):
        """El bot responde a la apuesta del rival."""
        estado = self.bot.estado_mano
        canto = self.canto_rival_var.get()

        if canto in ["Envido", "Real Envido", "Falta Envido"]:
            tipo = "envido"
            nivel = estado.estado_envido
            estado.fase_actual = "juego_cartas"
        else:
            tipo = "truco"
            nivel = estado.estado_truco

        respuesta = self.bot.responder_apuesta(tipo, nivel)
        self._imprimir(f"[BOT] Responde a {canto}: {respuesta}")

        self.canto_rival_var.set("Nada")

        if "Retruco" in respuesta:
            estado.estado_truco = 2
            estado.turno_apuesta_truco = "rival"
            self._imprimir("[SISTEMA] Bot ha cantado Retruco. Esperando respuesta del humano.")
        elif "Vale 4" in respuesta:
            estado.estado_truco = 3
            estado.turno_apuesta_truco = "rival"
            self._imprimir("[SISTEMA] Bot ha cantado Vale 4. Esperando respuesta del humano.")
        else:
            self.btn_responder.config(state=tk.DISABLED)
            self.btn_iniciativa.config(state=tk.NORMAL)
            self.btn_registrar_carta.config(state=tk.NORMAL)
            self.btn_registrar_canto.config(state=tk.NORMAL)

        self.entry_fast.focus_set()

    def notificar_carta_rival(self):
        """Registra una carta jugada por el rival."""
        val = self.carta_val_var.get()
        pal = self.carta_pal_var.get()
        if not val or not pal:
            return

        carta = Card(val, pal)
        self.bot.registrar_carta_rival(carta)
        self._imprimir(f"[RIVAL] Juega carta: {carta}")

        ganador = self.bot.evaluar_ganador_ronda()
        if ganador:
            self._imprimir(f">>> Fin de la ronda. Ganador: {ganador.upper()} <<<")

        self.entry_fast.focus_set()

    def pedir_iniciativa_bot(self):
        """Pide al bot que tome la iniciativa (cantar o jugar carta)."""
        canto, carta = self.bot.evaluar_iniciativa()
        estado = self.bot.estado_mano

        if not canto and not carta:
            self._imprimir("[BOT] Ya no me quedan cartas para jugar.")
            return

        acciones = []
        if canto:
            acciones.append(f"Canto {canto}")
            if canto in ["ENVIDO", "REAL ENVIDO", "FALTA ENVIDO"]:
                estado.fase_actual = "juego_cartas"
                if canto == "ENVIDO":
                    estado.estado_envido = 1
                elif canto == "REAL ENVIDO":
                    estado.estado_envido = 2
                elif canto == "FALTA ENVIDO":
                    estado.estado_envido = 3

            if canto in ["TRUCO", "RETRUCO", "VALE 4"]:
                estado.turno_apuesta_truco = "rival"
                if canto == "TRUCO":
                    estado.estado_truco = 1
                elif canto == "RETRUCO":
                    estado.estado_truco = 2
                elif canto == "VALE 4":
                    estado.estado_truco = 3

        if carta:
            acciones.append(f"Juego el {carta}")
            self.bot.jugar_carta(carta)

        self._imprimir(f"[BOT] {', luego '.join(acciones)}")

        if canto:
            self._imprimir("[SISTEMA] Selecciona 'Quiero' o 'No Quiero' (ej: 'q' o 'nq' en entrada rápida).")

        ganador = self.bot.evaluar_ganador_ronda()
        if ganador:
            self._imprimir(f">>> Fin de la ronda. Ganador: {ganador.upper()} <<<")

        self.entry_fast.focus_set()

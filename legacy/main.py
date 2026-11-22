import tkinter as tk
from tkinter import ttk
import random
import logging
from typing import List, Tuple, Optional

from cfr_engine import CFR_Engine, generar_infoset

# ==========================================
# Paso 1: Estructura de Datos y Core Lógico
# ==========================================

JERARQUIA_TRUCO = {
    '1 Espadas': 14,
    '1 Bastos': 13,
    '7 Espadas': 12,
    '7 Oro': 11,
    '3': 10,
    '2': 9,
    '1 Copa': 8,
    '1 Oro': 8,
    '12': 7,
    '11': 6,
    '10': 5,
    '7 Copa': 4,
    '7 Bastos': 4,
    '6': 3,
    '5': 2,
    '4': 1
}

PALOS = ['Espadas', 'Bastos', 'Oro', 'Copa']
VALORES = ['1', '2', '3', '4', '5', '6', '7', '10', '11', '12']

class Carta:
    def __init__(self, valor: str, palo: str):
        self.valor = valor
        self.palo = palo
        
    def obtener_nombre(self) -> str:
        if self.valor == '1' and self.palo in ['Espadas', 'Bastos']:
            return f"{self.valor} {self.palo}"
        if self.valor == '7' and self.palo in ['Espadas', 'Oro']:
            return f"{self.valor} {self.palo}"
        if self.valor == '1' and self.palo in ['Copa', 'Oro']:
            return f"{self.valor} {self.palo}"
        if self.valor == '7' and self.palo in ['Copa', 'Bastos']:
            return f"{self.valor} {self.palo}"
        return self.valor
        
    def obtener_jerarquia(self) -> int:
        return JERARQUIA_TRUCO[self.obtener_nombre()]

    def valor_envido(self) -> int:
        v = int(self.valor)
        if v >= 10:
            return 0
        return v
        
    def __str__(self) -> str:
        return f"{self.valor} de {self.palo}"
        
    def __repr__(self) -> str:
        return self.__str__()
        
    def __eq__(self, other) -> bool:
        if isinstance(other, Carta):
            return self.valor == other.valor and self.palo == other.palo
        return False

def calcular_envido(cartas: Tuple[Carta, Carta, Carta]) -> int:
    palos_dict = {}
    for c in cartas:
        palos_dict.setdefault(c.palo, []).append(c.valor_envido())
    
    max_envido = 0
    for _, vals in palos_dict.items():
        if len(vals) >= 2:
            vals.sort(reverse=True)
            envido = 20 + vals[0] + vals[1]
            if envido > max_envido:
                max_envido = envido
        elif len(vals) == 1:
            if vals[0] > max_envido:
                max_envido = vals[0]
                
    return max_envido

class Mazo:
    def __init__(self):
        self.cartas = [Carta(v, p) for v in VALORES for p in PALOS]
        random.shuffle(self.cartas)
        
    def repartir(self, cantidad: int) -> List[Carta]:
        return [self.cartas.pop() for _ in range(cantidad)]

class EstadoMano:
    def __init__(self, cartas_iniciales: Tuple[Carta, Carta, Carta], puntos_bot: int = 0, puntos_rival: int = 0):
        self.cartas_iniciales = cartas_iniciales 
        self.cartas_restantes = list(cartas_iniciales)
        self.puntos_bot = puntos_bot
        self.puntos_rival = puntos_rival
        
        self.estado_envido = 0  
        self.estado_truco = 0   
        self.turno_apuesta_truco = "bot" 
        self.fase_actual = "envido_disponible" 
        self.bot_canto_envido_nivel = 0
        
        self.cartas_en_mesa: List[Tuple[str, Carta]] = [] 
        self.resultados_rondas: List[str] = [] 
        
        self.puntos_envido_mano = calcular_envido(self.cartas_iniciales)

class LoggerMano:
    def __init__(self, filename="debug_nivel4.log"):
        self.logger = logging.getLogger("TrucoBotNivel4")
        self.logger.setLevel(logging.DEBUG)
        
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
            
        fh = logging.FileHandler(filename)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
    def log_cartas_iniciales(self, cartas: Tuple[Carta, Carta, Carta]):
        self.logger.debug(f"[CARTAS INICIALES] {cartas}")
        
    def log_estado(self, mensaje: str):
        self.logger.debug(f"[ESTADO] {mensaje}")
        
    def log_iniciativa(self, evaluacion: str, decision: str):
        self.logger.debug(f"[INICIATIVA] {evaluacion} -> DECISIÓN: {decision}")

# ==========================================
# Paso 2 y 3: La Máquina de Estados y Gestión de Mesa (Módulo B)
# ==========================================

class BotTruco:
    def __init__(self, logger: LoggerMano):
        self.logger = logger
        self.estado_mano: Optional[EstadoMano] = None
        self.cfr = CFR_Engine() # Inicializa con perfil vacío para fallback
        
    def set_estado(self, estado: EstadoMano):
        self.estado_mano = estado
        self.logger.log_cartas_iniciales(estado.cartas_iniciales)
        self.logger.log_estado(
            f"Nueva mano. Envido bot: {estado.puntos_envido_mano}. "
            f"Tanteador Bot: {estado.puntos_bot} - Rival: {estado.puntos_rival}"
        )

    def _calcular_probabilidad_victoria(self) -> float:
        if not self.estado_mano.cartas_restantes:
            return 0.0
            
        poderes = [c.obtener_jerarquia() for c in self.estado_mano.cartas_restantes]
        
        if len(poderes) == 3:
            if max(poderes) >= 12: return 0.85
            elif max(poderes) >= 10: 
                return 0.70 if sum(poderes) > 20 else 0.5
            return 0.3
        elif len(poderes) == 2:
            if max(poderes) >= 12: return 0.9
            if max(poderes) >= 9: return 0.7
            return 0.4
        else:
            if max(poderes) >= 12: return 0.9
            if max(poderes) >= 10: return 0.8
            return 0.5

    def _buscar_carta_por_shortname(self, short_name: str) -> Carta:
        for c in self.estado_mano.cartas_restantes:
            if short_name == f"{c.valor}{c.palo[0]}":
                return c
        return self.estado_mano.cartas_restantes[0]

    def evaluar_iniciativa(self) -> Tuple[Optional[str], Optional[Carta]]:
        estado = self.estado_mano
        
        if not estado.cartas_restantes:
            return None, None
            
        infoset = generar_infoset(estado)
        accion_cfr = self.cfr.get_action(infoset)
        
        if accion_cfr:
            self.logger.log_estado(f"CFR InfoSet encontrado: {infoset} -> Acción: {accion_cfr}")
            if accion_cfr.startswith("JUGAR_"):
                carta_str = accion_cfr.split("_")[1]
                carta = self._buscar_carta_por_shortname(carta_str)
                return None, carta
            elif accion_cfr.startswith("CANTAR_"):
                canto = accion_cfr.split("_")[1].replace("-", " ")
                return canto, None

        self.logger.log_estado(f"CFR InfoSet NO encontrado: {infoset}. Ejecutando Fallback Heurístico.")
        
        prob = self._calcular_probabilidad_victoria()
        evaluacion = f"Probabilidad victoria: {prob:.2f}. Fase: {estado.fase_actual}"
        
        # 1. Proactividad: Evaluar Envido
        if estado.fase_actual == "envido_disponible" and estado.estado_envido == 0:
            if estado.puntos_envido_mano >= 30:
                decision = "REAL ENVIDO"
                estado.bot_canto_envido_nivel = 2
                self.logger.log_iniciativa(f"Envido alto ({estado.puntos_envido_mano})", decision)
                return decision, None
            elif estado.puntos_envido_mano >= 27:
                decision = "ENVIDO"
                estado.bot_canto_envido_nivel = 1
                self.logger.log_iniciativa(f"Envido medio ({estado.puntos_envido_mano})", decision)
                return decision, None
                
        # 2. Proactividad: Evaluar Truco
        if estado.estado_truco == 0:
            gano_ronda_1 = len(estado.resultados_rondas) > 0 and estado.resultados_rondas[-1] == "bot"
            if prob > 0.80:
                decision = "TRUCO"
                self.logger.log_iniciativa(evaluacion, decision)
                return decision, None
            elif gano_ronda_1 and prob < 0.40 and random.random() < 0.20:
                decision = "TRUCO"
                self.logger.log_iniciativa("FAROL ACTIVADO", decision)
                return decision, None
                
        elif estado.estado_truco == 1 and estado.turno_apuesta_truco == "bot":
            if max([c.obtener_jerarquia() for c in estado.cartas_restantes]) >= 12:
                decision = "RETRUCO"
                self.logger.log_iniciativa("Tengo carta brava", decision)
                return decision, None

        # 3. Jugar Carta
        carta_a_jugar = None
        if not estado.cartas_en_mesa:
            estado.cartas_restantes.sort(key=lambda c: c.obtener_jerarquia())
            poderes = [c.obtener_jerarquia() for c in estado.cartas_restantes]
            max_poder = max(poderes) if poderes else 0
            
            if max_poder >= 9:
                if max_poder < 13: 
                    carta_a_jugar = estado.cartas_restantes[-1]
                    decision = f"Apertura fuerte, juego carta más alta: {carta_a_jugar}"
                else: 
                    if len(estado.cartas_restantes) >= 2:
                        segunda_mejor = poderes[-2]
                        if segunda_mejor < 6:
                            carta_a_jugar = estado.cartas_restantes[-1]
                            decision = f"Ancho Bravo sin cobertura (cartas < 6), aseguro primera ronda: {carta_a_jugar}"
                        else:
                            carta_a_jugar = estado.cartas_restantes[-2]
                            decision = f"Tiendo trampa con Ancho Bravo y cobertura, juego segunda carta: {carta_a_jugar}"
                    else:
                        carta_a_jugar = estado.cartas_restantes[-1]
                        decision = f"Solo queda una carta, juego: {carta_a_jugar}"
            else:
                carta_a_jugar = estado.cartas_restantes[0]
                decision = f"Mano baja, juego carta más baja: {carta_a_jugar}"
        else:
            rival_carta = estado.cartas_en_mesa[0][1]
            rival_poder = rival_carta.obtener_jerarquia()
            
            superadoras = [c for c in estado.cartas_restantes if c.obtener_jerarquia() > rival_poder]
            if superadoras:
                superadoras.sort(key=lambda c: c.obtener_jerarquia())
                carta_a_jugar = superadoras[0]
                decision = f"Juego {carta_a_jugar} superando {rival_carta}"
            else:
                estado.cartas_restantes.sort(key=lambda c: c.obtener_jerarquia())
                carta_a_jugar = estado.cartas_restantes[0]
                decision = f"Juego {carta_a_jugar} entregando ronda ante {rival_carta}"
                
        self.logger.log_iniciativa("No canto nada, procedo a jugar carta", decision)
        return None, carta_a_jugar

    def responder_apuesta(self, tipo_apuesta: str, nivel_apuesta: int) -> str:
        estado = self.estado_mano
        
        infoset = generar_infoset(estado)
        accion_cfr = self.cfr.get_action(infoset)
        if accion_cfr and accion_cfr.startswith("RESPONDER_"):
            respuesta = accion_cfr.split("_")[1].replace("-", " ")
            self.logger.log_estado(f"CFR responde a apuesta: {respuesta}")
            return respuesta
            
        self.logger.log_estado(f"CFR InfoSet NO encontrado: {infoset}. Fallback Heurístico para respuesta.")
        
        if tipo_apuesta == "envido":
            pts = estado.puntos_envido_mano
            if nivel_apuesta == 1:
                resp = "Quiero" if pts >= 26 else "No Quiero"
            elif nivel_apuesta == 2: 
                resp = "Quiero" if pts >= 28 else "No Quiero"
            elif nivel_apuesta == 3: 
                puntos_propios = estado.puntos_bot
                faltan_rival = 30 - estado.puntos_rival
                
                if estado.bot_canto_envido_nivel >= 2 and pts >= 30:
                    resp = "Quiero"
                elif puntos_propios < 10:
                    resp = "Quiero" if pts >= 28 else "No Quiero"
                elif puntos_propios < 20:
                    resp = "Quiero" if pts >= 29 else "No Quiero"
                else:
                    if pts >= 31 or faltan_rival <= 3:
                        resp = "Quiero"
                    else:
                        resp = "No Quiero"
            else:
                resp = "No Quiero"
            self.logger.log_estado(f"Rival canta {tipo_apuesta} nivel {nivel_apuesta}. Bot responde: {resp} (Puntos: {pts})")
            return resp
            
        elif tipo_apuesta == "truco":
            poderes = [c.obtener_jerarquia() for c in estado.cartas_restantes]
            max_poder = max(poderes) if poderes else 0
            prob_victoria = self._calcular_probabilidad_victoria()
            
            if nivel_apuesta == 1: 
                if prob_victoria >= 0.80:
                    resp = "Quiero y Retruco"
                else:
                    resp = "Quiero" if max_poder >= 10 and len(poderes) >= 2 else "No Quiero"
            elif nivel_apuesta == 2: 
                if max_poder >= 13:
                    resp = "Quiero y Vale 4"
                else:
                    resp = "Quiero" if max_poder >= 12 else "No Quiero"
            elif nivel_apuesta == 3: 
                resp = "Quiero" if max_poder >= 13 else "No Quiero"
            else:
                resp = "No Quiero"
            self.logger.log_estado(f"Rival canta {tipo_apuesta} nivel {nivel_apuesta}. Bot responde: {resp}")
            return resp
        
        return "No Quiero"

    def jugar_carta(self, carta: Carta):
        self.estado_mano.cartas_restantes.remove(carta)
        self.estado_mano.cartas_en_mesa.append(("bot", carta))
        self.estado_mano.fase_actual = "juego_cartas" 
        self.logger.log_estado(f"Bot jugó {carta}")

    def registrar_carta_rival(self, carta: Carta):
        self.estado_mano.cartas_en_mesa.append(("rival", carta))
        self.estado_mano.fase_actual = "juego_cartas" 
        self.logger.log_estado(f"Rival jugó {carta}")
        
    def evaluar_ganador_ronda(self) -> Optional[str]:
        if len(self.estado_mano.cartas_en_mesa) == 2:
            jugador1, carta1 = self.estado_mano.cartas_en_mesa[0]
            jugador2, carta2 = self.estado_mano.cartas_en_mesa[1]
            
            p1 = carta1.obtener_jerarquia()
            p2 = carta2.obtener_jerarquia()
            
            if p1 > p2:
                ganador = jugador1
            elif p2 > p1:
                ganador = jugador2
            else:
                ganador = "parda"
                
            self.estado_mano.resultados_rondas.append(ganador)
            self.logger.log_estado(f"Fin de ronda. Mesa: {carta1} vs {carta2}. Ganador: {ganador}")
            
            self.estado_mano.cartas_en_mesa = []
            return ganador
        return None

# ==========================================
# Paso 4: Implementación de la Interfaz con Módulo A
# ==========================================

class AppTrucoGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("TrucoBot Argentino - Nivel 4 (CFR)")
        self.root.geometry("600x650")
        
        self.logger = LoggerMano()
        self.bot = BotTruco(self.logger)
        
        self._construir_interfaz()
        self._bind_hotkeys()
        self.iniciar_mano()
        
    def _construir_interfaz(self):
        frame_tanteador = ttk.LabelFrame(self.root, text="Tanteador a 30 (Referencia)")
        frame_tanteador.pack(fill=tk.X, padx=10, pady=5)
        
        self.lbl_puntos = ttk.Label(frame_tanteador, text="Bot: 0 - Rival: 0", font=("Helvetica", 14, "bold"))
        self.lbl_puntos.pack(pady=5)
        
        frame_cartas_bot = ttk.LabelFrame(self.root, text="Cartas del Bot (Dejar vacío para Random)")
        frame_cartas_bot.pack(fill=tk.X, padx=10, pady=5)
        
        self.bot_vars = []
        for i in range(3):
            val_var = tk.StringVar()
            pal_var = tk.StringVar()
            
            ttk.Combobox(frame_cartas_bot, textvariable=val_var, values=[""] + VALORES, state="readonly", width=4).grid(row=0, column=i*2, padx=2, pady=5)
            ttk.Combobox(frame_cartas_bot, textvariable=pal_var, values=[""] + PALOS, state="readonly", width=8).grid(row=0, column=i*2+1, padx=2, pady=5)
            
            self.bot_vars.append((val_var, pal_var))
            
        ttk.Button(frame_cartas_bot, text="Nueva Mano con estas cartas", command=self.iniciar_mano).grid(row=1, column=0, columnspan=6, pady=5)
        
        frame_rival = ttk.LabelFrame(self.root, text="Acciones del Rival (Humano)")
        frame_rival.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame_rival, text="Rival cantó:").grid(row=0, column=0, padx=5, pady=5)
        self.canto_rival_var = tk.StringVar(value="Nada")
        cantos_posibles = ["Nada", "Envido", "Real Envido", "Falta Envido", "Truco", "Retruco", "Vale 4", "Quiero", "No Quiero"]
        self.combo_canto = ttk.Combobox(frame_rival, textvariable=self.canto_rival_var, values=cantos_posibles, state="readonly", width=15)
        self.combo_canto.grid(row=0, column=1, padx=5, pady=5)
        
        self.btn_registrar_canto = ttk.Button(frame_rival, text="Notificar Canto al Bot", command=self.notificar_canto_rival)
        self.btn_registrar_canto.grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(frame_rival, text="Rival tiró carta:").grid(row=1, column=0, padx=5, pady=5)
        
        self.carta_val_var = tk.StringVar()
        self.combo_val = ttk.Combobox(frame_rival, textvariable=self.carta_val_var, values=VALORES, state="readonly", width=5)
        self.combo_val.grid(row=1, column=1, padx=5, pady=5, sticky="W")
        
        self.carta_pal_var = tk.StringVar()
        self.combo_pal = ttk.Combobox(frame_rival, textvariable=self.carta_pal_var, values=PALOS, state="readonly", width=8)
        self.combo_pal.grid(row=1, column=1, padx=5, pady=5, sticky="E")
        
        self.btn_registrar_carta = ttk.Button(frame_rival, text="Notificar Carta", command=self.notificar_carta_rival)
        self.btn_registrar_carta.grid(row=1, column=2, padx=5, pady=5)
        
        frame_bot = ttk.LabelFrame(self.root, text="Controles del Bot")
        frame_bot.pack(fill=tk.X, padx=10, pady=5)
        
        self.btn_iniciativa = ttk.Button(frame_bot, text="Bot: Pedir Iniciativa / Tirar Carta (Space)", command=self.pedir_iniciativa_bot)
        self.btn_iniciativa.pack(fill=tk.X, padx=50, pady=5)
        
        self.btn_responder = ttk.Button(frame_bot, text="Bot: Responder a Apuesta", command=self.responder_apuesta, state=tk.DISABLED)
        self.btn_responder.pack(fill=tk.X, padx=50, pady=5)
        
        frame_consola = ttk.LabelFrame(self.root, text="Consola Integrada (Razonamientos)")
        frame_consola.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.txt_consola = tk.Text(frame_consola, state=tk.DISABLED, wrap=tk.WORD, bg="#1e1e1e", fg="#00ff00", height=8)
        self.txt_consola.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- MÓDULO A: Consola de Entrada Rápida ---
        frame_fast = ttk.LabelFrame(self.root, text="Entrada Rápida (Módulo A)")
        frame_fast.pack(fill=tk.X, padx=10, pady=5)
        
        self.fast_input_var = tk.StringVar()
        self.entry_fast = ttk.Entry(frame_fast, textvariable=self.fast_input_var, font=("Courier", 12))
        self.entry_fast.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(self.root, text="Reanudar / Nueva Mano Random", command=self.iniciar_mano_random).pack(pady=5)
        
    def _bind_hotkeys(self):
        # Módulo A: Global Hotkeys
        self.root.bind("<space>", lambda e: self.pedir_iniciativa_bot() if self.btn_iniciativa['state'] == tk.NORMAL else None)
        self.root.bind("<Escape>", lambda e: self.fast_input_var.set(""))
        self.entry_fast.bind("<Return>", self.parse_fast_input)
        
    def parse_fast_input(self, event):
        cmd = self.fast_input_var.get().strip().lower()
        self.fast_input_var.set("")
        if not cmd: return
        
        dic_cantos = {
            't': 'Truco', 'r': 'Retruco', 'v': 'Vale 4',
            'e': 'Envido', 're': 'Real Envido', 'f': 'Falta Envido',
            'q': 'Quiero', 'nq': 'No Quiero', 'n': 'No Quiero'
        }
        
        # Caso Canto
        if cmd in dic_cantos:
            canto = dic_cantos[cmd]
            self.canto_rival_var.set(canto)
            self.notificar_canto_rival()
            return
            
        # Caso Carta (ej: 1e, 7o, 12c, 4b)
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
        self.txt_consola.config(state=tk.NORMAL)
        self.txt_consola.insert(tk.END, texto + "\n")
        self.txt_consola.see(tk.END)
        self.txt_consola.config(state=tk.DISABLED)
        
    def iniciar_mano_random(self):
        for v, p in self.bot_vars:
            v.set("")
            p.set("")
        self.iniciar_mano()
        
    def iniciar_mano(self):
        pts_bot = 0
        pts_rival = 0
        if self.bot.estado_mano:
            pts_bot = self.bot.estado_mano.puntos_bot
            pts_rival = self.bot.estado_mano.puntos_rival
            
        cartas_manuales = []
        cartas_vistas = set()
        
        for v_var, p_var in self.bot_vars:
            v = v_var.get()
            p = p_var.get()
            if v and p:
                c_str = f"{v}-{p}"
                if c_str not in cartas_vistas:
                    cartas_manuales.append(Carta(v, p))
                    cartas_vistas.add(c_str)

        mazo = Mazo() 
        
        if len(cartas_manuales) == 3:
            cartas = (cartas_manuales[0], cartas_manuales[1], cartas_manuales[2])
        else:
            cartas_bot_lista = mazo.repartir(3)
            cartas = (cartas_bot_lista[0], cartas_bot_lista[1], cartas_bot_lista[2])
            for i in range(3):
                self.bot_vars[i][0].set(cartas[i].valor)
                self.bot_vars[i][1].set(cartas[i].palo)
        
        estado = EstadoMano(cartas, pts_bot, pts_rival)
        self.bot.set_estado(estado)
        
        self._imprimir("\n" + "="*40)
        self._imprimir(f"NUEVA MANO - El bot recibe sus cartas.")
        self._imprimir(f"Mano Oculta: {cartas[0]} | {cartas[1]} | {cartas[2]}")
        self._imprimir(f"Puntos de Envido del Bot: {estado.puntos_envido_mano}")
        self._imprimir(f"InfoSet Inicial: {generar_infoset(estado)}")
        self._imprimir("="*40)
        
        self.btn_iniciativa.config(state=tk.NORMAL)
        self.btn_registrar_carta.config(state=tk.NORMAL)
        self.btn_registrar_canto.config(state=tk.NORMAL)
        self.btn_responder.config(state=tk.DISABLED)
        self.entry_fast.focus_set()
        
    def notificar_canto_rival(self):
        canto = self.canto_rival_var.get()
        if canto == "Nada": return
            
        estado = self.bot.estado_mano
        
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
        
        self.btn_iniciativa.config(state=tk.DISABLED)
        self.btn_registrar_carta.config(state=tk.DISABLED)
        self.btn_registrar_canto.config(state=tk.DISABLED)
        self.btn_responder.config(state=tk.NORMAL)
        
        if canto in ["Envido", "Real Envido", "Falta Envido"]:
            estado.fase_actual = "envido_disponible"
            if canto == "Envido": estado.estado_envido = max(estado.estado_envido, 1)
            elif canto == "Real Envido": estado.estado_envido = max(estado.estado_envido, 2)
            elif canto == "Falta Envido": estado.estado_envido = max(estado.estado_envido, 3)
        elif canto in ["Truco", "Retruco", "Vale 4"]:
            if canto == "Truco": estado.estado_truco = 1
            elif canto == "Retruco": estado.estado_truco = 2
            elif canto == "Vale 4": estado.estado_truco = 3
            estado.turno_apuesta_truco = "bot"

    def responder_apuesta(self):
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
        val = self.carta_val_var.get()
        pal = self.carta_pal_var.get()
        if not val or not pal: return
            
        carta = Carta(val, pal)
        self.bot.registrar_carta_rival(carta)
        self._imprimir(f"[RIVAL] Juega carta: {carta}")
        
        ganador = self.bot.evaluar_ganador_ronda()
        if ganador:
            self._imprimir(f">>> Fin de la ronda. Ganador: {ganador.upper()} <<<")
            
        self.entry_fast.focus_set()
            
    def pedir_iniciativa_bot(self):
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
                if canto == "ENVIDO": estado.estado_envido = 1
                elif canto == "REAL ENVIDO": estado.estado_envido = 2
                elif canto == "FALTA ENVIDO": estado.estado_envido = 3
                
            if canto in ["TRUCO", "RETRUCO", "VALE 4"]:
                estado.turno_apuesta_truco = "rival"
                if canto == "TRUCO": estado.estado_truco = 1
                elif canto == "RETRUCO": estado.estado_truco = 2
                elif canto == "VALE 4": estado.estado_truco = 3
                
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

if __name__ == "__main__":
    root = tk.Tk()
    app = AppTrucoGUI(root)
    root.mainloop()

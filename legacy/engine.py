import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import os

class LoggerMano:
    def __init__(self):
        self.archivo_log = "debug_nivel2.log"
        self.reset()

    def reset(self):
        self.mano_actual = {
            "timestamp": None,
            "tanteador_inicio": {"bot": 0, "rival": 0},
            "cartas_iniciales": [],
            "evaluaciones_internas": [],
            "fase_envido": [],
            "fase_truco": [],
            "cartas_jugadas": {"ronda_1": [], "ronda_2": [], "ronda_3": []}
        }

    def iniciar_mano(self, pts_bot, pts_rival, cartas):
        self.mano_actual["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.mano_actual["tanteador_inicio"] = {"bot": pts_bot, "rival": pts_rival}
        self.mano_actual["cartas_iniciales"] = [str(c) for c in cartas]

    def registrar_evento(self, categoria, detalle):
        """
        Categorías válidas: 'envido', 'truco', 'evaluacion', 'ronda_1', 'ronda_2', 'ronda_3'
        """
        if categoria in self.mano_actual["cartas_jugadas"]:
            self.mano_actual["cartas_jugadas"][categoria].append(detalle)
        elif categoria == "envido":
            self.mano_actual["fase_envido"].append(detalle)
        elif categoria == "truco":
            self.mano_actual["fase_truco"].append(detalle)
        elif categoria == "evaluacion":
            self.mano_actual["evaluaciones_internas"].append(detalle)

    def guardar_y_cerrar_mano(self, pts_bot_fin, pts_rival_fin):
        if not self.mano_actual["timestamp"]:
            return # Evita guardar si no se había iniciado una mano
        
        with open(self.archivo_log, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"MANO INICIADA: {self.mano_actual['timestamp']}\n")
            f.write(f"TANTEADOR INICIO -> Bot: {self.mano_actual['tanteador_inicio']['bot']} | Rival: {self.mano_actual['tanteador_inicio']['rival']}\n")
            f.write(f"CARTAS DEL BOT   -> {', '.join(self.mano_actual['cartas_iniciales'])}\n")
            f.write(f"{'-'*60}\n")
            
            f.write("--- CÁLCULOS Y EVALUACIONES INTERNAS ---\n")
            for ev in self.mano_actual["evaluaciones_internas"]: 
                f.write(f"  [>] {ev}\n")
            
            f.write("\n--- DESARROLLO DE ENVIDO ---\n")
            for env in self.mano_actual["fase_envido"]: 
                f.write(f"  * {env}\n")
            
            f.write("\n--- DESARROLLO DE TRUCO ---\n")
            for tr in self.mano_actual["fase_truco"]: 
                f.write(f"  * {tr}\n")
            
            f.write("\n--- DESARROLLO DE CARTAS ---\n")
            for r in ["ronda_1", "ronda_2", "ronda_3"]:
                if self.mano_actual["cartas_jugadas"][r]:
                    f.write(f"  [{r.upper()}]: {' -> '.join(self.mano_actual['cartas_jugadas'][r])}\n")
            
            f.write(f"{'-'*60}\n")
            f.write(f"TANTEADOR FIN MANO -> Bot: {pts_bot_fin} | Rival: {pts_rival_fin}\n")
            f.write(f"{'='*60}\n")
        
        self.reset()


# Diccionario de jerarquía del Truco
JERARQUIA_TRUCO = {
    (1, 'espadas'): 14, (1, 'bastos'): 13, (7, 'espadas'): 12, (7, 'oros'): 11,
    (3, 'espadas'): 10, (3, 'bastos'): 10, (3, 'oros'): 10, (3, 'copas'): 10,
    (2, 'espadas'): 9,  (2, 'bastos'): 9,  (2, 'oros'): 9,  (2, 'copas'): 9,
    (1, 'oros'): 8,     (1, 'copas'): 8,
    (12, 'espadas'): 7, (12, 'bastos'): 7, (12, 'oros'): 7, (12, 'copas'): 7,
    (11, 'espadas'): 6, (11, 'bastos'): 6, (11, 'oros'): 6, (11, 'copas'): 6,
    (10, 'espadas'): 5, (10, 'bastos'): 5, (10, 'oros'): 5, (10, 'copas'): 5,
    (7, 'bastos'): 4,   (7, 'copas'): 4,
    (6, 'espadas'): 3,  (6, 'bastos'): 3,  (6, 'oros'): 3,  (6, 'copas'): 3,
    (5, 'espadas'): 2,  (5, 'bastos'): 2,  (5, 'oros'): 2,  (5, 'copas'): 2,
    (4, 'espadas'): 1,  (4, 'bastos'): 1,  (4, 'oros'): 1,  (4, 'copas'): 1,
}

PALOS_VALIDOS = ["espadas", "bastos", "oros", "copas"]
NUMEROS_VALIDOS = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]

class Carta:
    def __init__(self, numero, palo):
        self.numero = int(numero)
        self.palo = palo.lower()
        self.poder_truco = JERARQUIA_TRUCO.get((self.numero, self.palo), 0)
        self.valor_envido = self.numero if self.numero < 10 else 0

    def __str__(self):
        return f"{self.numero} de {self.palo.capitalize()}"

class AsistenteBot:
    def __init__(self):
        self.mano = []
        self.puntos_propios = 0
        self.puntos_rival = 0
        self.objetivo = 30
        
        self.es_mano = False
        self.ronda_actual = 1
        self.resultados_rondas = []
        
        self.cartas_jugadas_bot = []
        self.cartas_jugadas_rival = []
        self.cartas_restantes_mazo = 34 
        self.cartas_vistas = []

    def set_mano(self, cartas):
        self.mano = cartas
        self.cartas_jugadas_bot = []
        self.cartas_jugadas_rival = []
        self.resultados_rondas = []
        self.ronda_actual = 1
        self.cartas_vistas = list(cartas)

    def actualizar_tanteador(self, puntos_propios, puntos_rival):
        self.puntos_propios = puntos_propios
        self.puntos_rival = puntos_rival

    def registrar_accion_rival(self, tipo_accion, carta=None):
        if tipo_accion == 'carta' and carta:
            self.cartas_jugadas_rival.append(carta)
            self.cartas_vistas.append(carta)
        elif tipo_accion == 'envido':
            pass

    def calcular_envido(self):
        if not self.mano: return 0
        palos = {}
        for carta in self.mano:
            if carta.palo not in palos: palos[carta.palo] = []
            palos[carta.palo].append(carta.valor_envido)
        
        max_envido = 0
        for palo, valores in palos.items():
            if len(valores) >= 2:
                valores.sort(reverse=True)
                envido = 20 + valores[0] + valores[1]
            else:
                envido = valores[0]
            if envido > max_envido: max_envido = envido
        return max_envido

    def evaluar_riesgo_envido(self, puntos_mano=None, tanteador=None):
        if puntos_mano is None:
            puntos_mano = self.calcular_envido()
            
        diferencia = self.puntos_rival - self.puntos_propios
        faltan_rival = self.objetivo - self.puntos_rival
        
        if faltan_rival <= 2:
            return puntos_mano >= 29
        elif diferencia > 5:
            return puntos_mano >= 23
        else:
            return puntos_mano >= 26

    def calcular_probabilidad_victoria(self):
        if not self.mano:
            return 0
        mejor_carta = max(self.mano, key=lambda c: c.poder_truco)
        poder = mejor_carta.poder_truco
        
        mejores_vistas = sum(1 for c in self.cartas_vistas if c.poder_truco > poder)
        cartas_superiores_totales = sum(1 for p in range(poder + 1, 15) for _, v in JERARQUIA_TRUCO.items() if v == p)
        
        cartas_superiores_vivas = cartas_superiores_totales - mejores_vistas
        
        if cartas_superiores_vivas == 0:
            return 100.0
        else:
            prob = max(0, 100 - (cartas_superiores_vivas * 10))
            return prob

    def evaluar_riesgo_truco(self, cartas_mano=None, tanteador=None, cartas_vistas=None):
        if not self.mano: return False
        
        diferencia = self.puntos_rival - self.puntos_propios
        prob_victoria = self.calcular_probabilidad_victoria()
        mejor_carta = max(self.mano, key=lambda c: c.poder_truco)
        
        umbral_poder = 9
        umbral_prob = 50
        
        if diferencia > 5:
            umbral_poder = 7
            umbral_prob = 30
            
        return mejor_carta.poder_truco >= umbral_poder or prob_victoria >= umbral_prob

    def remover_carta(self, carta):
        for c in self.mano:
            if c.numero == carta.numero and c.palo == carta.palo:
                self.mano.remove(c)
                self.cartas_jugadas_bot.append(c)
                self.cartas_vistas.append(c)
                break

class TrucoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Asistente de Truco - Bot Nivel 2")
        self.bot = AsistenteBot()
        self.logger = LoggerMano()
        self.crear_interfaz()

    def log(self, mensaje):
        self.consola.config(state='normal')
        self.consola.insert(tk.END, mensaje + "\n")
        self.consola.see(tk.END)
        self.consola.config(state='disabled')

    def validar_carta(self, num_str, palo):
        try:
            num = int(num_str)
            if num not in NUMEROS_VALIDOS:
                raise ValueError
            return Carta(num, palo)
        except ValueError:
            return None

    def cargar_mano(self):
        # 1. GUARDAR LA MANO ANTERIOR (si existía)
        self.logger.guardar_y_cerrar_mano(self.pts_bot.get(), self.pts_rival.get())

        c1 = self.validar_carta(self.num1.get(), self.palo1.get())
        c2 = self.validar_carta(self.num2.get(), self.palo2.get())
        c3 = self.validar_carta(self.num3.get(), self.palo3.get())

        if not (c1 and c2 and c3):
            messagebox.showerror("Error", "Asegúrate de ingresar números válidos (1-7, 10-12).")
            return

        self.bot.set_mano([c1, c2, c3])
        
        # 2. INICIAR LA NUEVA MANO EN EL LOGGER
        self.logger.iniciar_mano(self.pts_bot.get(), self.pts_rival.get(), [c1, c2, c3])
        
        # 3. Registrar los cálculos iniciales del bot
        pts_envido = self.bot.calcular_envido()
        self.logger.registrar_evento("evaluacion", f"Puntos de envido base calculados: {pts_envido}")

        self.actualizar_vista_mano()
        self.log(f"--- NUEVA MANO CARGADA ---")
        self.log(f"Cartas: {c1}, {c2}, {c3}")
        self.log(f"Puntos de Envido automáticos: {pts_envido}")

    def actualizar_vista_mano(self):
        if not self.bot.mano:
            self.lbl_mano_actual.config(text="Mano actual: (Vacía)")
        else:
            txt = " | ".join(str(c) for c in self.bot.mano)
            self.lbl_mano_actual.config(text=f"Mano actual: {txt}")

    def actualizar_tanteador_ui(self):
        self.bot.actualizar_tanteador(self.pts_bot.get(), self.pts_rival.get())
        self.log(f"Tanteador actualizado: Bot {self.bot.puntos_propios} - Rival {self.bot.puntos_rival}")

    def consejo_envido(self):
        pts = self.bot.calcular_envido()
        acepta = self.bot.evaluar_riesgo_envido()
        self.logger.registrar_evento("evaluacion", f"Evalúa Envido: Tiene {pts} puntos.")
        if acepta:
            self.logger.registrar_evento("envido", "Bot ACEPTA / CANTA envido.")
            self.log(f"ENVIDO: Tienes {pts} puntos. ¡ACEPTAR / CANTAR!")
        else:
            self.logger.registrar_evento("envido", "Bot RECHAZA envido.")
            self.log(f"ENVIDO: Tienes {pts} puntos. RECHAZAR / IR AL MAZO.")

    def consejo_truco(self):
        if not self.bot.mano:
            self.log("TRUCO: No tienes cartas.")
            return
        
        acepta = self.bot.evaluar_riesgo_truco()
        prob = self.bot.calcular_probabilidad_victoria()
        self.logger.registrar_evento("evaluacion", f"Evalúa Truco: Probabilidad victoria {prob:.1f}%")
        if acepta:
            self.logger.registrar_evento("truco", f"Bot ACEPTA / CANTA truco (Prob: {prob:.1f}%).")
            self.log(f"TRUCO: ¡ACEPTAR / CANTAR! (Probabilidad ganar baza: {prob:.1f}%)")
        else:
            self.logger.registrar_evento("truco", f"Bot RECHAZA truco (Prob: {prob:.1f}%).")
            self.log(f"TRUCO: Cartas débiles o en desventaja. RECHAZAR. (Probabilidad: {prob:.1f}%)")

    def jugar_carta(self, carta_rival=None):
        if not self.bot.mano:
            self.log("JUGAR: No te quedan cartas.")
            return

        self.bot.mano.sort(key=lambda c: c.poder_truco)
        carta_elegida = None
        motivo = ""

        if carta_rival is None:
            if 'parda' in self.bot.resultados_rondas:
                carta_elegida = self.bot.mano[-1]
                motivo = "Ronda anterior fue parda. Tira tu mejor carta para asegurar."
            elif len(self.bot.mano) >= 2 and self.bot.mano[-1].poder_truco == 14:
                carta_elegida = self.bot.mano[-2]
                motivo = "Abre con tu segunda mejor para guardar el ancho."
            else:
                carta_elegida = self.bot.mano[-1]
                motivo = "Abre con tu carta más alta."
        else:
            for carta in self.bot.mano:
                if carta.poder_truco > carta_rival.poder_truco:
                    carta_elegida = carta
                    motivo = "Mata su carta con esta."
                    break
            if not carta_elegida:
                carta_elegida = self.bot.mano[0]
                motivo = "No puedes matarla. Tira tu carta más baja."

        self.log(f"JUGAR: {motivo} -> {carta_elegida}")
        
        ronda_str = f"ronda_{self.bot.ronda_actual}"
        if carta_rival:
            self.logger.registrar_evento(ronda_str, f"Bot decide responder/matar con {carta_elegida} (Poder: {carta_elegida.poder_truco}) - Motivo: {motivo}")
        else:
            self.logger.registrar_evento(ronda_str, f"Bot abre con {carta_elegida} (Poder: {carta_elegida.poder_truco}) - Motivo: {motivo}")

        if messagebox.askyesno("Confirmación", f"¿Tiraste el {carta_elegida} a la mesa?"):
            self.bot.remover_carta(carta_elegida)
            self.actualizar_vista_mano()
            self.log(f"({carta_elegida} eliminada de la mano)")
            self.bot.ronda_actual += 1

    def abrir_mano(self):
        self.jugar_carta()

    def registrar_carta_rival_ui(self):
        c_rival = self.validar_carta(self.num_rival.get(), self.palo_rival.get())
        if not c_rival:
            messagebox.showerror("Error", "Ingresa una carta rival válida.")
            return
        self.bot.registrar_accion_rival('carta', c_rival)
        ronda_str = f"ronda_{self.bot.ronda_actual}"
        self.logger.registrar_evento(ronda_str, f"Rival tiró {c_rival}")
        self.log(f"Registrada carta rival: {c_rival}")
        self.num_rival.set("")

    def responder_mano(self):
        if not self.bot.cartas_jugadas_rival:
            self.log("No hay cartas rivales registradas a las que responder.")
            return
        ultima_carta = self.bot.cartas_jugadas_rival[-1]
        self.jugar_carta(ultima_carta)

    def crear_interfaz(self):
        frame_top = tk.Frame(self.root, padx=10, pady=10)
        frame_top.pack(fill="x")

        tk.Label(frame_top, text="INGRESO DE CARTAS", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=3, pady=5)
        
        self.num1 = tk.StringVar(value="1")
        self.palo1 = tk.StringVar(value=PALOS_VALIDOS[0])
        tk.Label(frame_top, text="Carta 1:").grid(row=1, column=0)
        tk.Spinbox(frame_top, values=NUMEROS_VALIDOS, textvariable=self.num1, width=5).grid(row=1, column=1, padx=5)
        f_p1 = tk.Frame(frame_top)
        f_p1.grid(row=1, column=2)
        for p in PALOS_VALIDOS: tk.Radiobutton(f_p1, text=p.capitalize(), variable=self.palo1, value=p).pack(side=tk.LEFT)

        self.num2 = tk.StringVar(value="1")
        self.palo2 = tk.StringVar(value=PALOS_VALIDOS[0])
        tk.Label(frame_top, text="Carta 2:").grid(row=2, column=0)
        tk.Spinbox(frame_top, values=NUMEROS_VALIDOS, textvariable=self.num2, width=5).grid(row=2, column=1, padx=5)
        f_p2 = tk.Frame(frame_top)
        f_p2.grid(row=2, column=2)
        for p in PALOS_VALIDOS: tk.Radiobutton(f_p2, text=p.capitalize(), variable=self.palo2, value=p).pack(side=tk.LEFT)

        self.num3 = tk.StringVar(value="1")
        self.palo3 = tk.StringVar(value=PALOS_VALIDOS[0])
        tk.Label(frame_top, text="Carta 3:").grid(row=3, column=0)
        tk.Spinbox(frame_top, values=NUMEROS_VALIDOS, textvariable=self.num3, width=5).grid(row=3, column=1, padx=5)
        f_p3 = tk.Frame(frame_top)
        f_p3.grid(row=3, column=2)
        for p in PALOS_VALIDOS: tk.Radiobutton(f_p3, text=p.capitalize(), variable=self.palo3, value=p).pack(side=tk.LEFT)

        tk.Button(frame_top, text="Cargar Mano Inicial", command=self.cargar_mano, bg="#4CAF50", fg="white").grid(row=4, column=0, columnspan=3, pady=10)

        frame_tanteador = tk.Frame(frame_top)
        frame_tanteador.grid(row=5, column=0, columnspan=3, pady=5)
        tk.Label(frame_tanteador, text="Pts Bot:").pack(side=tk.LEFT)
        self.pts_bot = tk.IntVar(value=0)
        tk.Entry(frame_tanteador, textvariable=self.pts_bot, width=4).pack(side=tk.LEFT, padx=5)
        tk.Label(frame_tanteador, text="Pts Rival:").pack(side=tk.LEFT)
        self.pts_rival = tk.IntVar(value=0)
        tk.Entry(frame_tanteador, textvariable=self.pts_rival, width=4).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_tanteador, text="Actualizar", command=self.actualizar_tanteador_ui).pack(side=tk.LEFT, padx=5)

        ttk.Separator(self.root, orient='horizontal').pack(fill='x', padx=10)

        frame_mid = tk.Frame(self.root, padx=10, pady=5)
        frame_mid.pack(fill="x")
        self.lbl_mano_actual = tk.Label(frame_mid, text="Mano actual: (Vacía)", font=("Arial", 10, "bold"), fg="#333333")
        self.lbl_mano_actual.pack()

        ttk.Separator(self.root, orient='horizontal').pack(fill='x', padx=10)

        frame_acciones = tk.Frame(self.root, padx=10, pady=10)
        frame_acciones.pack(fill="x")

        tk.Button(frame_acciones, text="¿Qué hago con el Envido?", command=self.consejo_envido).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(frame_acciones, text="¿Qué hago con el Truco?", command=self.consejo_truco).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(frame_acciones, text="Tirar Carta (Abro yo)", command=self.abrir_mano).grid(row=1, column=0, columnspan=2, pady=10, sticky="we", padx=5)

        tk.Label(frame_acciones, text="Rival tiró:").grid(row=2, column=0, sticky="e")
        
        frame_rival = tk.Frame(frame_acciones)
        frame_rival.grid(row=2, column=1, sticky="w")
        
        self.num_rival = tk.StringVar(value="1")
        self.palo_rival = tk.StringVar(value=PALOS_VALIDOS[0])
        tk.Spinbox(frame_rival, values=NUMEROS_VALIDOS, textvariable=self.num_rival, width=5).pack(side=tk.LEFT, padx=2)
        for p in PALOS_VALIDOS:
            tk.Radiobutton(frame_rival, text=p.capitalize(), variable=self.palo_rival, value=p).pack(side=tk.LEFT)
        
        tk.Button(frame_acciones, text="Registrar Carta Rival", command=self.registrar_carta_rival_ui, bg="#FF9800", fg="white").grid(row=3, column=0, pady=5, sticky="we", padx=5)
        tk.Button(frame_acciones, text="Responder a Última Carta", command=self.responder_mano, bg="#2196F3", fg="white").grid(row=3, column=1, pady=5, sticky="we", padx=5)

        frame_bottom = tk.Frame(self.root, padx=10, pady=10)
        frame_bottom.pack(fill="both", expand=True)
        tk.Label(frame_bottom, text="Consejos del Bot:").pack(anchor="w")
        self.consola = tk.Text(frame_bottom, height=8, width=50, state='disabled', bg="#f4f4f4")
        self.consola.pack(fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = TrucoApp(root)
    root.mainloop()
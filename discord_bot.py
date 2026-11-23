import discord
from discord import app_commands
import random, os, json
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Truco Online!"
def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
Thread(target=run, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

partidas = {}
NOMBRES_BOTS = ["Don Ramon","Messi","El Mago","Cacho"]
PALOS = ["espada","basto","oro","copa"]
NUMEROS = [1,2,3,4,5,6,7,10,11,12]
USUARIOS_FILE = "usuarios.json"

# --- CARTAS ---
CARPETA_CARTAS = "Cartas_reales"
MAPA_CARTAS = {
    (1, "oro"): "WA_1795360976029.jpeg", (2, "oro"): "WA_1795361008859.jpeg", (3, "oro"): "WA_1795361029880.jpeg",
    (4, "oro"): "WA_1795361045359.jpeg", (5, "oro"): "WA_1795361059645.jpeg", (6, "oro"): "WA_1795361075067.jpeg",
    (7, "oro"): "f298a3b4410a23085a92f853f79a248d.jpg", (10, "oro"): "WA_1795361089117.jpeg",
    (11, "oro"): "WA_1795361103363.jpeg", (12, "oro"): "WA_1795361115693.jpeg",
    (1, "copa"): "WA_1795361133619.jpeg", (2, "copa"): "WA_1795361147081.jpeg", (3, "copa"): "WA_1795361159409.jpeg",
    (4, "copa"): "WA_1795361167029.jpeg", (5, "copa"): "WA_1795361181627.jpeg", (6, "copa"): "WA_1795361194858.jpeg",
    (7, "copa"): "WA_1795361207200.jpeg", (10, "copa"): "WA_1795361223477.jpeg",
    (11, "copa"): "WA_1795361247470.jpeg", (12, "copa"): "WA_1795361256354.jpeg",
    (1, "espada"): "WA_1795361273879.jpeg", (2, "espada"): "WA_1795361291920.jpeg", (3, "espada"): "WA_1795361309028.jpeg",
    (4, "espada"): "WA_1795361319086.jpeg", (5, "espada"): "WA_1795361329193.jpeg", (6, "espada"): "WA_1795361338149.jpeg",
    (7, "espada"): "WA_1795361346453.jpeg", (10, "espada"): "WA_1795361359955.jpeg",
    (11, "espada"): "WA_1795361370531.jpeg", (12, "espada"): "WA_1795361377563.jpeg",
    (1, "basto"): "WA_1795361405106.jpeg", (2, "basto"): "WA_1795361414925.jpeg", (3, "basto"): "WA_1795361426382.jpeg",
    (4, "basto"): "WA_1795361435086.jpeg", (5, "basto"): "WA_1795361445594.jpeg", (6, "basto"): "WA_1795361455619.jpeg",
    (7, "basto"): "WA_1795361462938.jpeg", (10, "basto"): "WA_1795361479310.jpeg",
    (11, "basto"): "WA_1795361489348.jpeg", (12, "basto"): "WA_1795361496548.jpeg",
}
DORSO = "WA_1795360931463.jpeg"
def foto_carta(n,p):
    nom = MAPA_CARTAS.get((n,p))
    if nom:
        r = os.path.join(CARPETA_CARTAS, nom)
        if os.path.exists(r): return r
    rd = os.path.join(CARPETA_CARTAS, DORSO)
    return rd if os.path.exists(rd) else None

# VALOR TRUCO REAL
VALOR_TRUCO = {
    (1, "espada"): 14, (1, "basto"): 13, (7, "espada"): 12, (7, "oro"): 11,
    3: 10, 2: 9, 1: 8, 12: 7, 11: 6, 10: 5, 7: 4, 6: 3, 5: 2, 4: 1
}
def valor_truco_carta(numero, palo):
    if (numero, palo) in VALOR_TRUCO: return VALOR_TRUCO[(numero, palo)]
    return VALOR_TRUCO.get(numero, 0)

def get_bot_avatar():
    for n in ["bot_rojo.png", "bot_rojo.jpg", "bot_rojo.jpeg", "bot_rojo.pnj"]:
        if os.path.exists(n): return n
        if os.path.exists(f"tableros/{n}"): return f"tableros/{n}"
    return None

def get_default_tablero():
    if os.path.exists("tableros/Tablero.jpg"): return "tableros/Tablero.jpg"
    if os.path.exists("tableros/tablero.jpg"): return "tableros/tablero.jpg"
    if os.path.exists("Tablero.jpg"): return "Tablero.jpg"
    if os.path.exists("tableros"):
        for f in os.listdir("tableros"):
            if "tablero" in f.lower() or "madera" in f.lower() or "default" in f.lower():
                return os.path.join("tableros", f)
    return None

TIENDA_TABLEROS = {
    "boca": {"nombre": "Boca", "precio": 100, "keyword": "boca"}, "river": {"nombre": "River", "precio": 100, "keyword": "river"},
    "racing": {"nombre": "Racing", "precio": 100, "keyword": "racing"}, "casla": {"nombre": "San Lorenzo", "precio": 100, "keyword": "san_lorenzo"},
    "oro": {"nombre": "Oro", "precio": 500, "keyword": "oro"}, "diamante": {"nombre": "Diamante", "precio": 1000, "keyword": "diamante"},
    "fnaf": {"nombre": "FNAF Springtrap", "precio": 1500, "keyword": "springtrap"},
}
CODIGOS = {
    "navidad_se_acerca": {"tipo": "trucoins", "valor": 500}, "gaming": {"tipo": "tablero", "valor": "neon"},
    "truco!": {"tipo": "poder", "valor": "random"},
}
PODERES_DISPONIBLES = ["ver_carta_rival", "cambiar_carta", "doble_puntos_envido", "esconder_carta"]

def cargar_usuarios():
    if not os.path.exists(USUARIOS_FILE): return {}
    try:
        with open(USUARIOS_FILE, "r") as f: return json.load(f)
    except: return {}
def guardar_usuarios(data):
    with open(USUARIOS_FILE, "w") as f: json.dump(data, f, indent=2)
def get_or_create_user(user_id):
    data = cargar_usuarios(); uid = str(user_id)
    if uid not in data:
        data[uid] = {"wins":0, "losses":0, "trucoins":300, "tableros":["default"], "equipado":"default", "poderes":[], "codigos_usados":[]}
        guardar_usuarios(data)
    return data[uid], data

def buscar_archivo_tablero(keyword):
    if os.path.exists("tableros"):
        kw = keyword.lower()
        for archivo in os.listdir("tableros"):
            if kw in archivo.lower(): return os.path.join("tableros", archivo)
    return None

def get_tablero_path_user(user_id):
    usuario, _ = get_or_create_user(user_id)
    equipado = usuario.get("equipado", "default")
    if equipado == "default": return get_default_tablero()
    if equipado == "neon":
        p = buscar_archivo_tablero("gamer"); return p if p else get_default_tablero()
    info = TIENDA_TABLEROS.get(equipado)
    if info:
        p = buscar_archivo_tablero(info["keyword"]); return p if p else get_default_tablero()
    p = buscar_archivo_tablero(equipado); return p if p else get_default_tablero()

def calcular_envido(cartas):
    mejor=0
    for i in range(3):
        for j in range(i+1,3):
            if cartas[i][1]==cartas[j][1]:
                n1=0 if cartas[i][0]>=10 else cartas[i][0]
                n2=0 if cartas[j][0]>=10 else cartas[j][0]
                if n1+n2+20>mejor: mejor=n1+n2+20
    if mejor==0:
        for n,p in cartas:
            v=0 if n>=10 else n
            if v>mejor: mejor=v
    return mejor

# --- BOTONES CON BLOQUEO FINAL ---
class CartaButton(discord.ui.Button):
    def __init__(self,carta,owner):
        self.carta=carta; self.owner=owner
        super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary,row=0)
    async def callback(self,interaction: discord.Interaction):
        if interaction.user.id!=self.owner:
            await interaction.response.send_message("No es tu partida",ephemeral=True); return
        
        self.disabled=True
        self.label=f"✓ {self.carta[0]} de {self.carta[1]}"
        data_partida = partidas.get(self.owner)
        if not data_partida or not data_partida["bot"]:
            await interaction.response.edit_message(view=self.view); return
        
        carta_bot = data_partida["bot"].pop(0)
        v_yo = valor_truco_carta(self.carta[0], self.carta[1])
        v_bot = valor_truco_carta(carta_bot[0], carta_bot[1])
        
        if v_yo > v_bot:
            ganador = f"🏆 Ganaste vos!"
            data_partida["puntos_jugador"] += 1
        elif v_bot > v_yo:
            ganador = f"😢 Ganó {data_partida['nombre']}"
            data_partida["puntos_bot"] += 1
        else:
            ganador = "🤝 Empate!"
        
        data_partida["jugadas"].append((self.carta, carta_bot))
        
        # CHEQUEO SI ES LA ULTIMA CARTA
        cartas_restantes = sum(1 for c in self.view.children if isinstance(c, CartaButton) and not c.disabled)
        es_final = len(data_partida["bot"]) == 0 or cartas_restantes == 0

        files=[]
        r1 = foto_carta(self.carta[0], self.carta[1])
        r2 = foto_carta(carta_bot[0], carta_bot[1])
        if r1 and os.path.exists(r1): files.append(discord.File(r1, filename="yo.jpg"))
        if r2 and os.path.exists(r2): files.append(discord.File(r2, filename="bot_carta.jpg"))
        
        if es_final:
            for child in self.view.children: child.disabled = True
            py = data_partida.get("puntos_jugador",0)
            pb = data_partida.get("puntos_bot",0)
            if py > pb: final_txt = f"\n\n🎉 **GANASTE LA PARTIDA {py} a {pb}** - /jugar de nuevo"
            elif pb > py: final_txt = f"\n\n💀 **PERDISTE LA PARTIDA {pb} a {py}** - /jugar para revancha"
            else: final_txt = f"\n\n🤝 **EMPATE {py} a {pb}**"
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send(f"**Vos {self.carta[0]} de {self.carta[1]}** vs **Bot {carta_bot[0]} de {carta_bot[1]}**\n{ganador}{final_txt}", files=files if files else None)
            partidas.pop(self.owner, None)
        else:
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send(f"**Vos {self.carta[0]} de {self.carta[1]}** vs **Bot {carta_bot[0]} de {carta_bot[1]}**\n{ganador}", files=files if files else None)

class TrucoButton(discord.ui.Button):
    def __init__(self,owner): self.owner=owner; super().__init__(label="TRUCO",style=discord.ButtonStyle.danger,row=1)
    async def callback(self,interaction: discord.Interaction):
        if interaction.user.id!=self.owner: await interaction.response.send_message("No es tu partida",ephemeral=True); return
        await interaction.response.send_message(f"{interaction.user.mention} cantó TRUCO!")

class EnvidoButton(discord.ui.Button):
    def __init__(self,owner): self.owner=owner; super().__init__(label="ENVIDO",style=discord.ButtonStyle.success,row=1)
    async def callback(self,interaction: discord.Interaction):
        if interaction.user.id!=self.owner: await interaction.response.send_message("No es tu partida",ephemeral=True); return
        env = partidas.get(self.owner, {}).get("envido", 0)
        await interaction.response.send_message(f"{interaction.user.mention} cantó ENVIDO! Tengo {env}")

class ExpresionesButton(discord.ui.Button):
    def __init__(self,owner): self.owner=owner; super().__init__(label="Expresiones",style=discord.ButtonStyle.secondary,row=2)
    async def callback(self,interaction: discord.Interaction):
        if interaction.user.id!=self.owner: await interaction.response.send_message("No es tu partida",ephemeral=True); return
        await interaction.response.send_message("Elegí tu mensaje:", view=ExpresionesView(self.owner), ephemeral=True)

class SalirButton(discord.ui.Button):
    def __init__(self,owner): self.owner=owner

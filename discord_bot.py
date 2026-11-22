import discord
from discord import app_commands
import random
import os
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home():
    return "Bot Truco Online!"
def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
Thread(target=run, daemon=True).start()

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

partidas = {}

# --- CONFIG MESA Y BOTS ---
NOMBRES_BOTS = ["Don Ramón", "Messi", "El Mago", "Cacho"]
CARPETA_BOTS = "truco_bots"
TABLERO_PATH = os.path.join(CARPETA_BOTS, "Tablero.jpg")
# Si no está en truco_bots, busca en la raiz
if not os.path.exists(TABLERO_PATH):
    TABLERO_PATH = "Tablero.jpg"

BOT_AVATARES = [
    os.path.join(CARPETA_BOTS, "Bot_rojo.png"),
    os.path.join(CARPETA_BOTS, "Bot_naranja.png"),
    "Bot_rojo.png",
    "Bot_naranja.png"
]

def get_bot_avatar_file():
    for ruta in BOT_AVATARES:
        if os.path.exists(ruta):
            return ruta
    return None

# --- MAZO REAL ARGENTINO ---
PALOS = ["espada", "basto", "oro", "copa"]
NUMEROS = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
CARPETA_CARTAS = "Cartas_reales"
MAPA_CARTAS = {
    (1, "oro"): "WA_1795360976029.jpeg",
    (2, "oro"): "WA_1795361008859.jpeg",
    (3, "oro"): "WA_1795361029880.jpeg",
    (4, "oro"): "WA_1795361045359.jpeg",
    (5, "oro"): "WA_1795361059645.jpeg",
    (6, "oro"): "WA_1795361075067.jpeg",
    (7, "oro"): "f298a3b4410a23085a92f853f79a248d.jpg",
    (10, "oro"): "WA_1795361089117.jpeg",
    (11, "oro"): "WA_1795361103363.jpeg",
    (12, "oro"): "WA_1795361115693.jpeg",
    (1, "copa"): "WA_1795361133619.jpeg",
    (2, "copa"): "WA_1795361147081.jpeg",
    (3, "copa"): "WA_1795361159409.jpeg",
    (4, "copa"): "WA_1795361167029.jpeg",
    (5, "copa"): "WA_1795361181627.jpeg",
    (6, "copa"): "WA_1795361194858.jpeg",
    (7, "copa"): "WA_1795361207200.jpeg",
    (10, "copa"): "WA_1795361223477.jpeg",
    (11, "copa"): "WA_1795361247470.jpeg",
    (12, "copa"): "WA_1795361256354.jpeg",
    (1, "espada"): "WA_1795361273879.jpeg",
    (2, "espada"): "WA_1795361291920.jpeg",
    (3, "espada"): "WA_1795361309028.jpeg",
    (4, "espada"): "WA_1795361319086.jpeg",
    (5, "espada"): "WA_1795361329193.jpeg",
    (6, "espada"): "WA_1795361338149.jpeg",
    (7, "espada"): "WA_1795361346453.jpeg",
    (10, "espada"): "WA_1795361359955.jpeg",
    (11, "espada"): "WA_1795361370531.jpeg",
    (12, "espada"): "WA_1795361377563.jpeg",
    (1, "basto"): "WA_1795361405106.jpeg",
    (2, "basto"): "WA_1795361414925.jpeg",
    (3, "basto"): "WA_1795361426382.jpeg",
    (4, "basto"): "WA_1795361435086.jpeg",
    (5, "basto"): "WA_1795361445594.jpeg",
    (6, "basto"): "WA_1795361455619.jpeg",
    (7, "basto"): "WA_1795361462938.jpeg",
    (10, "basto"): "WA_1795361479310.jpeg",
    (11, "basto"): "WA_1795361489348.jpeg",
    (12, "basto"): "WA_1795361496548.jpeg",
}
DORSO = "WA_1795360931463.jpeg"

def foto_carta(numero, palo):
    nombre = MAPA_CARTAS.get((numero, palo))
    if nombre:
        ruta = os.path.join(CARPETA_CARTAS, nombre)
        if os.path.exists(ruta):
            return ruta
    ruta_dorso = os.path.join(CARPETA_CARTAS, DORSO)
    return ruta_dorso if os.path.exists(ruta_dorso) else None

VALOR_TRUCO = {(1, "espada"): 14, (1, "basto"): 13, (7, "espada"): 12, (7, "oro"): 11, 3: 10, 2: 9, 1: 8, 12: 7, 11: 6, 10: 5, 7: 4, 6: 3, 5: 2, 4: 1}
def valor_truco_carta(numero, palo):
    if (numero, palo) in VALOR_TRUCO: return VALOR_TRUCO[(numero, palo)]
    return VALOR_TRUCO.get(numero, 0)

def calcular_envido(cartas):
    mejor = 0
    for i in range(len(cartas)):
        for j in range(i+1, len(cartas)):
            if cartas[i][1] == cartas[j][1]:
                n1 = 0 if cartas[i][0] >= 10 else cartas[i][0]
                n2 = 0 if cartas[j][0] >= 10 else cartas[j][0]
                total = n1 + n2 + 20
                if total > mejor: mejor = total
    if mejor == 0:
        for n, p in cartas:
            val = 0 if n >= 10 else n
            if val > mejor: mejor = val
    return mejor

def tiene_flor(cartas): return cartas[0][1] == cartas[1][1] == cartas[2][1]

# --- VIEWS NUEVAS ---
class CartaButton(discord.ui.Button):
    def __init__(self, carta, idx):
        self.carta = carta
        self.idx = idx
        super().__init__(label=f"{carta[0]} de {carta[1]}", style=discord.ButtonStyle.primary, row=0)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Vas a tirar **{self.carta[0]} de {self.carta[1]}**? Confirmá con el botón verde", view=ConfirmarTirarView(self.carta, self.idx, interaction.user.id), ephemeral=True)

class ConfirmarTirarView(discord.ui.View):
    def __init__(self, carta, idx, owner_id):
        super().__init__(timeout=30)
        self.carta = carta; self.idx = idx; self.owner_id = owner_id
    @discord.ui.button(label="✅ TIRAR CARTA", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        partida = partidas.get(self.owner_id)
        if partida: await interaction.response.send_message(f"🃏 Tiraste **{self.carta[0]} de {self.carta[1]}** - El bot piensa...", ephemeral=False)
        else: await interaction.response.send_message("No hay partida", ephemeral=True)

# --- COMANDOS ---

@tree.command(name="jugar", description="Jugar al truco vs bot o vs amigo")
@app_commands.describe(oponente="Escribi 'bot' o menciona a tu amigo")
async def jugar(interaction: discord.Interaction, oponente: str):
    mazo = [(n, p) for p in PALOS for n in NUMEROS]
    random.shuffle(mazo)
    mano_jugador = [mazo.pop() for _ in range(3)]
    mano_rival = [mazo.pop() for _ in range(3)]
    envido_jugador = calcular_envido(mano_jugador)
    envido_bot = calcular_envido(mano_rival)
    
    partidas[interaction.user.id] = {"mano": mano_jugador, "rival": mano_rival, "envido": envido_jugador, "envido_bot": envido_bot}

    if oponente.lower() == "bot":
        nombre_bot = random.choice(NOMBRES_BOTS)
        avatar_path = get_bot_avatar_file()
        
        embed = discord.Embed(title="🟩 MESA DE TRUCO 1v1 - ARGENTINO", description=f"**{nombre_bot}** 🤖 [BOT] VS {interaction.user.mention} 👤\n\nTu envido: **{envido_jugador}** {'🌸 FLOR!' if tiene_flor(mano_jugador) else ''}", color=0x1e8449)
        
        files = []
        if os.path.exists(TABLERO_PATH):
            files.append(discord.File(TABLERO_PATH, filename="tablero.jpg"))
            embed.set_image(url="attachment://tablero.jpg")
        if avatar_path:
            files.append(discord.File(avatar_path, filename="bot.png"))
            embed.set_thumbnail(url="attachment://bot.png")
            embed.set_author(name=f"{nombre_bot} [BOT] - Tiene 3 cartas boca abajo")
        
        view = discord.ui.View(timeout=120)
        for idx, carta in enumerate(mano_jugador):
            view.add_item(CartaButton(carta, idx))
        view.add_item(discord.ui.Button(label="ENVIDO", style=discord.ButtonStyle.success, row=1))
        view.add_item(discord.ui.Button(label="TRUCO", style=discord.ButtonStyle.danger, row=1))
        
        await interaction.response.send_message(embed=embed, files=files, view=view)
    else:
        texto_cartas = "\n".join([f"{n} de {p}" for n, p in mano_jugador])
        await interaction.response.send_message(f"🔥 {interaction.user.mention} desafió a {oponente}! Tus cartas: {texto_cartas}")

@tree.command(name="cantar", description="Cantar en el truco")
@app_commands.choices(canto=[app_commands.Choice(name="envido", value="envido"), app_commands.Choice(name="real envido", value="real_envido"), app_commands.Choice(name="falta envido", value="falta_envido"), app_commands.Choice(name="flor", value="flor"), app_commands.Choice(name="truco", value="truco"), app_commands.Choice(name="retruco", value="retruco"), app_commands.Choice(name="vale cuatro", value="vale_cuatro")])
async def cantar(interaction: discord.Interaction, canto: str):
    partida = partidas.get(interaction.user.id)
    if not partida: await interaction.response.send_message("Primero /jugar bot", ephemeral=True); return
    await interaction.response.send_message(f"🎲 {interaction.user.mention} cantó **{canto.upper()}**! Tu envido: {partida['envido']}")

@tree.command(name="tirar", description="Tirar carta 1,2 o 3")
async def tirar(interaction: discord.Interaction, numero: int):
    partida = partidas.get(interaction.user.id)
    if not partida or numero < 1 or numero > 3: await interaction.response.send_message("Usá /jugar bot primero", ephemeral=True); return
    carta = partida['mano'][numero-1]
    ruta = foto_carta(carta[0], carta[1])
    archivo = [discord.File(ruta)] if ruta and os.path.exists(ruta) else []
    await interaction.response.send_message(f"🃏 {interaction.user.mention} tiró **{carta[0]} de {carta[1]}**", files=archivo)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="Truco [🤖 vs Bot] [👥 vs Amigo]"))
    await tree.sync()
    print("Bot truco con mesa listo!")

bot.run(os.getenv("DISCORD_TOKEN") or "TU_TOKEN")

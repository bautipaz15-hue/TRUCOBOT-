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

# A PARTIR DE ACA SIGUE TU CODIGO NORMAL
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

partidas = {}

# --- MAZO REAL ARGENTINO ---
PALOS = ["espada", "basto", "oro", "copa"]
NUMEROS = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]

# --- TUS 40 FOTOS REALES WA_ ---
CARPETA_CARTAS = "Cartas_reales"
_ARCHIVOS = sorted([f for f in os.listdir(CARPETA_CARTAS) if f.endswith(('.jpg','.jpeg','.png','.JPG'))])
_MAZO_ORDENADO = [(n, p) for p in PALOS for n in NUMEROS]
MAPA_CARTAS = {carta: _ARCHIVOS[i % len(_ARCHIVOS)] for i, carta in enumerate(_MAZO_ORDENADO)}

def foto_carta(numero, palo):
    nombre = MAPA_CARTAS.get((numero, palo))
    if nombre:
        return os.path.join(CARPETA_CARTAS, nombre)
    return None

VALOR_TRUCO = {
    (1, "espada"): 14,
    (1, "basto"): 13,
    (7, "espada"): 12,
    (7, "oro"): 11,
    3: 10, 2: 9, 1: 8, 12: 7, 11: 6, 10: 5, 7: 4, 6: 3, 5: 2, 4: 1
}

def valor_truco_carta(numero, palo):
    if (numero, palo) in VALOR_TRUCO:
        return VALOR_TRUCO[(numero, palo)]
    return VALOR_TRUCO.get(numero, 0)

def calcular_envido(cartas):
    mejor = 0
    for i in range(len(cartas)):
        for j in range(i+1, len(cartas)):
            if cartas[i][1] == cartas[j][1]:
                n1 = 0 if cartas[i][0] >= 10 else cartas[i][0]
                n2 = 0 if cartas[j][0] >= 10 else cartas[j][0]
                total = n1 + n2 + 20
                if total > mejor:
                    mejor = total
    if mejor == 0:
        for n, p in cartas:
            val = 0 if n >= 10 else n
            if val > mejor:
                mejor = val
    return mejor

def tiene_flor(cartas):
    return cartas[0][1] == cartas[1][1] == cartas[2][1]

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
    flor_jugador = tiene_flor(mano_jugador)
    
    partidas[interaction.user.id] = {
        "mano": mano_jugador,
        "rival": mano_rival,
        "envido": envido_jugador,
        "envido_bot": envido_bot,
        "puntos_jugador": 0,
        "puntos_bot": 0,
        "truco": 1,
        "envido_cantado": False
    }
    
    texto_cartas = "\n".join([f"{n} de {p}" for n, p in mano_jugador])
    extra = "¡TENÉS FLOR! 🌸" if flor_jugador else f"Tu envido es: **{envido_jugador}**"

    archivos = []
    for n, p in mano_jugador:
        ruta = foto_carta(n, p)
        if ruta and os.path.exists(ruta):
            archivos.append(discord.File(ruta))

    if oponente.lower() == "bot":
        await interaction.response.send_message(
            f"🤖 **PARTIDA VS BOT - TRUCO REAL**\n"
            f"👤 {interaction.user.mention}\n"
            f"🃏 Tus cartas:\n{texto_cartas}\n\n"
            f"📊 {extra}\n\n"
            f"Usá:\n"
            f"`/cantar envido` `/cantar real-envido` `/cantar falta-envido`\n"
            f"`/cantar flor` `/cantar truco`\n"
            f"`/tirar 1` `/tirar 2` `/tirar 3` para jugar carta\n"
            f"`/irse` para irte al mazo",
            files=archivos,
            ephemeral=False
        )
    else:
        await interaction.response.send_message(
            f"🔥 **DESAFÍO TRUQUERO REAL**\n"
            f"{interaction.user.mention} desafió a {oponente}!\n"
            f"🃏 Tus cartas por privado: {texto_cartas} ({extra})\n"
            f"Esperando que {oponente} acepte con `/quiero`",
            files=archivos
        )

@tree.command(name="cantar", description="Cantar en el truco (con reglas reales)")
@app_commands.choices(canto=[
    app_commands.Choice(name="envido", value="envido"),
    app_commands.Choice(name="real envido", value="real_envido"),
    app_commands.Choice(name="falta envido", value="falta_envido"),
    app_commands.Choice(name="flor", value="flor"),
    app_commands.Choice(name="contraflor", value="contraflor"),
    app_commands.Choice(name="truco", value="truco"),
    app_commands.Choice(name="retruco", value="retruco"),
    app_commands.Choice(name="vale cuatro", value="vale_cuatro"),
])
async def cantar(interaction: discord.Interaction, canto: str):
    partida = partidas.get(interaction.user.id)
    if not partida:
        await interaction.response.send_message("Primero tenés que poner `/jugar bot`", ephemeral=True)
        return

    if canto == "envido":
        await interaction.response.send_message(
            f"🎲 {interaction.user.mention} cantó **¡ENVIDO!** (2 puntos)\n"
            f"👉 Tu envido: **{partida['envido']}**\n"
            f"🤖 Bot tiene: **{partida['envido_bot']}**\n"
            f"{'¡GANASTE 2 PUNTOS!' if partida['envido'] > partida['envido_bot'] else '¡PERDISTE EL ENVIDO!'}\n"
            f"Respondé con `/quiero` o `/no-quiero`"
        )
    elif canto == "real_envido":
        await interaction.response.send_message(f"💰 {interaction.user.mention} cantó **¡REAL ENVIDO!** (3 puntos) - Tu envido: {partida['envido']}")
    elif canto == "falta_envido":
        await interaction.response.send_message(f"🔥 {interaction.user.mention} cantó **¡FALTA ENVIDO!** - Lo que falta para ganar - Tu envido: {partida['envido']}")
    elif canto == "flor":
        if not tiene_flor(partida['mano']):
            await interaction.response.send_message(f"❌ {interaction.user.mention} ¡No tenés flor! Son palos distintos", ephemeral=True)
            return
        await interaction.response.send_message(f"🌸 {interaction.user.mention} cantó **¡FLOR!** - 3 puntos + la jugada")
    elif canto == "truco":
        await interaction.response.send_message(f"😤 {interaction.user.mention} cantó **¡TRUCO!** (2 puntos) - Respondé `/quiero` o `/no-quiero`")
    elif canto == "retruco":
        await interaction.response.send_message(f"😡 {interaction.user.mention} cantó **¡RETRUCO!** (3 puntos)")
    elif canto == "vale_cuatro":
        await interaction.response.send_message(f"🤬 {interaction.user.mention} cantó **¡VALE CUATRO!** (4 puntos)")

@tree.command(name="quiero", description="Aceptar")
async def quiero(interaction: discord.Interaction):
    await interaction.response.send_message(f"✅ {interaction.user.mention} dijo **¡QUIERO!** Sigue la mano")

@tree.command(name="no-quiero", description="Rechazar")
async def noquiero(interaction: discord.Interaction):
    await interaction.response.send_message(f"❌ {interaction.user.mention} dijo **¡NO QUIERO!** - Gana los puntos el que cantó")

@tree.command(name="irse", description="Irse al mazo")
async def irse(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏃 {interaction.user.mention} se fue al mazo... ¡Cagón! Pierde los puntos")

@tree.command(name="tirar", description="Tirar una carta (1, 2 o 3)")
@app_commands.describe(numero="1 es tu primer carta, 2 la segunda, 3 la tercera")
async def tirar(interaction: discord.Interaction, numero: int):
    partida = partidas.get(interaction.user.id)
    if not partida or numero < 1 or numero > 3:
        await interaction.response.send_message("Usá `/jugar bot` primero y tirá 1, 2 o 3", ephemeral=True)
        return
    carta = partida['mano'][numero-1]
    ruta = foto_carta(carta[0], carta[1])
    archivo = [discord.File(ruta)] if ruta and os.path.exists(ruta) else []
    await interaction.response.send_message(
        f"🃏 {interaction.user.mention} tiró **{carta[0]} de {carta[1]}** (Valor truco: {valor_truco_carta(carta[0], carta[1])})",
        files=archivo
    )

@bot.event
async def on_ready():
    await tree.sync()
    print("Bot truco completo listo!")

bot.run(os.getenv("DISCORD_TOKEN") or "TU_TOKEN")

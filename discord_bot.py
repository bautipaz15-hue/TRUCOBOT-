from flask import Flask
import threading
import os
import discord
from discord.ext import commands
from discord import app_commands
import random

# === TRUCO PARA RENDER (puerto falso) ===
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot de Truco prendido!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# === BOT DE DISCORD ===
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

CARTAS = ["1 Espada", "1 Basto", "7 Espada", "7 Oro", "3", "2", "12", "11", "10", "7", "6", "5", "4"]

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos")
    except Exception as e:
        print(e)

@bot.tree.command(name="truco", description="Jugar al truco contra el bot")
async def truco(interaction: discord.Interaction):
    mano_bot = random.sample(CARTAS, 3)
    mano_tuya = random.sample(CARTAS, 3)
    
    embed = discord.Embed(title="🃏 ¡TRUCO!", color=0x00ff00)
    embed.add_field(name="Tu mano", value="\n".join(mano_tuya), inline=True)
    embed.add_field(name="Mano del bot", value="???\n???\n???", inline=True)
    embed.add_field(name="Accion", value="¿Que queres hacer?", inline=False)
    
    view = TrucoView(mano_tuya, mano_bot)
    await interaction.response.send_message(embed=embed, view=view)

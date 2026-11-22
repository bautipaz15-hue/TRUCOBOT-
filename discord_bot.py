import os
import discord
from discord.ext import commands
from flask import Flask
import threading
from discord import app_commands
import random

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Truco ON"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Conectado como {bot.user}")
    try:
        await bot.tree.sync()
        print("Comandos sincronizados")
    except Exception as e:
        print(e)

@bot.tree.command(name="ping", description="Prueba el bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! Live!")

@bot.tree.command(name="truco", description="Jugar al truco vs bot")
async def truco_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(f"🃏 Tu mano: {random.randint(1,7)} de Espada, {random.randint(1,7)} de Oro, 3 de Basto. Deci TRUCO!")

TOKEN = os.environ.get("DISCORD_TOKEN")
print("Iniciando bot...")
bot.run(TOKEN)

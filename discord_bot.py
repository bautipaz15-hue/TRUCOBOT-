from flask import Flask
from threading import Thread

app = Flask(__name__)
@app.route('/')
def home(): return "Bot vivo!"

def run_web():
    app.run(host="0.0.0.0", port=10000)

Thread(target=run_web, daemon=True).start()
import discord
from discord.ext import commands
import os
import random

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"TRUCOBOT online como {bot.user}")

@bot.command(name="truco")
async def truco(ctx, rival: discord.Member = None):
    if rival is None:
        await ctx.send("Usa `!truco @amigo` para desafiar")
        return
    embed = discord.Embed(title="🇦🇷 ¡DESAFÍO TRUCO!", description=f"{ctx.author.mention} desafia a {rival.mention} a un truco", color=0x0099ff)
    embed.set_image(url="https://media.giphy.com/media/l1J9u3TZfpfeDLkD6/giphy.gif")
    await ctx.send(embed=embed)

@bot.command(name="acepto")
async def acepto(ctx):
    await ctx.send(f"{ctx.author.mention} aceptó! Tira con `!tirar 1` `!tirar 2` `!tirar 3`")

@bot.command(name="tirar")
async def tirar(ctx, numero: int = 1):
    cartas = ["1 de Espada 🗡️", "7 de Espada", "3 de Oro", "Ancho de Basto"]
    carta = random.choice(cartas)
    embed = discord.Embed(title=f"{ctx.author.display_name} tiró", description=f"## {carta}", color=0x00ff00)
    embed.set_thumbnail(url="https://i.imgur.com/Qk2Ya6O.png")
    await ctx.send(embed=embed)

@bot.command(name="envido")
async def envido(ctx):
    embed = discord.Embed(title="¡ENVIDO! 🔥", description=f"{ctx.author.mention} cantó ENVIDO", color=0xff0000)
    embed.set_image(url="https://i.imgur.com/3o7aCTn.gif")
    await ctx.send(embed=embed)

@bot.command(name="flor")
async def flor(ctx):
    embed = discord.Embed(title="¡FLOR! 🌸", color=0xff66cc)
    embed.set_image(url="https://i.imgur.com/8Km9tLL.png")
    await ctx.send(f"{ctx.author.mention}", embed=embed)

@bot.command(name="quiero")
async def quiero(ctx):
    await ctx.send(f"{ctx.author.mention} dijo ¡QUIERO! 💪")
@bot.command(name="noquiero")
async def noquiero(ctx):
    await ctx.send(f"{ctx.author.mention} dijo ¡NO QUIERO! 😤")

bot.run(os.getenv("DISCORD_TOKEN"))

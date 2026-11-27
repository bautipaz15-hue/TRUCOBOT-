import discord
from discord import app_commands
import os
intents=discord.Intents.default()
bot=discord.Client(intents=intents)
tree=app_commands.CommandTree(bot)
@tree.command(name="tienda",description="test")
async def tienda(i:discord.Interaction):
    await i.response.send_message("TIENDA ANDA")
@bot.event
async def on_ready():
    await tree.sync()
    print("SYNC TEST OK")
bot.run(os.getenv("DISCORD_TOKEN"))

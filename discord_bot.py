import discord
from discord.ext import commands
import random
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

MAZO = [("1 de Espada 🗡️",14), ("1 de Basto 🌿",10), ("7 de Espada 🗡️",13), ("7 de Oro 💰",13), ("3",12), ("2",11), ("12 Rey 👑",8), ("4",1)]
def repartir(n=3):
    m = MAZO.copy(); random.shuffle(m); return m[:n]
partidas = {}

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos slash - /truco activo!")
    except Exception as e:
        print(e)
    print(f'Conectado como {bot.user}')

# --- COMANDOS CON / ---
@bot.tree.command(name="truco", description="Jugar al truco solo vs BOT o con amigo")
async def truco_slash(interaction: discord.Interaction, oponente: discord.Member = None):
    mano1 = repartir(); mano2 = repartir()
    partidas[interaction.channel_id] = {"p1": interaction.user, "mano1": mano1, "mano2": mano2}
    
    if oponente is None:
        msg = f"🎮 **{interaction.user.mention} vs 🤖 BOT Truco!**"
    else:
        msg = f"🎮 **{interaction.user.mention} desafía a {oponente.mention}!**"
    
    cartas_txt = "\n".join([f"{i+1}. {c[0]}" for i, c in enumerate(mano1)])
    embed = discord.Embed(title="🃏 Partida Iniciada! /truco", color=0x00ff00, description=msg)
    embed.add_field(name="Tus cartas", value=cartas_txt)
    embed.set_footer(text="Tirá escribiendo 1, 2 o 3 en el chat")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="tirar", description="Tirar una carta")
async def tirar_slash(interaction: discord.Interaction, numero: int = 1):
    carta = random.choice(MAZO)
    await interaction.response.send_message(f"🃏 **{interaction.user.display_name} tiró {carta[0]}**")

@bot.tree.command(name="envido", description="Cantar envido")
async def envido_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f"🔥 **{interaction.user.mention} dice ¡ENVIDO!**")

@bot.tree.command(name="flor", description="Cantar flor")
async def flor_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f"🌸 **{interaction.user.mention} cantó ¡FLOR!**")

@bot.tree.command(name="quiero", description="Aceptar")
async def quiero_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f"✅ **{interaction.user.mention} dice ¡QUIERO!**")

@bot.tree.command(name="noquiero", description="Rechazar")
async def noquiero_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f"❌ **{interaction.user.mention} dice ¡NO QUIERO!**")

# --- LÓGICA PARA JUGAR CON 1,2,3 (sigue igual) ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id in partidas and message.content.strip() in ["1","2","3"]:
        p = partidas[message.channel.id]
        if message.author.id != p["p1"].id: return
        idx = int(message.content.strip())-1
        if idx >= len(p["mano1"]):
            await message.channel.send("Esa ya la usaste!"); return
        carta_yo = p["mano1"].pop(idx)
        carta_bot = p["mano2"].pop(random.randrange(len(p["mano2"])))
        res = "Ganaste vos! 🔥" if carta_yo[1] > carta_bot[1] else "Gana el BOT! 🤖" if carta_yo[1] < carta_bot[1] else "Parda!"
        await message.channel.send(f"**Vos:** {carta_yo[0]} VS **BOT:** {carta_bot[0]}\n**{res}**")
        if not p["mano1"]:
            await message.channel.send(f"🏁 ¡Fin! Hacé /truco de nuevo {p['p1'].mention}")
            del partidas[message.channel.id]
        else:
            restantes = "\n".join([f"{i+1}. {c[0]}" for i, c in enumerate(p["mano1"])])
            await message.channel.send(f"Te quedan:\n{restantes}")
    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))

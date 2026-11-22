import discord
from discord import app_commands

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# --- COMANDO /jugar ---
@tree.command(name="jugar", description="Jugar al truco: vs bot o vs amigo")
@app_commands.describe(oponente="Escribí 'bot' o menciona @Pepito")
async def jugar(interaction: discord.Interaction, oponente: str):
    
    # Si pone /jugar bot
    if oponente.lower() == "bot":
        await interaction.response.send_message(
            f"🤖 **Partida vs BOT creada**\n"
            f"Jugador: {interaction.user.mention}\n"
            f"Tus cartas: 1 de Espada, 7 de Oro, 3 de Basto\n"
            f"Usá `/cantar truco` o `/cantar envido`"
        )
    # Si pone /jugar @Pepito
    else:
        await interaction.response.send_message(
            f"🔥 **DESAFÍO TRUQUERO**\n"
            f"{interaction.user.mention} desafió a {oponente} a un truco!\n"
            f"{oponente} aceptá con `/quiero`"
        )

# --- COMANDO /cantar ---
@tree.command(name="cantar", description="Cantar en el truco")
@app_commands.describe(canto="Qué querés cantar")
@app_commands.choices(canto=[
    app_commands.Choice(name="envido", value="envido"),
    app_commands.Choice(name="real envido", value="real_envido"),
    app_commands.Choice(name="falta envido", value="falta_envido"),
    app_commands.Choice(name="flor", value="flor"),
    app_commands.Choice(name="rosa 🌹", value="rosa"),
    app_commands.Choice(name="truco", value="truco"),
    app_commands.Choice(name="retruco", value="retruco"),
    app_commands.Choice(name="vale cuatro", value="vale_cuatro"),
])
async def cantar(interaction: discord.Interaction, canto: str):
    mapa = {
        "envido": "¡ENVIDO!",
        "real_envido": "¡REAL ENVIDO!",
        "falta_envido": "¡FALTA ENVIDO!",
        "flor": "¡FLOR!",
        "rosa": "¡ROSA! 🌹",
        "truco": "¡TRUCO!",
        "retruco": "¡RETRUCO!",
        "vale_cuatro": "¡VALE CUATRO!"
    }
    await interaction.response.send_message(f"{interaction.user.mention} cantó **{mapa[canto]}** Responde con `/quiero` o `/no-quiero`")

@tree.command(name="quiero", description="Aceptar canto")
async def quiero(interaction: discord.Interaction):
    await interaction.response.send_message(f"✅ {interaction.user.mention} dijo ¡QUIERO!")

@tree.command(name="no-quiero", description="Rechazar canto")
async def noquiero(interaction: discord.Interaction):
    await interaction.response.send_message(f"❌ {interaction.user.mention} dijo ¡NO QUIERO!")

@tree.command(name="irse", description="Irse al mazo")
async def irse(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏃 {interaction.user.mention} se fue al mazo")

@bot.event
async def on_ready():
    await tree.sync()
    print("Bot de truco listo!")

bot.run("TU_TOKEN")

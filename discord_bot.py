import discord
from discord import app_commands
import random, os
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
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)
partidas = {}
partidas_amigos = {}

NOMBRES_BOTS = ["Don Ramon","Messi","El Mago","Cacho"]
TABLERO_PATH = "Tablero.jpg"

PALOS = ["espada","basto","oro","copa"]
NUMEROS = [1,2,3,4,5,6,7,10,11,12]

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

class CartaButton(discord.ui.Button):
    def __init__(self,carta,owner):
        self.carta=carta; self.owner=owner
        super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary,row=0)
    async def callback(self,interaction: discord.Interaction):
        if interaction.user.id!=self.owner:
            await interaction.response.send_message("No es tu partida",ephemeral=True)
            return
        await interaction.response.send_message(f"Tiraste {self.carta[0]} de {self.carta[1]}",ephemeral=False)

class SalirButton(discord.ui.Button):
    def __init__(self,owner):
        self.owner=owner
        super().__init__(label="SALIR",style=discord.ButtonStyle.secondary,row=1)
    async def callback(self,interaction: discord.Interaction):
        if interaction.user.id!=self.owner:
            await interaction.response.send_message("No es tu partida",ephemeral=True)
            return
        partidas.pop(self.owner,None)
        for c in self.view.children: c.disabled=True
        await interaction.response.edit_message(content="Se retiro.",view=self.view)

class MesaView(discord.ui.View):
    def __init__(self,owner,mano):
        super().__init__(timeout=600)
        for carta in mano: self.add_item(CartaButton(carta,owner))
        self.add_item(SalirButton(owner))

class MesaAmigosView(discord.ui.View):
    def __init__(self,j1,j2,mano):
        super().__init__(timeout=600)
        self.j1=j1; self.j2=j2; self.turno=j1
        for carta in mano: self.add_item(CartaAmigoButton(carta,j1,j2,self))
        self.add_item(SalirAmigoButton(j1,j2))

class CartaAmigoButton(discord.ui.Button):
    def __init__(self,carta,j1,j2,parent):
        self.carta=carta; self.j1=j1; self.j2=j2; self.parent=parent
        super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary,row=0)
    async def callback(self,interaction: discord.Interaction):
        if interaction.user.id not in [self.j1,self.j2]:
            await interaction.response.send_message("No sos parte",ephemeral=True)
            return
        if interaction.user.id!=self.parent.turno:
            await interaction.response.send_message("No es tu turno!",ephemeral=True)
            return
        self.parent.turno=self.j2 if interaction.user.id==self.j1 else self.j1
        await interaction.response.send_message(f"{interaction.user.mention} tiro {self.carta[0]} de {self.carta[1]}",ephemeral=False)

class SalirAmigoButton(discord.ui.Button):
    def __init__(self,j1,j2):
        self.j1=j1; self.j2=j2
        super().__init__(label="SALIR",style=discord.ButtonStyle.secondary,row=1)
    async def callback(self,interaction: discord.Interaction):
        if interaction.user.id not in [self.j1,self.j2]:
            await interaction.response.send_message("No sos parte",ephemeral=True)
            return
        for c in self.view.children: c.disabled=True
        await interaction.response.edit_message(content="Abandono.",view=self.view)

@tree.command(name="jugar",description="Jugar truco vs bot")
async def jugar(interaction: discord.Interaction):
    mazo=[(n,p) for p in PALOS for n in NUMEROS]
    random.shuffle(mazo)
    mano=[mazo.pop() for _ in range(3)]
    partidas[interaction.user.id]={"mano":mano,"envido":calcular_envido(mano)}
    nombre=random.choice(NOMBRES_BOTS)
    embed=discord.Embed(title="MESA TRUCO 1v1",description=f"{nombre} VS {interaction.user.mention} Envido {partidas[interaction.user.id]['envido']}",color=0x1e8449)
    embed.set_author(name=f"{nombre} BOT")
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    view=MesaView(interaction.user.id,mano)
    await interaction.response.send_message(embed=embed,view=view)

@tree.command(name="desafiar",description="Desafia a un amigo")
async def desafiar(interaction: discord.Interaction,amigo: discord.Member):
    if amigo.bot or amigo.id==interaction.user.id:
        await interaction.response.send_message("Amigo invalido",ephemeral=True)
        return
    mazo=[(n,p) for p in PALOS for n in NUMEROS]
    random.shuffle(mazo)
    mano=[mazo.pop() for _ in range(3)]
    partidas_amigos[f"{interaction.user.id}_{amigo.id}"]=mano
    embed=discord.Embed(title="MESA AMIGOS",description=f"{interaction.user.display_name} VS {amigo.display_name} Turno {interaction.user.mention}",color=0x3498db)
    embed.set_thumbnail(url=amigo.display_avatar.url)
    embed.set_footer(text=f"{interaction.user.display_name}",icon_url=interaction.user.display_avatar.url)
    view=MesaAmigosView(interaction.user.id,amigo.id,mano)
    await interaction.response.send_message(content=f"{amigo.mention} te desafiaron!",embed=embed,view=view)

@bot.event
async def on_ready():
    await tree.sync()
    print("Bot listo!")

bot.run(os.getenv("DISCORD_TOKEN") or "TOKEN")

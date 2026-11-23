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

TIENDA_TABLEROS = {
    "boca": {"nombre": "Boca", "precio": 100, "keyword": "boca"},
    "river": {"nombre": "River", "precio": 100, "keyword": "river"},
    "racing": {"nombre": "Racing", "precio": 100, "keyword": "racing"},
    "casla": {"nombre": "San Lorenzo", "precio": 100, "keyword": "san_lorenzo"},
    "oro": {"nombre": "Oro", "precio": 500, "keyword": "oro"},
    "diamante": {"nombre": "Diamante", "precio": 1000, "keyword": "diamante"},
    "fnaf": {"nombre": "FNAF Springtrap", "precio": 1500, "keyword": "springtrap"},
}

CODIGOS = {
    "navidad_se_acerca": {"tipo": "trucoins", "valor": 500, "desc": "500 Trucoins"},
    "gaming": {"tipo": "tablero", "valor": "neon", "desc": "Tablero Gamer Neon EXCLUSIVO"},
    "truco!": {"tipo": "poder", "valor": "random", "desc": "1 Poder Random"},
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
    data = cargar_usuarios()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"wins":0, "losses":0, "trucoins":300, "tableros":["default"], "equipado":"default", "poderes":[], "codigos_usados":[]}
        guardar_usuarios(data)
    if "poderes" not in data[uid]: data[uid]["poderes"] = []
    if "codigos_usados" not in data[uid]: data[uid]["codigos_usados"] = []
    if "trucoins" not in data[uid]: data[uid]["trucoins"] = 300
    if "tableros" not in data[uid]: data[uid]["tableros"] = ["default"]
    return data[uid], data

def buscar_archivo_tablero(keyword):
    carpeta = "tableros"
    if keyword == "default" or keyword == "madera":
        return "Tablero.jpg" if os.path.exists("Tablero.jpg") else None
    if not os.path.exists(carpeta):
        return "Tablero.jpg" if os.path.exists("Tablero.jpg") else None
    keyword = keyword.lower()
    for archivo in os.listdir(carpeta):
        if keyword in archivo.lower():
            return os.path.join(carpeta, archivo)
    return None

def get_tablero_path_user(user_id):
    usuario, _ = get_or_create_user(user_id)
    equipado = usuario.get("equipado", "default")
    # FIX RIVER: default es madera, NUNCA boca
    if equipado == "default":
        return "Tablero.jpg" if os.path.exists("Tablero.jpg") else None
    if equipado == "neon":
        p = buscar_archivo_tablero("gamer")
        return p if p else "Tablero.jpg"
    info = TIENDA_TABLEROS.get(equipado)
    if info:
        p = buscar_archivo_tablero(info["keyword"])
        return p if p else "Tablero.jpg"
    p = buscar_archivo_tablero(equipado)
    return p if p else "Tablero.jpg"

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

# --- BOTONES CON BOT QUE RESPONDE ---
class CartaButton(discord.ui.Button):
    def __init__(self,carta,owner):
        self.carta=carta; self.owner=owner
        super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary,row=0)
    async def callback(self,interaction: discord.Interaction):
        if interaction.user.id!=self.owner:
            await interaction.response.send_message("No es tu partida",ephemeral=True); return
        
        # Desactivar la carta usada
        self.disabled = True
        self.label = f"✓ {self.carta[0]} de {self.carta[1]}"
        
        data_partida = partidas.get(self.owner)
        if not data_partida or not data_partida["bot"]:
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send(f"Tiraste {self.carta[0]} de {self.carta[1]}")
            return

        # Bot juega
        carta_bot = data_partida["bot"].pop(0)
        data_partida["jugadas"].append((self.carta, carta_bot))
        
        frases_bot = [f"Yo tiro {carta_bot[0]} de {carta_bot[1]} 😎", f"Toma: {carta_bot[0]} de {carta_bot[1]}", f"{carta_bot[0]} de {carta_bot[1]} y te gano"]
        
        await interaction.response.edit_message(view=self.view)
        await interaction.followup.send(f"**Vos:** {self.carta[0]} de {self.carta[1]}\n**{data_partida['nombre']}:** {random.choice(frases_bot)}")

class TrucoButton(discord.ui.Button):
    def __init__(self,owner):
        self.owner=owner
        super().__init__(label="TRUCO 🔥",style=discord.ButtonStyle.danger,row=1)
    async def callback(self,interaction: discord.Interaction):
        if interaction.user.id!=self.owner: await interaction.response.send_message("No es tu partida",ephemeral=True); return
        await interaction.response.send_message(f"{interaction.user.mention} cantó TRUCO! 🔥")

class EnvidoButton(discord.ui.Button):
    def __init__(self,owner):
        self.owner=owner
        super().__init__(label="ENVIDO 💰",style=discord.ButtonStyle.success,row=1)
    async def callback(self,interaction: discord.Interaction):
        if interaction.user.id!=self.owner: await interaction.response.send_message("No es tu partida",ephemeral=True); return
        env = partidas.get(self.owner, {}).get("envido", 0)
        await interaction.response.send_message(f"{interaction.user.mention} cantó ENVIDO! Tengo {env}")

class ExpresionesButton(discord.ui.Button):
    def __init__(self,owner):
        self.owner=owner
        super().__init__(label="😎 Expresiones",style=discord.ButtonStyle.secondary,row=2)
    async def callback(self,interaction: discord.Interaction):
        if interaction.user.id!=self.owner: await interaction.response.send_message("No es tu partida",ephemeral=True); return
        await interaction.response.send_message("Elegí tu bardo:", view=ExpresionesView(self.owner), ephemeral=True)

class SalirButton(discord.ui.Button):
    def __init__(self,owner):
        self.owner=owner
        super().__init__(label="SALIR",style=discord.ButtonStyle.secondary,row=2)
    async def callback(self,interaction: discord.Interaction):
        if interaction.user.id!=self.owner: await interaction.response.send_message("No es tu partida",ephemeral=True); return
        partidas.pop(self.owner,None)
        for c in self.view.children: c.disabled=True
        await interaction.response.edit_message(content="Te retiraste cagón.",view=self.view)

class MesaView(discord.ui.View):
    def __init__(self,owner,mano):
        super().__init__(timeout=600)
        for carta in mano: self.add_item(CartaButton(carta,owner))
        self.add_item(TrucoButton(owner)); self.add_item(EnvidoButton(owner))
        self.add_item(ExpresionesButton(owner)); self.add_item(SalirButton(owner))

class CartaAmigoButton(discord.ui.Button):
    def __init__(self,carta,j1,j2,parent):
        self.carta=carta; self.j1=j1; self.j2=j2; self.parent=parent
        super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary,row=0)
    async def callback(self,interaction: discord.Interaction):
        if interaction.user.id not in [self.j1,self.j2]: await interaction.response.send_message("No sos parte",ephemeral=True); return
        if interaction.user.id!=self.parent.turno: await interaction.response.send_message("No es tu turno!",ephemeral=True); return
        self.disabled=True
        self.parent.turno=self.j2 if interaction.user.id==self.j1 else self.j1
        await interaction.response.edit_message(view=self.parent)
        await interaction.followup.send(f"{interaction.user.mention} tiro {self.carta[0]} de {self.carta[1]} - Turno <@{self.parent.turno}>")

class MesaAmigosView(discord.ui.View):
    def __init__(self,j1,j2,mano):
        super().__init__(timeout=600)
        self.j1=j1; self.j2=j2; self.turno=j1
        for carta in mano: self.add_item(CartaAmigoButton(carta,j1,j2,self))

class ExpButton(discord.ui.Button):
    def __init__(self,text,label,owner):
        self.text=text; self.owner=owner
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
    async def callback(self,interaction: discord.Interaction):
        if interaction.user.id!=self.owner: await interaction.response.send_message("No es tu partida",ephemeral=True); return
        await interaction.response.send_message(f"**{interaction.user.display_name} dice:** {self.text}", ephemeral=False)

class ExpresionesView(discord.ui.View):
    def __init__(self,owner):
        super().__init__(timeout=120)
        self.add_item(ExpButton("¡Apurate que me duermo! 😴","😴 Me duermo",owner))
        self.add_item(ExpButton("¿Estás buscando en goggle como se juega? 🤓","🤓 Google?",owner))
        self.add_item(ExpButton("XD","XD",owner))
        self.add_item(ExpButton("LOL","LOL",owner))
        self.add_item(ExpButton("JAJAJA 😂","😂 JAJA",owner))

@tree.command(name="jugar",description="Jugar truco vs bot")
async def jugar(interaction: discord.Interaction):
    mazo=[(n,p) for p in PALOS for n in NUMEROS]
    random.shuffle(mazo)
    mano_jugador=[mazo.pop() for _ in range(3)]
    mano_bot=[mazo.pop() for _ in range(3)]
    nombre=random.choice(NOMBRES_BOTS)
    partidas[interaction.user.id]={"jugador":mano_jugador, "bot":mano_bot, "envido":calcular_envido(mano_jugador), "nombre":nombre, "jugadas":[]}
    tablero_path = get_tablero_path_user(interaction.user.id)
    embed=discord.Embed(title="MESA TRUCO 1v1",description=f"{nombre} VS {interaction.user.mention} Envido {partidas[interaction.user.id]['envido']}",color=0x1e8449)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    view=MesaView(interaction.user.id,mano_jugador)
    if tablero_path and os.path.exists(tablero_path):
        file = discord.File(tablero_path, filename="tablero.jpg")
        embed.set_image(url="attachment://tablero.jpg")
        await interaction.response.send_message(embed=embed, view=view, file=file)
    else:
        await interaction.response.send_message(embed=embed,view=view)

@tree.command(name="desafiar",description="Desafia a un amigo")
async def desafiar(interaction: discord.Interaction,amigo: discord.Member):
    if amigo.bot or amigo.id==interaction.user.id:
        await interaction.response.send_message("Amigo invalido",ephemeral=True); return
    mazo=[(n,p) for p in PALOS for n in NUMEROS]
    random.shuffle(mazo)
    mano=[mazo.pop() for _ in range(3)]
    tablero_j1 = get_tablero_path_user(interaction.user.id)
    embed=discord.Embed(title="MESA AMIGOS",description=f"{interaction.user.display_name} VS {amigo.display_name} Turno {interaction.user.mention}",color=0x3498db)
    embed.set_thumbnail(url=amigo.display_avatar.url)
    view=MesaAmigosView(interaction.user.id,amigo.id,mano)
    if tablero_j1 and os.path.exists(tablero_j1):
        file = discord.File(tablero_j1, filename="tablero.jpg")
        embed.set_image(url="attachment://tablero.jpg")
        await interaction.response.send_message(content=f"{amigo.mention} te desafiaron!",embed=embed,view=view,file=file)
    else:
        await interaction.response.send_message(content=f"{amigo.mention} te desafiaron!",embed=embed,view=view)

@tree.command(name="tienda", description="Ver tienda con imagen de tableros")
async def tienda(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.followup.send("🏪 **TIENDA TRUCOBOT** - /equipar river para ser de River")
    for key, item in TIENDA_TABLEROS.items():
        path = buscar_archivo_tablero(item["keyword"])
        if path and os.path.exists(path):
            file = discord.File(path, filename=f"{key}.jpg")
            embed = discord.Embed(title=f"{item['nombre']}", description=f"Precio: {item['precio']} Trucoins\n/equipar {key}", color=0xf1c40f)
            embed.set_image(url=f"attachment://{key}.jpg")
            await interaction.followup.send(embed=embed, file=file)
    path_gamer = buscar_archivo_tablero("gamer")
    if path_gamer and os.path.exists(path_gamer):
        file = discord.File(path_gamer, filename="gamer.jpg")
        embed = discord.Embed(title="GAMER NEON - EXCLUSIVO CÓDIGO", description="Solo con /codigos gaming", color=0xe74c3c)
        embed.set_image(url="attachment://gamer.jpg")
        await interaction.followup.send(embed=embed, file=file)

@tree.command(name="ranking", description="Ver ranking")
async def ranking(interaction: discord.Interaction):
    data = cargar_usuarios()
    if not data: await interaction.response.send_message("Aún no hay datos", ephemeral=True); return
    orden = sorted(data.items(), key=lambda x: x[1].get("wins",0), reverse=True)
    texto = "🏆 **RANKING TRUCOBOT**\n\n"
    for i, (uid, info) in enumerate(orden[:10], 1):
        texto += f"{i}. <@{uid}> - {info.get('wins',0)}W / {info.get('losses',0)}L - {info.get('trucoins',0)} TC\n"
    texto += f"\n💀 Peor: <@{orden[-1][0]}> con {orden[-1][1].get('losses',0)} derrotas"
    await interaction.response.send_message(texto)

@tree.command(name="equipar", description="Equipar un tablero")
async def equipar(interaction: discord.Interaction, tablero: str):
    tablero = tablero.lower()
    usuario, all_data = get_or_create_user(interaction.user.id)
    if tablero not in usuario["tableros"] and tablero != "default":
        if tablero in TIENDA_TABLEROS:
            precio = TIENDA_TABLEROS[tablero]["precio"]
            if usuario["trucoins"] < precio:
                await interaction.response.send_message(f"Te faltan TC. Tenés {usuario['trucoins']} y cuesta {precio}", ephemeral=True); return
            usuario["trucoins"] -= precio
            usuario["tableros"].append(tablero)
        elif tablero == "neon":
            await interaction.response.send_message(f"El tablero neon es exclusivo con /codigos gaming", ephemeral=True); return
        else:
            await interaction.response.send_message(f"No tenés ese tablero. Usa /tienda o /codigos", ephemeral=True); return
    usuario["equipado"] = tablero
    all_data[str(interaction.user.id)] = usuario
    guardar_usuarios(all_data)
    path = get_tablero_path_user(interaction.user.id)
    if path and os.path.exists(path):
        file = discord.File(path, filename="tablero.jpg")
        embed = discord.Embed(title=f"Equipaste {tablero} - AGUANTE RIVER" if tablero=="river" else f"Equipaste {tablero}", color=0x2ecc71)
        embed.set_image(url="attachment://tablero.jpg")
        await interaction.response.send_message(embed=embed, file=file)
    else:
        await interaction.response.send_message(f"Equipaste {tablero}")

@tree.command(name="codigos", description="Canjear un código")
async def codigos(interaction: discord.Interaction, codigo: str):
    codigo = codigo.lower()
    usuario, all_data = get_or_create_user(interaction.user.id)
    if codigo not in CODIGOS:
        await interaction.response.send_message(f"❌ Código `{codigo}` no existe", ephemeral=True); return
    if codigo in usuario.get("codigos_usados", []):
        await interaction.response.send_message(f"❌ Ya usaste `{codigo}`", ephemeral=True); return
    info = CODIGOS[codigo]
    if info["tipo"] == "trucoins":
        usuario["trucoins"] += info["valor"]
        texto = f"✅ Canjeaste `{codigo}` - Ganaste {info['valor']} Trucoins! Ahora tenés {usuario['trucoins']}"
    elif info["tipo"] == "tablero":
        if info["valor"] not in usuario["tableros"]:
            usuario["tableros"].append(info["valor"])
        usuario["equipado"] = info["valor"]
        texto = f"✅ Canjeaste `{codigo}` - Desbloqueaste {info['valor'].upper()}!"
    elif info["tipo"] == "poder":
        poder = random.choice(PODERES_DISPONIBLES)
        usuario["poderes"].append(poder)
        texto = f"✅ Canjeaste `{codigo}` - Ganaste poder: **{poder}**"
    usuario["codigos_usados"].append(codigo)
    all_data[str(interaction.user.id)] = usuario
    guardar_usuarios(all_data)
    await interaction.response.send_message(texto)

@tree.command(name="custom", description="Mandar mensaje custom")
async def custom(interaction: discord.Interaction, mensaje: str):
    await interaction.response.send_message(f"**{interaction.user.display_name} dice:** {mensaje}")

@bot.event
async def on_ready():
    await tree.sync()
    print("Bot V3.1 FIX RIVER listo")

bot.run(os.getenv("DISCORD_TOKEN"))

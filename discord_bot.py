import discord
from discord import app_commands
import random, os, json
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Truco"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
Thread(target=run, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

partidas = {}
NOMBRES = ["Don Ramon","Messi","El Mago"]
PALOS = ["espada","basto","oro","copa"]
NUMEROS = [1,2,3,4,5,6,7,10,11,12]
FILE = "usuarios.json"

def load_u():
    if not os.path.exists(FILE): return {}
    try: return json.load(open(FILE))
    except: return {}
def save_u(d): json.dump(d, open(FILE,"w"), indent=2)
def get_u(uid):
    data=load_u(); s=str(uid)
    if s not in data:
        data[s]={"wins":0,"trucoins":300,"tableros":["default"],"equipado":"default","codigos":[]}
        save_u(data)
    return data[s], data

def tablero_default():
    if os.path.exists("tableros/Tablero.jpg"): return "tableros/Tablero.jpg"
    if os.path.exists("Tablero.jpg"): return "Tablero.jpg"
    return None

def buscar_tab(kw):
    if os.path.exists("tableros"):
        for f in os.listdir("tableros"):
            if kw.lower() in f.lower(): return os.path.join("tableros",f)
    return None

def tablero_user(uid):
    u,_=get_u(uid)
    eq=u.get("equipado","default")
    if eq=="default": return tablero_default()
    p=buscar_tab(eq)
    return p if p else tablero_default()

def bot_avatar():
    for n in ["bot_rojo.png","bot_rojo.jpg","bot_rojo.pnj"]:
        if os.path.exists(n): return n
        if os.path.exists(f"tableros/{n}"): return f"tableros/{n}"
    return None

def foto_carta(num,palo):
    if not os.path.exists("Cartas_reales"): return None
    for f in os.listdir("Cartas_reales"):
        if str(num) in f and palo[:3] in f.lower(): 
            return os.path.join("Cartas_reales",f)
    return None

VALOR={(1,"espada"):14,(1,"basto"):13,(7,"espada"):12,(7,"oro"):11,3:10,2:9,1:8,12:7,11:6,10:5,7:4,6:3,5:2,4:1}
def valor_c(n,p):
    if (n,p) in VALOR: return VALOR[(n,p)]
    return VALOR.get(n,0)

def envido_calc(cs):
    m=0
    for i in range(3):
        for j in range(i+1,3):
            if cs[i][1]==cs[j][1]:
                a=0 if cs[i][0]>=10 else cs[i][0]
                b=0 if cs[j][0]>=10 else cs[j][0]
                if a+b+20>m: m=a+b+20
    if m==0:
        for n,p in cs:
            v=0 if n>=10 else n
            if v>m: m=v
    return m

class CartaBtn(discord.ui.Button):
    def __init__(self,carta,owner):
        self.carta=carta; self.owner=owner
        super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary,row=0)
    async def callback(self,interaction):
        if interaction.user.id!=self.owner:
            await interaction.response.send_message("No es tu partida",ephemeral=True); return
        self.disabled=True
        data=partidas.get(self.owner)
        if not data: await interaction.response.edit_message(view=self.view); return
        cb=data["bot"].pop(0)
        vy=valor_c(self.carta[0],self.carta[1]); vb=valor_c(cb[0],cb[1])
        if vy>vb: g="🏆 Ganaste!"; data["pj"]+=1
        elif vb>vy: g=f"😢 Gano {data['nombre']}"; data["pb"]+=1
        else: g="🤝 Empate"
        files=[]
        r1=foto_carta(self.carta[0],self.carta[1]); r2=foto_carta(cb[0],cb[1])
        if r1 and os.path.exists(r1): files.append(discord.File(r1,filename="yo.jpg"))
        if r2 and os.path.exists(r2): files.append(discord.File(r2,filename="bot.jpg"))
        fin=len(data["bot"])==0
        if fin:
            for c in self.view.children: c.disabled=True
            py=data["pj"]; pb=data["pb"]
            if py>pb: fin_txt=f"\n🎉 GANASTE {py}-{pb} /jugar"
            elif pb>py: fin_txt=f"\n💀 PERDISTE {pb}-{py} /jugar"
            else: fin_txt=f"\n🤝 EMPATE {py}-{pb}"
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send(f"Vos {self.carta[0]} de {self.carta[1]} vs {cb[0]} de {cb[1]}\n{g}{fin_txt}",files=files or None)
            partidas.pop(self.owner,None)
        else:
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send(f"Vos {self.carta[0]} de {self.carta[1]} vs {cb[0]} de {cb[1]}\n{g}",files=files or None)

class MesaView(discord.ui.View):
    def __init__(self,owner,mano):
        super().__init__(timeout=600)
        for c in mano: self.add_item(CartaBtn(c,owner))

@tree.command(name="jugar",description="Jugar vs bot")
async def jugar(interaction: discord.Interaction):
    mazo=[(n,p) for p in PALOS for n in NUMEROS]; random.shuffle(mazo)
    mj=[mazo.pop() for _ in range(3)]; mb=[mazo.pop() for _ in range(3)]
    nombre=random.choice(NOMBRES)
    partidas[interaction.user.id]={"bot":mb,"nombre":nombre,"pj":0,"pb":0,"env":envido_calc(mj)}
    tab=tablero_default(); av=bot_avatar()
    emb=discord.Embed(title="MESA TRUCO 1v1",description=f"{nombre} VS {interaction.user.mention} Envido {partidas[interaction.user.id]['env']}",color=0x1e8449)
    files=[]
    if tab and os.path.exists(tab): files.append(discord.File(tab,filename="tablero.jpg")); emb.set_image(url="attachment://tablero.jpg")
    if av and os.path.exists(av): files.append(discord.File(av,filename="bot_rojo.jpg")); emb.set_thumbnail(url="attachment://bot_rojo.jpg")
    view=MesaView(interaction.user.id,mj)
    if files: await interaction.response.send_message(embed=emb,view=view,files=files)
    else: await interaction.response.send_message(embed=emb,view=view)

@tree.command(name="desafiar",description="Desafiar amigo")
async def desafiar(interaction: discord.Interaction, amigo: discord.Member):
    if amigo.bot or amigo.id==interaction.user.id:
        await interaction.response.send_message("Amigo invalido",ephemeral=True); return
    mazo=[(n,p) for p in PALOS for n in NUMEROS]; random.shuffle(mazo); mano=[mazo.pop() for _ in range(3)]
    t1=tablero_user(interaction.user.id); t2=tablero_user(amigo.id)
    emb=discord.Embed(title="MESA AMIGOS",description=f"{interaction.user.display_name} VS {amigo.display_name}",color=0x3498db)
    files=[]
    if t1 and os.path.exists(t1): files.append(discord.File(t1,filename="t1.jpg"))
    if t2 and os.path.exists(t2) and t1!=t2: files.append(discord.File(t2,filename="t2.jpg"))
    if files: emb.set_image(url=f"attachment://{files[0].filename}")
    view=MesaView(interaction.user.id,mano)
    await interaction.response.send_message(content=f"{amigo.mention} te desafiaron!",embed=emb,view=view,files=files or None)

@tree.command(name="ayuda",description="Ver comandos")
async def ayuda(interaction: discord.Interaction):
    emb=discord.Embed(title="📖 AYUDA TRUCOBOT",color=0x9b59b6)
    emb.add_field(name="/jugar",value="Vs bot, tablero default en tableros/Tablero.jpg + icono bot_rojo.png. Bloquea cartas al perder.",inline=False)
    emb.add_field(name="/desafiar @amigo",value="Vs amigo, muestra tu tablero y el suyo.",inline=False)
    emb.add_field(name="/tienda /equipar /ranking",value="Tienda y equipar tableros.",inline=False)
    emb.add_field(name="Valor Truco",value="1 espada > 1 basto > 7 espada > 7 oro > 3 > 2 > 1 > 12 > 11 > 10",inline=False)
    await interaction.response.send_message(embed=emb)

@tree.command(name="tienda",description="Tienda")
async def tienda(interaction: discord.Interaction):
    await interaction.response.send_message("🏪 Usa /equipar river, boca, racing, etc")

@tree.command(name="equipar",description="Equipar tablero")
async def equipar(interaction: discord.Interaction, tablero: str):
    tablero=tablero.lower()
    u,data=get_u(interaction.user.id)
    u["equipado"]=tablero; data[str(interaction.user.id)]=u; save_u(data)
    p=tablero_user(interaction.user.id)
    if p and os.path.exists(p):
        f=discord.File(p,filename="tab.jpg")
        e=discord.Embed(title=f"Equipaste {tablero}"); e.set_image(url="attachment://tab.jpg")
        await interaction.response.send_message(embed=e,file=f)
    else: await interaction.response.send_message(f"Equipaste {tablero}")

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing,name="Truco | /ayuda"))
    await tree.sync()
    print("Bot listo")

bot.run(os.getenv("DISCORD_TOKEN"))

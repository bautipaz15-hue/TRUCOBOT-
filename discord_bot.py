import discord, random, os, json
from discord import app_commands
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def h(): return "ok"
Thread(target=lambda: app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000))),daemon=True).start()

intents=discord.Intents.default()
intents.message_content=True
bot=discord.Client(intents=intents)
tree=app_commands.CommandTree(bot)
partidas={}

PALOS=["espada","basto","oro","copa"]
NUMS=[1,2,3,4,5,6,7,10,11,12]
VALOR={(1,"espada"):14,(1,"basto"):13,(7,"espada"):12,(7,"oro"):11,3:10,2:9,1:8,12:7,11:6,10:5,7:4,6:3,5:2,4:1}
def v(n,p): return VALOR.get((n,p),VALOR.get(n,0))

PRECIOS={"river":500,"boca":500,"san lorenzo":500,"sanlorenzo":500,"racing":500,"oro":700,"diamante":1450,"springtrap":650}
FILE="usuarios.json"

def load_u():
 if not os.path.exists(FILE): return {}
 try: return json.load(open(FILE))
 except: return {}
def save_u(d): json.dump(d, open(FILE,"w"), indent=2)
def get_u(uid):
 data=load_u(); s=str(uid)
 if s not in data: data[s]={"coins":0,"equipado":"default","owned":["default"]}
 if "owned" not in data[s]: data[s]["owned"]=["default"]
 return data, s
def add_coins(uid,cant):
 data,s=get_u(uid)
 data[s]["coins"]=data[s].get("coins",0)+cant
 save_u(data); return data[s]["coins"]

def foto(n,p):
 try:
  if not os.path.exists("Cartas_reales"): return None
  n=str(n); p=p.lower()
  for f in os.listdir("Cartas_reales"):
   fl=f.lower()
   if n in fl and (p in fl or p[0] in fl): return os.path.join("Cartas_reales",f)
 except: pass
 return None

def buscar_tablero(nombre):
 if not os.path.exists("tableros"): return None
 nombre=nombre.lower()
 for f in os.listdir("tableros"):
  if nombre in f.lower(): return os.path.join("tableros",f)
 return None

def tab_default(): return "tableros/Tablero.jpg" if os.path.exists("tableros/Tablero.jpg") else None
def tab_user(uid):
 data=load_u(); s=str(uid)
 eq=data.get(s,{}).get("equipado","default")
 if eq=="default": return tab_default()
 t=buscar_tablero(eq)
 return t if t else tab_default()

def av():
 for x in ["bot_rojo.png","tableros/bot_rojo.png"]: 
  if os.path.exists(x): return x
 return None

class C(discord.ui.Button):
 def __init__(self,carta,owner):
  self.carta=carta; self.owner=owner
  super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary,row=0)
 async def callback(self,i):
  if i.user.id!=self.owner: await i.response.send_message("No es tuya",ephemeral=True);return
  d=partidas.get(self.owner)
  if not d or len(d["bot"])==0: return
  self.disabled=True
  cb=d["bot"].pop(0)
  vy=v(self.carta[0],self.carta[1]); vb=v(cb[0],cb[1])
  if vy>vb: txt=f"🏆 GANASTE! {self.carta[0]} de {self.carta[1]} le gana a {cb[0]} de {cb[1]}"; d["pj"]+=1
  elif vb>vy: txt=f"😢 PERDISTE! Bot {cb[0]} de {cb[1]} vs {self.carta[0]}"; d["pb"]+=1
  else: txt=f"🤝 EMPATE {self.carta[0]} vs {cb[0]}"
  fs=[]
  r1=foto(self.carta[0],self.carta[1]); r2=foto(cb[0],cb[1])
  if r1 and os.path.exists(r1): fs.append(discord.File(r1,filename="yo.jpg"))
  if r2 and os.path.exists(r2): fs.append(discord.File(r2,filename="bot.jpg"))
  fin=len(d["bot"])==0
  if fin:
   for c in self.view.children: c.disabled=True
   if d["pj"]>d["pb"]:
    coins=add_coins(self.owner,250)
    txt+=f"\n\n🎉 GANASTE {d['pj']}-{d['pb']} +250 Trucoins! Total: {coins}"
   elif d["pb"]>d["pj"]:
    txt+=f"\n\n💀 PERDISTE {d['pb']}-{d['pj']} +0 coins"
   else:
    txt+=f"\n\n🤝 EMPATE {d['pj']}-{d['pb']}"
   partidas.pop(self.owner,None)
  await i.response.edit_message(view=self.view)
  await i.followup.send(content=txt,files=fs if fs else None)

class T(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="TRUCO",style=discord.ButtonStyle.danger,row=1)
 async def callback(self,i): await i.response.send_message(f"{i.user.mention} TRUCO!")
class E(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="ENVIDO",style=discord.ButtonStyle.success,row=1)
 async def callback(self,i): await i.response.send_message(f"{i.user.mention} ENVIDO!")
class S(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="SALIR",style=discord.ButtonStyle.secondary,row=2)
 async def callback(self,i):
  partidas.pop(self.o,None)
  for c in self.view.children: c.disabled=True
  await i.response.edit_message(content="Saliste - /jugar",view=self.view)
class ExpB(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="Expresiones",style=discord.ButtonStyle.secondary,row=2)
 async def callback(self,i): await i.response.send_message("XD / JAJA / Apurate!",ephemeral=True)

class V(discord.ui.View):
 def __init__(self,o,m):
  super().__init__(timeout=600)
  for c in m: self.add_item(C(c,o))
  self.add_item(T(o)); self.add_item(E(o)); self.add_item(ExpB(o)); self.add_item(S(o))

@tree.command(name="jugar",description="Jugar vs bot - ganas 250")
async def jugar(i:discord.Interaction):
 m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m)
 mj=[m.pop() for _ in range(3)]; mb=[m.pop() for _ in range(3)]
 partidas[i.user.id]={"bot":mb,"pj":0,"pb":0}
 t=tab_user(i.user.id); a=av()
 emb=discord.Embed(title="TRUCO - 250 coins si ganas",description=f"Bot vs {i.user.mention}",color=0x1e8449)
 fs=[]
 if t and os.path.exists(t): fs.append(discord.File(t,filename="t.jpg")); emb.set_image(url="attachment://t.jpg")
 if a and os.path.exists(a): fs.append(discord.File(a,filename="b.jpg")); emb.set_thumbnail(url="attachment://b.jpg")
 await i.response.send_message(embed=emb,view=V(i.user.id,mj),files=fs if fs else None)

@tree.command(name="perfil",description="Ver tus trucoins")
async def perfil(i:discord.Interaction):
 data,s=get_u(i.user.id)
 coins=data.get(s,{}).get("coins",0); eq=data.get(s,{}).get("equipado","default")
 await i.response.send_message(f"💰 {i.user.display_name}: {coins} Trucoins | Tablero equipado: {eq}")

@tree.command(name="tienda",description="Ver tienda")
async def tienda(i:discord.Interaction):
 e=discord.Embed(title="🛒 TIENDA",description="Ganas 250 vs bot, 350 vs amigos",color=0xf1c40f)
 e.add_field(name="River - 500",value="/comprar river",inline=True)
 e.add_field(name="Boca - 500",value="/comprar boca",inline=True)
 e.add_field(name="San Lorenzo - 500",value="/comprar san lorenzo",inline=True)
 e.add_field(name="Racing - 500",value="/comprar racing",inline=True)
 e.add_field(name="Oro - 700",value="/comprar oro",inline=True)
 e.add_field(name="Diamante - 1450",value="/comprar diamante",inline=True)
 e.add_field(name="Springtrap - 650",value="/comprar springtrap",inline=True)
 await i.response.send_message(embed=e)

@tree.command(name="comprar",description="Comprar tablero")
async def comprar(i:discord.Interaction, tablero: str):
 tablero=tablero.lower()
 if tablero not in PRECIOS and tablero.replace(" ","") not in PRECIOS:
  await i.response.send_message("No existe. Usa /tienda"); return
 precio=PRECIOS.get(tablero,PRECIOS.get(tablero.replace(" ",""),0))
 data,s=get_u(i.user.id)
 coins=data[s].get("coins",0)
 if tablero in data[s].get("owned",[]): await i.response.send_message(f"Ya tenes {tablero}"); return
 if coins < precio: await i.response.send_message(f"Te faltan {precio-coins} coins. Tenes {coins}"); return
 data[s]["coins"]-=precio
 if tablero not in data[s]["owned"]: data[s]["owned"].append(tablero)
 save_u(data)
 await i.response.send_message(f"✅ Compraste {tablero} por {precio}! Te quedan {data[s]['coins']} - /equipar {tablero}")

@tree.command(name="equipar",description="Equipar tablero")
async def equipar(i:discord.Interaction, tablero: str):
 tablero=tablero.lower()
 data,s=get_u(i.user.id)
 if tablero!="default" and tablero not in data[s].get("owned",[]):
  await i.response.send_message(f"No tenes {tablero}. /comprar {tablero}"); return
 data[s]["equipado"]=tablero; save_u(data)
 t=tab_user(i.user.id)
 if t and os.path.exists(t):
  await i.response.send_message(f"Equipaste {tablero}",file=discord.File(t,filename="tab.jpg"))
 else: await i.response.send_message(f"Equipaste {tablero}")

@bot.event
async def on_ready():
 await tree.sync()
 print("Final con coins y tienda listo")

bot.run(os.getenv("DISCORD_TOKEN"))

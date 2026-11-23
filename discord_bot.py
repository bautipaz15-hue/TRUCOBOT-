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

PRECIOS={"river":500,"boca":500,"san lorenzo":500,"racing":500,"oro":700,"diamante":1450,"springtrap":650}
CODIGOS={"TRUCO2026":1000,"RIVER2026":500,"BOCA":300}
FILE="usuarios.json"

def load_u():
 if not os.path.exists(FILE): return {}
 try:
  with open(FILE,"r") as f: return json.load(f)
 except: return {}
def save_u(d):
 with open(FILE,"w") as f: json.dump(d,f,indent=2)
def get_u(uid):
 data=load_u(); s=str(uid)
 if s not in data: data[s]={"coins":0,"equipado":"default","owned":["default"],"codigos":[]}
 if "owned" not in data[s]: data[s]["owned"]=["default"]
 if "codigos" not in data[s]: data[s]["codigos"]=[]
 save_u(data)
 return data,s
def add_coins(uid,cant):
 data,s=get_u(uid)
 data=load_u(); s=str(uid)
 if s not in data: data[s]={"coins":0,"equipado":"default","owned":["default"],"codigos":[]}
 data[s]["coins"]=data[s].get("coins",0)+cant
 save_u(data)
 return data[s]["coins"]

def foto(n,p):
 try:
  if not os.path.exists("Cartas_reales"): return None
  for f in os.listdir("Cartas_reales"):
   fl=f.lower()
   if str(n) in fl and p[0] in fl.lower(): return os.path.join("Cartas_reales",f)
 except: pass
 return None

def buscar_tablero(nombre):
 if not os.path.exists("tableros"): return None
 nombre=nombre.lower().replace(" ","")
 for f in os.listdir("tableros"):
  if nombre in f.lower().replace(" ",""): return os.path.join("tableros",f)
 return None

def tab_user(uid):
 data=load_u(); s=str(uid)
 eq=data.get(s,{}).get("equipado","default").lower()
 if eq=="default": 
  return "tableros/Tablero.jpg" if os.path.exists("tableros/Tablero.jpg") else None
 t=buscar_tablero(eq)
 return t if t else "tableros/Tablero.jpg"

def av():
 for x in ["bot_rojo.png","tableros/bot_rojo.png"]:
  if os.path.exists(x): return x
 return None

# --- BOTONES PARTIDA ---
class C(discord.ui.Button):
 def __init__(self,carta,owner):
  self.carta=carta; self.owner=owner
  super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary,row=0)
 async def callback(self,i):
  if i.user.id!=self.owner: await i.response.send_message("No es tuya",ephemeral=True);return
  d=partidas.get(self.owner)
  if not d: return
  self.disabled=True
  cb=d["bot"].pop(0)
  vy=v(self.carta[0],self.carta[1]); vb=v(cb[0],cb[1])
  if vy>vb: res=f"🏆 GANASTE mano!"; d["pj"]+=1
  elif vb>vy: res=f"😢 Perdiste mano"; d["pb"]+=1
  else: res="🤝 Empate"
  res_full=f"Vos {self.carta[0]} de {self.carta[1]} vs Bot {cb[0]} de {cb[1]}\n{res} ({d['pj']}-{d['pb']})"
  fs=[]
  r1=foto(self.carta[0],self.carta[1]); r2=foto(cb[0],cb[1])
  if r1 and os.path.exists(r1): fs.append(discord.File(r1,filename="yo.jpg"))
  if r2 and os.path.exists(r2): fs.append(discord.File(r2,filename="bot.jpg"))
  fin=len(d["bot"])==0
  if fin:
   for c in self.view.children: c.disabled=True
   if d["pj"]>d["pb"]:
    coins=add_coins(self.owner,250)
    res_full+=f"\n\n🎉 GANASTE PARTIDA {d['pj']}-{d['pb']} +250 Trucoins! Total: {coins}"
   elif d["pb"]>d["pj"]:
    res_full+=f"\n\n💀 PERDISTE {d['pb']}-{d['pj']} +0"
   else:
    res_full+=f"\n\n🤝 EMPATE"
   partidas.pop(self.owner,None)
  await i.response.edit_message(view=self.view)
  await i.followup.send(content=res_full,files=fs if fs else None)

class T(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="TRUCO",style=discord.ButtonStyle.danger,row=1)
 async def callback(self,i): await i.response.send_message(f"{i.user.mention} canto TRUCO!")
class E(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="ENVIDO",style=discord.ButtonStyle.success,row=1)
 async def callback(self,i): await i.response.send_message(f"{i.user.mention} canto ENVIDO!")
class S(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="SALIR",style=discord.ButtonStyle.secondary,row=2)
 async def callback(self,i):
  partidas.pop(self.o,None)
  for c in self.view.children: c.disabled=True
  await i.response.edit_message(content="Saliste",view=self.view)
class V(discord.ui.View):
 def __init__(self,o,m):
  super().__init__(timeout=600)
  for c in m: self.add_item(C(c,o))
  self.add_item(T(o)); self.add_item(E(o)); self.add_item(S(o))

# --- TIENDA CON BOTON ---
class ComprarBtn(discord.ui.Button):
 def __init__(self,nombre,precio):
  self.nombre=nombre; self.precio=precio
  super().__init__(label=f"Comprar {nombre} - {precio}",style=discord.ButtonStyle.success)
 async def callback(self,i):
  data,s=get_u(i.user.id)
  data=load_u()
  coins=data[s].get("coins",0)
  owned=data[s].get("owned",[])
  if self.nombre in owned:
   await i.response.send_message(f"Ya tenes {self.nombre} - /equipar {self.nombre}",ephemeral=True); return
  if coins < self.precio:
   await i.response.send_message(f"Te faltan {self.precio-coins} coins. Tenes {coins}",ephemeral=True); return
  data[s]["coins"]-=self.precio
  data[s]["owned"].append(self.nombre)
  save_u(data)
  await i.response.send_message(f"✅ Compraste {self.nombre} por {self.precio}! Te quedan {data[s]['coins']} - /equipar {self.nombre}",ephemeral=True)

class TiendaView(discord.ui.View):
 def __init__(self):
  super().__init__(timeout=120)
  for n,p in PRECIOS.items():
   self.add_item(ComprarBtn(n,p))

# --- COMANDOS ---
@tree.command(name="jugar",description="Jugar vs bot +250 si ganas")
async def jugar(i:discord.Interaction):
 m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m)
 mj=[m.pop() for _ in range(3)]; mb=[m.pop() for _ in range(3)]
 partidas[i.user.id]={"bot":mb,"pj":0,"pb":0}
 t=tab_user(i.user.id); a=av()
 emb=discord.Embed(title="TRUCO - Gana 250 Trucoins",description=f"{i.user.mention} tu mano: {', '.join([f'{c[0]} de {c[1]}' for c in mj])}",color=0x1e8449)
 fs=[]
 if t and os.path.exists(t): fs.append(discord.File(t,filename="t.jpg")); emb.set_image(url="attachment://t.jpg")
 if a and os.path.exists(a): fs.append(discord.File(a,filename="b.jpg")); emb.set_thumbnail(url="attachment://b.jpg")
 await i.response.send_message(embed=emb,view=V(i.user.id,mj),files=fs if fs else None)

@tree.command(name="perfil",description="Ver trucoins")
async def perfil(i:discord.Interaction):
 data,s=get_u(i.user.id)
 await i.response.send_message(f"💰 {i.user.display_name}: {data[s]['coins']} coins | Tablero: {data[s]['equipado']} | Desbloqueados: {', '.join(data[s]['owned'])}")

@tree.command(name="tienda",description="Tienda con fotos y boton comprar")
async def tienda(i:discord.Interaction):
 # Muestra el primer tablero como ejemplo con foto
 # Para ver todos usa los botones
 t=buscar_tablero("river") or tab_user(i.user.id)
 fs=[]
 if t and os.path.exists(t): fs.append(discord.File(t,filename="preview.jpg"))
 e=discord.Embed(title="🛒 TIENDA DE TABLEROS",description="Cada tablero muestra su foto al equiparlo. Ganás 250 vs bot y 350 vs amigos\nRiver 500, Boca 500, San Lorenzo 500, Racing 500, Oro 700, Diamante 1450, Springtrap 650",color=0xf1c40f)
 if fs: e.set_image(url="attachment://preview.jpg")
 await i.response.send_message(embed=e,view=TiendaView(),files=fs if fs else None)

@tree.command(name="comprar",description="Comprar tablero")
async def comprar(i:discord.Interaction, tablero: str):
 tablero=tablero.lower()
 # normalizar precio
 key=tablero
 if key not in PRECIOS:
  for k in PRECIOS:
   if k in key or key in k: key=k; break
 if key not in PRECIOS: await i.response.send_message("No existe. Opciones: river, boca, san lorenzo, racing, oro, diamante, springtrap"); return
 precio=PRECIOS[key]
 data=load_u(); s=str(i.user.id)
 if s not in data: data[s]={"coins":0,"equipado":"default","owned":["default"],"codigos":[]}
 if key in data[s]["owned"]: await i.response.send_message(f"Ya tenes {key}"); return
 if data[s]["coins"] < precio: await i.response.send_message(f"Te faltan {precio-data[s]['coins']} - Tenes {data[s]['coins']}"); return
 data[s]["coins"]-=precio; data[s]["owned"].append(key); save_u(data)
 await i.response.send_message(f"✅ Compraste {key} por {precio}! Quedan {data[s]['coins']}")

@tree.command(name="equipar",description="Equipar tablero")
async def equipar(i:discord.Interaction, tablero: str):
 tablero=tablero.lower()
 data,s=get_u(i.user.id); data=load_u()
 if tablero!="default" and tablero not in data[s]["owned"]:
  await i.response.send_message(f"No tenes {tablero}. /tienda"); return
 data[s]["equipado"]=tablero; save_u(data)
 t=buscar_tablero(tablero) if tablero!="default" else tab_user(i.user.id)
 if t and os.path.exists(t):
  await i.response.send_message(f"Equipado {tablero}!",file=discord.File(t,filename="t.jpg"))
 else: await i.response.send_message(f"Equipado {tablero}!")

@tree.command(name="codigos",description="Canjear codigos")
async def codigos(i:discord.Interaction, codigo: str):
 codigo=codigo.upper()
 if codigo not in CODIGOS: await i.response.send_message("Codigo invalido. Probá TRUCO2026"); return
 data,s=get_u(i.user.id); data=load_u()
 if codigo in data[s].get("codigos",[]): await i.response.send_message("Ya canjeaste ese codigo"); return
 cant=CODIGOS[codigo]
 data[s]["coins"]=data[s].get("coins",0)+cant
 data[s]["codigos"].append(codigo)
 save_u(data)
 await i.response.send_message(f"✅ Canjeaste {codigo} +{cant} coins! Total: {data[s]['coins']}")

@tree.command(name="ayuda",description="Ayuda truco")
async def ayuda(i:discord.Interaction):
 e=discord.Embed(title="AYUDA TRUCO",description="/jugar vs bot (250 coins si ganas)\n/tienda - ver tableros con foto + boton comprar\n/comprar [nombre] - river/boca/san lorenzo/racing/oro/diamante/springtrap\n/equipar [nombre]\n/perfil - ver coins\n/codigos TRUCO2026 - 1000 coins gratis\nPrecios: River 500, Boca 500, San Lorenzo 500, Racing 500, Oro 700, Diamante 1450, Springtrap 650",color=0x9b59b6)
 await i.response.send_message(embed=e)

@bot.event
async def on_ready():
 await tree.sync()
 print("TODO FIXEADO - coins + codigos + ayuda + tienda con boton")

bot.run(os.getenv("DISCORD_TOKEN"))

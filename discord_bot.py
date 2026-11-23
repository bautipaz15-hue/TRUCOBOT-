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
def envido_valor(n): return n if n<10 else 0
def calc_envido(mano):
 # mano = lista de 3 cartas
 max_e=0
 for i in range(3):
  for j in range(i+1,3):
   if mano[i][1]==mano[j][1]:
    s=20+envido_valor(mano[i][0])+envido_valor(mano[j][0])
    if s>max_e: max_e=s
 if max_e==0: max_e=max([envido_valor(c[0]) for c in mano])
 return max_e

PRECIOS={"river":500,"boca":500,"san lorenzo":500,"racing":500,"oro":700,"diamante":1450,"springtrap":650}
CODIGOS={"TRUCO2026":1000}
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
 return data,s
def add_coins(uid,cant):
 data=load_u(); s=str(uid)
 if s not in data: data[s]={"coins":0,"equipado":"default","owned":["default"],"codigos":[]}
 data[s]["coins"]=data[s].get("coins",0)+cant
 save_u(data); return data[s]["coins"]

def buscar_tablero(nombre):
 if not os.path.exists("tableros"): return None
 nombre=nombre.lower().replace(" ","")
 for f in os.listdir("tableros"):
  if nombre in f.lower().replace(" ",""): return os.path.join("tableros",f)
 return None
def tab_user(uid):
 data=load_u(); s=str(uid)
 eq=data.get(s,{}).get("equipado","default").lower() if s in data else "default"
 if eq=="default":
  return "tableros/Tablero.jpg" if os.path.exists("tableros/Tablero.jpg") else None
 t=buscar_tablero(eq)
 return t if t and os.path.exists(t) else "tableros/Tablero.jpg"
def av():
 for x in ["bot_rojo.png","tableros/bot_rojo.png"]:
  if os.path.exists(x): return x
 return None

# --- VIEWS TRUCO/ENVIDO FUNCIONAL ---
class TrucoResp(discord.ui.View):
 def __init__(self,owner):
  super().__init__(timeout=30); self.owner=owner
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b):
  d=partidas.get(self.owner)
  if not d: return
  d["truco_nivel"]+=1
  await i.response.send_message(f"{i.user.mention} QUIERO! Ahora vale {d['truco_nivel']} puntos")
  self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b):
  d=partidas.get(self.owner)
  if d: 
   d["pj"]=2 # gana el que canto
   await i.response.send_message(f"{i.user.mention} NO QUIERO! Gana punto el rival")
  self.stop()

class EnvidoResp(discord.ui.View):
 def __init__(self,owner):
  super().__init__(timeout=30); self.owner=owner
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b):
  d=partidas.get(self.owner)
  if not d: return
  mj=d["mano_jugador"]; mb=d["mano_bot"]
  ej=calc_envido(mj); eb=calc_envido(mb)
  if ej>eb:
   d["pj"]+=2
   await i.response.send_message(f"Envido: Vos {ej} vs Bot {eb} - Ganaste 2 puntos! ({d['pj']}-{d['pb']})")
  elif eb>ej:
   d["pb"]+=2
   await i.response.send_message(f"Envido: Vos {ej} vs Bot {eb} - Perdiste 2 puntos ({d['pj']}-{d['pb']})")
  else:
   await i.response.send_message(f"Envido {ej} empate - gana mano")
  d["envido_jugado"]=True
  self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b):
  d=partidas.get(self.owner)
  if d: d["pj"]+=1; await i.response.send_message(f"No quiso envido - Ganaste 1 punto")
  self.stop()

# --- EXPRESIONES ---
class ExpBtn(discord.ui.Button):
 def __init__(self,txt,label,o):
  self.txt=txt; self.o=o
  super().__init__(label=label,style=discord.ButtonStyle.secondary)
 async def callback(self,i):
  if i.user.id!=self.o: return
  await i.response.send_message(f"**{i.user.display_name}:** {self.txt}")

class ExpView(discord.ui.View):
 def __init__(self,o):
  super().__init__(timeout=60)
  self.add_item(ExpBtn("¡Apurate que me duermo!","😴 Me duermo",o))
  self.add_item(ExpBtn("¿Buscando como se juega?","🔍 Google?",o))
  self.add_item(ExpBtn("XD","😂 XD",o))
  self.add_item(ExpBtn("JAJAJA que malo sos","🤣 JAJA",o))

# --- CARTAS (SIN IMAGENES AL TIRAR) ---
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
  
  if vy>vb:
   d["pj"]+=d["truco_nivel"]
   txt=f"✅ Ganaste 1 punto! Tu {self.carta[0]} de {self.carta[1]} le gana a {cb[0]} de {cb[1]} -> {d['pj']}-{d['pb']}"
  elif vb>vy:
   d["pb"]+=d["truco_nivel"]
   txt=f"❌ Perdiste 1 punto. Bot {cb[0]} de {cb[1]} vs tu {self.carta[0]} -> {d['pj']}-{d['pb']}"
  else:
   txt=f"🤝 Empate {self.carta[0]} vs {cb[0]} -> {d['pj']}-{d['pb']}"

  if d["pj"]>=2 or d["pb"]>=2 or len(d["bot"])==0:
   for c in self.view.children: c.disabled=True
   if d["pj"]>d["pb"]:
    coins=add_coins(self.owner,250)
    txt+=f"\n\n🎉 GANASTE LA PARTIDA {d['pj']}-{d['pb']} +250 Trucoins! Total {coins}"
   elif d["pb"]>d["pj"]:
    txt+=f"\n\n💀 PERDISTE {d['pb']}-{d['pj']}"
   else: txt+=f"\n\n🤝 EMPATE"
   partidas.pop(self.owner,None)

  await i.response.edit_message(view=self.view)
  await i.followup.send(content=txt) # SIN IMAGENES AQUI

class T(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="TRUCO",style=discord.ButtonStyle.danger,row=1)
 async def callback(self,i):
  if i.user.id!=self.o: return
  d=partidas.get(self.o)
  if d and d["truco_nivel"]==1:
   d["truco_nivel"]=1
   await i.response.send_message(f"{i.user.mention} canto TRUCO! Vale 2",view=TrucoResp(self.o))
  elif d and d["truco_nivel"]==2:
   await i.response.send_message(f"{i.user.mention} RETRUCO! Vale 3",view=TrucoResp(self.o))
  else:
   await i.response.send_message(f"{i.user.mention} VALE 4! Vale 4",view=TrucoResp(self.o))

class E(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="ENVIDO",style=discord.ButtonStyle.success,row=1)
 async def callback(self,i):
  if i.user.id!=self.o: return
  d=partidas.get(self.o)
  if d and d.get("envido_jugado"): await i.response.send_message("Ya jugaron envido",ephemeral=True); return
  ej=calc_envido(d["mano_jugador"])
  await i.response.send_message(f"{i.user.mention} canto ENVIDO! Tiene {ej} - Bot decide:",view=EnvidoResp(self.o))

class S(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="SALIR",style=discord.ButtonStyle.secondary,row=1)
 async def callback(self,i):
  partidas.pop(self.o,None)
  for c in self.view.children: c.disabled=True
  await i.response.edit_message(content="Saliste",view=self.view)

class ExpOpen(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="Expresiones",style=discord.ButtonStyle.secondary,row=1)
 async def callback(self,i): await i.response.send_message("Elegi:",view=ExpView(self.o),ephemeral=True)

class V(discord.ui.View):
 def __init__(self,o,m):
  super().__init__(timeout=600)
  for c in m: self.add_item(C(c,o))
  self.add_item(T(o)); self.add_item(E(o)); self.add_item(ExpOpen(o)); self.add_item(S(o))

@tree.command(name="jugar",description="Jugar vs bot +250")
async def jugar(i:discord.Interaction):
 m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m)
 mj=[m.pop() for _ in range(3)]; mb=[m.pop() for _ in range(3)]
 partidas[i.user.id]={"bot":mb,"mano_jugador":mj,"mano_bot":mb.copy(),"pj":0,"pb":0,"truco_nivel":1,"envido_jugado":False}
 t=tab_user(i.user.id); a=av()
 emb=discord.Embed(title="TRUCO - a 2 puntos",description=f"{i.user.mention} Mano: {', '.join([f'{c[0]} de {c[1]}' for c in mj])}\nEnvido tuyo: {calc_envido(mj)} | Truco vale 1",color=0x1e8449)
 fs=[]
 if t and os.path.exists(t): fs.append(discord.File(t,filename="t.jpg")); emb.set_image(url="attachment://t.jpg")
 if a and os.path.exists(a): fs.append(discord.File(a,filename="b.jpg")); emb.set_thumbnail(url="attachment://b.jpg")
 await i.response.send_message(embed=emb,view=V(i.user.id,mj),files=fs if fs else None)

@tree.command(name="tienda",description="Tienda con fotos")
async def tienda(i:discord.Interaction):
 # Manda 1 mensaje con todas las fotos que existan
 files=[]
 embed_text=""
 for nombre,precio in PRECIOS.items():
  t=buscar_tablero(nombre)
  if t and os.path.exists(t):
   files.append(discord.File(t,filename=f"{nombre.replace(' ','')}.jpg"))
   embed_text+=f"{nombre} - {precio} coins\n"
  else:
   embed_text+=f"{nombre} - {precio} coins (sin imagen)\n"
 e=discord.Embed(title="🛒 TIENDA - Fotos reales",description=embed_text,color=0xf1c40f)
 if files:
  e.set_image(url=f"attachment://{files[0].filename}")
  await i.response.send_message(embed=e,files=files)
 else:
  await i.response.send_message(embed=e)

@tree.command(name="comprar",description="Comprar")
async def comprar(i:discord.Interaction, tablero: str):
 key=tablero.lower()
 for k in PRECIOS:
  if k in key or key in k: key=k; break
 if key not in PRECIOS: await i.response.send_message("No existe"); return
 data=load_u(); s=str(i.user.id)
 if s not in data: data[s]={"coins":0,"equipado":"default","owned":["default"],"codigos":[]}
 if key in data[s]["owned"]: await i.response.send_message(f"Ya tenes {key}"); return
 if data[s]["coins"]<PRECIOS[key]: await i.response.send_message(f"Te faltan {PRECIOS[key]-data[s]['coins']}"); return
 data[s]["coins"]-=PRECIOS[key]; data[s]["owned"].append(key); save_u(data)
 t=buscar_tablero(key)
 if t and os.path.exists(t):
  await i.response.send_message(f"✅ Compraste {key}!",file=discord.File(t,filename="tab.jpg"))
 else: await i.response.send_message(f"✅ Compraste {key}!")

@tree.command(name="equipar",description="Equipar")
async def equipar(i:discord.Interaction, tablero: str):
 key=tablero.lower()
 data=load_u(); s=str(i.user.id)
 if s not in data or (key!="default" and key not in data[s]["owned"]): await i.response.send_message("No lo tenes"); return
 data[s]["equipado"]=key; save_u(data)
 t=tab_user(i.user.id)
 if t and os.path.exists(t):
  await i.response.send_message(f"Equipaste {key}",file=discord.File(t,filename="tab.jpg"))
 else: await i.response.send_message(f"Equipaste {key}")

@tree.command(name="perfil",description="Perfil")
async def perfil(i:discord.Interaction):
 data=load_u(); s=str(i.user.id)
 c=data.get(s,{}).get("coins",0) if s in data else 0
 await i.response.send_message(f"💰 {c} coins")

@tree.command(name="codigos",description="Codigo")
async def codigos(i:discord.Interaction, codigo: str):
 codigo=codigo.upper()
 data=load_u(); s=str(i.user.id)
 if s not in data: data[s]={"coins":0,"equipado":"default","owned":["default"],"codigos":[]}
 if codigo not in CODIGOS: await i.response.send_message("Invalido"); return
 if codigo in data[s]["codigos"]: await i.response.send_message("Ya canjeado"); return
 data[s]["coins"]+=CODIGOS[codigo]; data[s]["codigos"].append(codigo); save_u(data)
 await i.response.send_message(f"+{CODIGOS[codigo]} coins! Total {data[s]['coins']}")

@tree.command(name="ayuda",description="Ayuda")
async def ayuda(i:discord.Interaction):
 e=discord.Embed(title="AYUDA",description="/jugar - Truco y Envido FUNCIONAN (envido suma puntos, truco vale mas)\nGanaste 1 punto / Perdiste 1 punto (no GANASTE!)\n2-0 termina partida\nExpresiones\n/tienda muestra foto de cada tablero",color=0x9b59b6)
 await i.response.send_message(embed=e)

@bot.event
async def on_ready():
 await tree.sync()
 print("FINAL PRO: sin imgs cartas + truco/envido funcional + tienda con fotos + 2-0 + expresiones")

bot.run(os.getenv("DISCORD_TOKEN"))

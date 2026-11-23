import discord, random, os, json, asyncio
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
def add_coins(uid,cant):
 data=load_u(); s=str(uid)
 if s not in data: data[s]={"coins":0,"equipado":"default","owned":["default"],"codigos":[]}
 data[s]["coins"]=data[s].get("coins",0)+cant
 save_u(data); return data[s]["coins"]

def buscar_tablero(nombre):
 if not os.path.exists("tableros"): return None
 nombre=nombre.lower().replace(" ","").replace("_","").replace("-","")
 for f in os.listdir("tableros"):
  fl=f.lower().replace(" ","").replace("_","").replace("-","")
  if "sanlorenzo" in nombre and "sanlorenzo" in fl: return os.path.join("tableros",f)
  if nombre in fl or fl.replace(".jpg","").replace(".png","").replace(".pnj","") in nombre: 
   return os.path.join("tableros",f)
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

# --- TIENDA ---
class BotonTienda(discord.ui.Button):
 def __init__(self,nombre,precio,owner):
  self.nombre=nombre; self.precio=precio; self.owner=owner
  data=load_u(); s=str(owner)
  owned=data.get(s,{}).get("owned",[]) if s in data else []
  equipado=data.get(s,{}).get("equipado","default") if s in data else "default"
  if nombre in owned:
   if equipado==nombre: super().__init__(label=f"{nombre.upper()} EQUIPADO ✅",style=discord.ButtonStyle.success,disabled=True)
   else: super().__init__(label=f"EQUIPAR {nombre.upper()}",style=discord.ButtonStyle.success)
  else: super().__init__(label=f"COMPRAR {nombre.upper()} - {precio}",style=discord.ButtonStyle.primary)
 async def callback(self,i):
  if i.user.id!=self.owner: await i.response.send_message("No es tu tienda",ephemeral=True); return
  data=load_u(); s=str(i.user.id)
  if s not in data: data[s]={"coins":0,"equipado":"default","owned":["default"],"codigos":[]}
  if self.nombre in data[s]["owned"]:
   data[s]["equipado"]=self.nombre; save_u(data)
   await i.response.edit_message(embed=discord.Embed(title=f"Equipaste {self.nombre.upper()} ✅",color=0x2ecc71),view=TiendaView(self.owner))
  else:
   if data[s]["coins"]<self.precio: await i.response.send_message(f"Te faltan {self.precio-data[s]['coins']} coins",ephemeral=True); return
   data[s]["coins"]-=self.precio; data[s]["owned"].append(self.nombre); save_u(data)
   await i.response.edit_message(embed=discord.Embed(title=f"Compraste {self.nombre.upper()} ✅",color=0xf1c40f),view=TiendaView(self.owner))

class TiendaView(discord.ui.View):
 def __init__(self,owner):
  super().__init__(timeout=300)
  for n,p in PRECIOS.items(): self.add_item(BotonTienda(n,p,owner))

@tree.command(name="tienda",description="Tienda")
async def tienda(i:discord.Interaction):
 data=load_u(); coins=data.get(str(i.user.id),{}).get("coins",0)
 files=[]
 for nombre in PRECIOS.keys():
  t=buscar_tablero(nombre)
  if t and os.path.exists(t): files.append(discord.File(t,filename=f"{nombre.replace(' ','')}.jpg"))
 e=discord.Embed(title=f"🛒 TIENDA - {coins} coins",description="COMPRAR -> EQUIPAR -> EQUIPADO",color=0xf1c40f)
 if files: e.set_image(url=f"attachment://{files[0].filename}")
 await i.response.send_message(embed=e,view=TiendaView(i.user.id),files=files if files else None, ephemeral=True)

# --- RESPUESTAS ---
class TrucoResp(discord.ui.View):
 def __init__(self,owner):
  super().__init__(timeout=30); self.owner=owner
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b): d=partidas.get(self.owner); d["truco_nivel"]+=1; await i.response.send_message(f"{i.user.mention} QUIERO! Vale {d['truco_nivel']}"); self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b): d=partidas.get(self.owner); d["pj"]=2; await i.response.send_message(f"{i.user.mention} NO QUIERO!"); self.stop()

class EnvidoResp(discord.ui.View):
 def __init__(self,owner):
  super().__init__(timeout=30); self.owner=owner
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b):
  d=partidas.get(self.owner); mj=d["mano_jugador"]; mb=d["mano_bot"]; ej=calc_envido(mj); eb=calc_envido(mb)
  if ej>eb: d["pj"]+=2; await i.response.send_message(f"Envido {ej} vs {eb} Ganaste 2 ({d['pj']}-{d['pb']})")
  else: d["pb"]+=2; await i.response.send_message(f"Envido {ej} vs {eb} Perdiste 2 ({d['pj']}-{d['pb']})")
  d["envido_jugado"]=True; self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b): d=partidas.get(self.owner); d["pj"]+=1; await i.response.send_message("No quiso - Ganaste 1"); self.stop()

class TrucoRespAmigo(discord.ui.View):
 def __init__(self,pid): super().__init__(timeout=30); self.pid=pid
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b): await i.response.send_message(f"{i.user.mention} QUIERO!"); self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b):
  d=partidas.get(self.pid); ganador=[x for x in d["puntos"].keys() if x!=i.user.id][0]; d["puntos"][ganador]+=1
  await i.response.send_message(f"{i.user.mention} NO QUIERO! +1 para {d['nombres'][ganador]}"); self.stop()

class EnvidoRespAmigo(discord.ui.View):
 def __init__(self,pid): super().__init__(timeout=30); self.pid=pid
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b):
  d=partidas.get(self.pid); u1,u2=list(d["mano"].keys()); ej1=calc_envido(d["mano"][u1]); ej2=calc_envido(d["mano"][u2])
  if ej1>ej2: d["puntos"][u1]+=2; await i.response.send_message(f"{d['nombres'][u1]} {ej1} vs {d['nombres'][u2]} {ej2} Gana {d['nombres'][u1]}")
  else: d["puntos"][u2]+=2; await i.response.send_message(f"{d['nombres'][u2]} {ej2} vs {d['nombres'][u1]} {ej1} Gana {d['nombres'][u2]}")
  self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b): d=partidas.get(self.pid); ganador=[x for x in d["puntos"].keys() if x!=i.user.id][0]; d["puntos"][ganador]+=1; await i.response.send_message(f"No quiso +1 para {d['nombres'][ganador]}"); self.stop()

# --- CARTAS BOT (DESACTIVA LOS DOS) ---
class C(discord.ui.Button):
 def __init__(self,carta,owner): self.carta=carta; self.owner=owner; super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary,row=0)
 async def callback(self,i):
  if i.user.id!=self.owner: await i.response.send_message("No es tuya",ephemeral=True);return
  d=partidas.get(self.owner); self.disabled=True; await i.response.edit_message(view=self.view)
  await i.followup.send(f"Tiraste {self.carta[0]} de {self.carta[1]}"); await i.followup.send("🤖 Bot pensando..."); await asyncio.sleep(2)
  cb=d["bot"].pop(0); vy=v(self.carta[0],self.carta[1]); vb=v(cb[0],cb[1])
  if vy>vb: d["pj"]+=d["truco_nivel"]; txt=f"✅ Ganaste! {self.carta[0]} vs {cb[0]} -> {d['pj']}-{d['pb']}"
  elif vb>vy: d["pb"]+=d["truco_nivel"]; txt=f"❌ Perdiste! {cb[0]} vs {self.carta[0]} -> {d['pj']}-{d['pb']}"
  else: txt=f"🤝 Empate {self.carta[0]} vs {cb[0]}"
  if d["pj"]>=2 or d["pb"]>=2 or len(d["bot"])==0:
   if d["pj"]>d["pb"]: coins=add_coins(self.owner,250); txt+=f"\n🎉 GANASTE +250 Total {coins}"
   else: txt+=f"\n💀 PERDISTE"; partidas.pop(self.owner,None)
  await i.followup.send(content=txt)

class T(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="TRUCO",style=discord.ButtonStyle.danger,row=1)
 async def callback(self,i):
  if i.user.id!=self.o: return
  d=partidas.get(self.o)
  # DESACTIVA TRUCO Y ENVIDO LOS DOS
  for child in self.view.children:
   if child.label in ["TRUCO","ENVIDO"]: child.disabled=True
  await i.response.edit_message(view=self.view)
  if d["truco_nivel"]==1: await i.followup.send(f"{i.user.mention} canto TRUCO! Vale 2",view=TrucoResp(self.o))
  elif d["truco_nivel"]==2: await i.followup.send(f"{i.user.mention} RETRUCO! Vale 3",view=TrucoResp(self.o))
  else: await i.followup.send(f"{i.user.mention} VALE 4!",view=TrucoResp(self.o))

class E(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="ENVIDO",style=discord.ButtonStyle.success,row=1)
 async def callback(self,i):
  if i.user.id!=self.o: return
  d=partidas.get(self.o)
  if d.get("envido_jugado"): await i.response.send_message("Ya jugaron envido",ephemeral=True); return
  # DESACTIVA TRUCO Y ENVIDO LOS DOS
  for child in self.view.children:
   if child.label in ["TRUCO","ENVIDO"]: child.disabled=True
  await i.response.edit_message(view=self.view)
  ej=calc_envido(d["mano_jugador"])
  await i.followup.send(f"{i.user.mention} canto ENVIDO! Tiene {ej}",view=EnvidoResp(self.o))

class V(discord.ui.View):
 def __init__(self,o,m): super().__init__(timeout=600); 
 for c in m: self.add_item(C(c,o))
 self.add_item(T(o)); self.add_item(E(o))

# --- AMIGO ---
class CartaAmigo(discord.ui.Button):
 def __init__(self,carta,owner,pid): self.carta=carta; self.owner=owner; self.pid=pid; super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary)
 async def callback(self,i):
  d=partidas.get(self.pid)
  if i.user.id!=self.owner or d["turno"]!=self.owner: await i.response.send_message("No es tu turno",ephemeral=True); return
  d["jugadas"][self.owner]=self.carta; self.disabled=True; await i.response.edit_message(view=self.view); await i.followup.send(f"{i.user.mention} tiró {self.carta[0]} de {self.carta[1]}")
  if len(d["jugadas"])==2:
   u1,u2=list(d["jugadas"].keys()); c1=d["jugadas"][u1]; c2=d["jugadas"][u2]; vy=v(c1[0],c1[1]); vb=v(c2[0],c2[1])
   if vy>vb: d["puntos"][u1]+=1; txt=f"✅ {d['nombres'][u1]} gana {c1[0]} vs {c2[0]} ({d['puntos'][u1]}-{d['puntos'][u2]})"
   elif vb>vy: d["puntos"][u2]+=1; txt=f"✅ {d['nombres'][u2]} gana ({d['puntos'][u1]}-{d['puntos'][u2]})"
   else: txt="🤝 Empate!"; d["jugadas"]={}
   if d["puntos"][u1]>=2 or d["puntos"][u2]>=2: ganador=u1 if d["puntos"][u1]>d["puntos"][u2] else u2; add_coins(ganador,250); txt+=f"\n🎉 {d['nombres'][ganador]} GANA +250!"; partidas.pop(self.pid,None); await i.followup.send(txt)
   else: d["turno"]=u1 if d["turno"]==u2 else u2; t_path=tab_user(d["turno"]); files=[]; 
   if t_path and os.path.exists(t_path): files.append(discord.File(t_path,filename="tablero.jpg"))
   emb=discord.Embed(title=f"TRUCO",description=f"{txt}\n➡️ Turno de {d['nombres'][d['turno']]}",color=0xe74c3c)
   if files: emb.set_image(url="attachment://tablero.jpg")
   await i.followup.send(embed=emb, files=files if files else None); d["jugadas"]={}
  else: d["turno"]=[x for x in d["puntos"].keys() if x!=self.owner][0]; t_path=tab_user(d["turno"]); files=[]; 
  if t_path and os.path.exists(t_path): files.append(discord.File(t_path,filename="tablero.jpg"))
  emb=discord.Embed(title="TRUCO 1vs1",description=f"➡️ Turno de {d['nombres'][d['turno']]} - Ve SU tablero",color=0xe74c3c)
  if files: emb.set_image(url="attachment://tablero.jpg")
  await i.followup.send(embed=emb, files=files if files else None)

class ViewAmigos(discord.ui.View):
 def __init__(self,pid,j1,j2,m1,m2):
  super().__init__(timeout=600); self.pid=pid
  for c in m1: self.add_item(CartaAmigo(c,j1,pid))
  for c in m2: b=CartaAmigo(c,j2,pid); b.row=1; self.add_item(b)
  truco=discord.ui.Button(label="TRUCO",style=discord.ButtonStyle.danger,row=2)
  envido=discord.ui.Button(label="ENVIDO",style=discord.ButtonStyle.success,row=2)
  async def truco_cb(inter):
   if inter.user.id not in [j1,j2]: return
   # DESACTIVA LOS DOS Y HACE FUNCION
   for child in self.children:
    if child.label in ["TRUCO","ENVIDO"]: child.disabled=True
   await inter.response.edit_message(view=self)
   await inter.followup.send(f"{inter.user.mention} cantó TRUCO!",view=TrucoRespAmigo(pid))
  async def envido_cb(inter):
   if inter.user.id not in [j1,j2]: return
   if partidas[pid].get("envido_jugado"): await inter.response.send_message("Ya cantaron",ephemeral=True); return
   # DESACTIVA LOS DOS Y HACE FUNCION
   for child in self.children:
    if child.label in ["TRUCO","ENVIDO"]: child.disabled=True
   partidas[pid]["envido_jugado"]=True
   await inter.response.edit_message(view=self)
   await inter.followup.send(f"{inter.user.mention} cantó ENVIDO!",view=EnvidoRespAmigo(pid))
  truco.callback=truco_cb; envido.callback=envido_cb
  self.add_item(truco); self.add_item(envido)

@tree.command(name="jugar",description="Jugar")
async def jugar(i:discord.Interaction, oponente: discord.Member = None):
 if oponente and oponente.id!=i.user.id and not oponente.bot:
  m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m); mj=[m.pop() for _ in range(3)]; mo=[m.pop() for _ in range(3)]
  pid=f"{i.user.id}_{oponente.id}_{random.randint(1,99999)}"
  partidas[pid]={"jugadas":{},"puntos":{i.user.id:0,oponente.id:0},"nombres":{i.user.id:i.user.display_name,oponente.id:oponente.display_name},"turno":i.user.id,"mano":{i.user.id:mj, oponente.id:mo},"envido_jugado":False}
  t_path=tab_user(i.user.id); files=[]; 
  if t_path and os.path.exists(t_path): files.append(discord.File(t_path,filename="tablero.jpg"))
  emb=discord.Embed(title=f"TRUCO {i.user.display_name} vs {oponente.display_name}",description=f"A 2 puntos ➡️ Turno de {i.user.display_name}",color=0xe74c3c)
  if files: emb.set_image(url="attachment://tablero.jpg")
  await i.response.send_message(embed=emb,view=ViewAmigos(pid,i.user.id,oponente.id,mj,mo),files=files if files else None)
  return
 m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m); mj=[m.pop() for _ in range(3)]; mb=[m.pop() for _ in range(3)]
 partidas[i.user.id]={"bot":mb,"mano_jugador":mj,"mano_bot":mb.copy(),"pj":0,"pb":0,"truco_nivel":1,"envido_jugado":False}
 t=tab_user(i.user.id); a=av(); emb=discord.Embed(title="TRUCO - a 2 puntos",description=f"{i.user.mention} Mano: {', '.join([f'{c[0]} de {c[1]}' for c in mj])}\nEnvido: {calc_envido(mj)}",color=0x1e8449); fs=[]
 if t and os.path.exists(t): fs.append(discord.File(t,filename="t.jpg")); emb.set_image(url="attachment://t.jpg")
 if a and os.path.exists(a): fs.append(discord.File(a,filename="b.jpg")); emb.set_thumbnail(url="attachment://b.jpg")
 await i.response.send_message(embed=emb,view=V(i.user.id,mj),files=fs if fs else None)

@tree.command(name="perfil",description="Perfil")
async def perfil(i:discord.Interaction): data=load_u(); s=str(i.user.id); c=data.get(s,{}).get("coins",0) if s in data else 0; await i.response.send_message(f"💰 {c} coins")
@tree.command(name="codigos",description="Codigo")
async def codigos(i:discord.Interaction, codigo: str):
 codigo=codigo.upper(); data=load_u(); s=str(i.user.id)
 if s not in data: data[s]={"coins":0,"equipado":"default","owned":["default"],"codigos":[]}
 if codigo not in CODIGOS: await i.response.send_message("Invalido"); return
 if codigo in data[s]["codigos"]: await i.response.send_message("Ya canjeado"); return
 data[s]["coins"]+=CODIGOS[codigo]; data[s]["codigos"].append(codigo); save_u(data)
 await i.response.send_message(f"+{CODIGOS[codigo]} coins! Total {data[s]['coins']}")

@bot.event
async def on_ready(): await tree.sync(); print("FINAL: truco/envido desactivan ambos pero hacen funcion + todo lo demas")
bot.run(os.getenv("DISCORD_TOKEN"))

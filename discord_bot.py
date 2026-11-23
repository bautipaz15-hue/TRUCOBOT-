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

# --- PRECIOS FINALES DEFINITIVOS ---
PRECIOS={
    "river":1000,"boca":1000,"san lorenzo":1000,"racing":1000,
    "springtrap":1250,
    "creeper":1500,"minecraft":1500,
    "diamante":1800,"oro":1200,"gamer":1200
}

# CODES DEFINITIVOS
CODIGOS={
    "TRUCO2026":1000,
    "navidad_se_acerca":350,
    "7_ORO":350,
    "TRUCO!":0,
    "1_ESPADA":0,
    "SPRITE":0,
    "VICTORY ROYALE":0
}

PODERES_PRECIO={
    "MAGO":{"x1":400,"x10":3500},
    "OJO":{"x1":350,"x10":3000},
    "ESCUDO":{"x1":500,"x10":4500},
    "LADRON":{"x1":450,"x10":4000}
}

EXPRESIONES_TIENDA={
    "DEFAULT":{"precio":0,"txt":["HOLA","GG"]},
    "AMIGABLE":{"precio":150,"txt":["`ദ്ദി(ᵔᗜᵔ) HOLA`","`GG`","`BUENA PARTIDA👍`"]},
    "KAOMOJI":{"precio":250,"txt":["`ദ്ദി(ᵔᗜᵔ)`","`( ✧Д✧) WOW`","`(╥_╥)`"]},
    "ARTE":{"precio":400,"txt":["`ARTE TEXTO 1`","`ARTE TEXTO 2`"]}
}

FILE="usuarios.json"
def load_u():
 if not os.path.exists(FILE): return {}
 try:
  with open(FILE,"r") as f: return json.load(f)
 except: return {}
def save_u(d):
 with open(FILE,"w") as f: json.dump(d,f,indent=2)

def ensure_user(uid):
 data=load_u(); s=str(uid)
 if s not in data:
  data[s]={"coins":0,"equipado":"default","owned":["default"],"codigos":[],"poderes":{"MAGO":0,"OJO":0,"ESCUDO":0,"LADRON":0},"owned_exp":["DEFAULT"],"exp_equipado":"DEFAULT"}
 # migración para usuarios viejos
 data[s].setdefault("poderes",{"MAGO":0,"OJO":0,"ESCUDO":0,"LADRON":0})
 data[s].setdefault("owned_exp",["DEFAULT"])
 data[s].setdefault("exp_equipado","DEFAULT")
 save_u(data)
 return data

def add_coins(uid,cant):
 data=ensure_user(uid); s=str(uid)
 data[s]["coins"]=data[s].get("coins",0)+cant
 save_u(data); return data[s]["coins"]

def buscar_tablero(nombre):
 if not os.path.exists("tableros"): return None
 nombre=nombre.lower().replace(" ","").replace("_","").replace("-","")
 for f in os.listdir("tableros"):
  fl=f.lower().replace(" ","").replace("_","").replace("-","")
  if "sanlorenzo" in nombre and "sanlorenzo" in fl: return os.path.join("tableros",f)
  if nombre in fl: return os.path.join("tableros",f)
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

# --- TIENDA BOTONES ---
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
  if s not in data: data[s]=ensure_user(i.user.id)[s]
  if self.nombre in data[s]["owned"]:
   data[s]["equipado"]=self.nombre; save_u(data)
   await i.response.edit_message(embed=discord.Embed(title=f"Equipaste {self.nombre.upper()} ✅",description=f"Tu tablero ahora es {self.nombre}",color=0x2ecc71),view=TiendaView(self.owner, "tableros"))
  else:
   if data[s]["coins"]<self.precio: await i.response.send_message(f"Te faltan {self.precio-data[s]['coins']} coins",ephemeral=True); return
   data[s]["coins"]-=self.precio; data[s]["owned"].append(self.nombre); save_u(data)
   await i.response.edit_message(embed=discord.Embed(title=f"Compraste {self.nombre.upper()} ✅",description="Ahora tocalo para equipar",color=0xf1c40f),view=TiendaView(self.owner, "tableros"))

class BotonPoder(discord.ui.Button):
 def __init__(self,nombre,tipo,precio,owner):
  self.nombre=nombre; self.tipo=tipo; self.precio=precio; self.owner=owner
  super().__init__(label=f"{nombre} {tipo} - {precio}",style=discord.ButtonStyle.primary)
 async def callback(self,i):
  if i.user.id!=self.owner: return
  data=load_u(); s=str(i.user.id)
  ensure_user(i.user.id); data=load_u()
  if data[s]["coins"]<self.precio: await i.response.send_message(f"Te faltan {self.precio-data[s]['coins']}",ephemeral=True); return
  cant=1 if self.tipo=="x1" else 10
  data[s]["coins"]-=self.precio
  data[s]["poderes"][self.nombre]+=cant
  save_u(data)
  await i.response.send_message(f"✅ Compraste {self.nombre} {self.tipo}! Ahora tenes {data[s]['poderes'][self.nombre]}",ephemeral=True)

class BotonExp(discord.ui.Button):
 def __init__(self,nombre,precio,owner):
  self.nombre=nombre; self.precio=precio; self.owner=owner
  data=load_u(); s=str(owner)
  owned=data.get(s,{}).get("owned_exp",["DEFAULT"]) if s in data else ["DEFAULT"]
  equip=data.get(s,{}).get("exp_equipado","DEFAULT") if s in data else "DEFAULT"
  if nombre in owned:
   if equip==nombre: super().__init__(label=f"{nombre} EQUIPADO ✅",style=discord.ButtonStyle.success,disabled=True)
   else: super().__init__(label=f"EQUIPAR {nombre}",style=discord.ButtonStyle.success)
  else: super().__init__(label=f"COMPRAR {nombre} - {precio}",style=discord.ButtonStyle.primary)
 async def callback(self,i):
  if i.user.id!=self.owner: return
  data=load_u(); s=str(i.user.id)
  ensure_user(i.user.id); data=load_u()
  if self.nombre in data[s]["owned_exp"]:
   # EQUIPADO UNICO: reemplaza el anterior
   anterior=data[s]["exp_equipado"]
   data[s]["exp_equipado"]=self.nombre
   save_u(data)
   await i.response.edit_message(embed=discord.Embed(title=f"Equipaste {self.nombre} ✅",description=f"Se quitó {anterior} y ahora usas {self.nombre}\nExpresiones: {', '.join(EXPRESIONES_TIENDA[self.nombre]['txt'])}",color=0x2ecc71),view=TiendaView(self.owner,"expresiones"))
  else:
   if data[s]["coins"]<self.precio: await i.response.send_message(f"Te faltan {self.precio-data[s]['coins']}",ephemeral=True); return
   data[s]["coins"]-=self.precio
   data[s]["owned_exp"].append(self.nombre)
   save_u(data)
   await i.response.edit_message(embed=discord.Embed(title=f"Compraste {self.nombre} ✅",description="Ahora equipalo",color=0xf1c40f),view=TiendaView(self.owner,"expresiones"))

class TiendaView(discord.ui.View):
 def __init__(self,owner, categoria="tableros"):
  super().__init__(timeout=300)
  self.owner=owner; self.categoria=categoria
  if categoria=="tableros":
   for n,p in PRECIOS.items(): self.add_item(BotonTienda(n,p,owner))
  elif categoria=="poderes":
   for nombre in PODERES_PRECIO:
    self.add_item(BotonPoder(nombre,"x1",PODERES_PRECIO[nombre]["x1"],owner))
    self.add_item(BotonPoder(nombre,"x10",PODERES_PRECIO[nombre]["x10"],owner))
  elif categoria=="expresiones":
   for nombre in EXPRESIONES_TIENDA:
    if nombre=="DEFAULT": continue
    self.add_item(BotonExp(nombre,EXPRESIONES_TIENDA[nombre]["precio"],owner))
  # Botones para cambiar de apartado
  self.add_item(BtnCambiar("TABLEROS",owner,0))
  self.add_item(BtnCambiar("PODERES",owner,1))
  self.add_item(BtnCambiar("EXPRESIONES",owner,2))

class BtnCambiar(discord.ui.Button):
 def __init__(self,label,owner,row):
  self.owner=owner; super().__init__(label=label,style=discord.ButtonStyle.secondary,row=row+3)
 async def callback(self,i):
  if i.user.id!=self.owner: return
  cat=self.label.lower()
  data=load_u(); s=str(i.user.id)
  coins=data.get(s,{}).get("coins",0)
  await i.response.edit_message(embed=discord.Embed(title=f"🛒 TIENDA {cat.upper()} - {coins} coins",description=f"Apartado: {cat}",color=0xf1c40f),view=TiendaView(self.owner,cat))

# --- VIEWS TRUCO/ENVIDO (TUS VIEJAS SIN CAMBIOS) ---
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
   d["pj"]=2
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

class TrucoRespAmigo(discord.ui.View):
 def __init__(self,pid):
  super().__init__(timeout=30); self.pid=pid
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b):
  await i.response.send_message(f"{i.user.mention} QUIERO! Sigue la mano")
  self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b):
  d=partidas.get(self.pid)
  ganador=[x for x in d["puntos"].keys() if x!=i.user.id][0]
  d["puntos"][ganador]+=1
  await i.response.send_message(f"{i.user.mention} NO QUIERO! +1 punto para {d['nombres'][ganador]}")
  self.stop()

class EnvidoRespAmigo(discord.ui.View):
 def __init__(self,pid):
  super().__init__(timeout=30); self.pid=pid
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b):
  d=partidas.get(self.pid)
  u1,u2=list(d["mano"].keys())
  ej1=calc_envido(d["mano"][u1]); ej2=calc_envido(d["mano"][u2])
  if ej1>ej2: d["puntos"][u1]+=2; await i.response.send_message(f"Envido: {d['nombres'][u1]} {ej1} vs {d['nombres'][u2]} {ej2} - Gana {d['nombres'][u1]} +2!")
  else: d["puntos"][u2]+=2; await i.response.send_message(f"Envido: {d['nombres'][u2]} {ej2} vs {d['nombres'][u1]} {ej1} - Gana {d['nombres'][u2]} +2!")
  self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b):
  d=partidas.get(self.pid)
  ganador=[x for x in d["puntos"].keys() if x!=i.user.id][0]
  d["puntos"][ganador]+=1
  await i.response.send_message(f"No quiso envido - +1 para {d['nombres'][ganador]}")
  self.stop()

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
  data=load_u(); s=str(o)
  pack=data.get(s,{}).get("exp_equipado","DEFAULT") if s in data else "DEFAULT"
  txts=EXPRESIONES_TIENDA.get(pack,EXPRESIONES_TIENDA["DEFAULT"])["txt"]
  for t in txts[:4]:
   self.add_item(ExpBtn(t, t[:20], o))

class C(discord.ui.Button):
 def __init__(self,carta,owner):
  self.carta=carta; self.owner=owner
  super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary,row=0)
 async def callback(self,i):
  if i.user.id!=self.owner: await i.response.send_message("No es tuya",ephemeral=True);return
  d=partidas.get(self.owner)
  if not d: return
  self.disabled=True
  await i.response.edit_message(view=self.view)
  await i.followup.send(f"Tiraste {self.carta[0]} de {self.carta[1]}")
  await i.followup.send("🤖 Bot pensando...")
  await asyncio.sleep(2)
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
  await i.followup.send(content=txt)

class T(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="TRUCO",style=discord.ButtonStyle.danger,row=1)
 async def callback(self,i):
  if i.user.id!=self.o: return
  d=partidas.get(self.o)
  for child in self.view.children:
   if child.label in ["TRUCO","ENVIDO"]: child.disabled=True
  await i.response.edit_message(view=self.view)
  if d and d["truco_nivel"]==1:
   await i.followup.send(f"{i.user.mention} canto TRUCO! Vale 2",view=TrucoResp(self.o))
  elif d and d["truco_nivel"]==2:
   await i.followup.send(f"{i.user.mention} RETRUCO! Vale 3",view=TrucoResp(self.o))
  else:
   await i.followup.send(f"{i.user.mention} VALE 4! Vale 4",view=TrucoResp(self.o))

class E(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="ENVIDO",style=discord.ButtonStyle.success,row=1)
 async def callback(self,i):
  if i.user.id!=self.o: return
  d=partidas.get(self.o)
  if d and d.get("envido_jugado"): await i.response.send_message("Ya jugaron envido",ephemeral=True); return
  for child in self.view.children:
   if child.label in ["TRUCO","ENVIDO"]: child.disabled=True
  await i.response.edit_message(view=self.view)
  ej=calc_envido(d["mano_jugador"])
  await i.followup.send(f"{i.user.mention} canto ENVIDO! Tiene {ej} - Bot decide:",view=EnvidoResp(self.o))

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
  for c in m:
   self.add_item(C(c,o))
  self.add_item(T(o))
  self.add_item(E(o))
  self.add_item(ExpOpen(o))
  self.add_item(S(o))

class CartaAmigo(discord.ui.Button):
 def __init__(self,carta,owner,pid):
  self.carta=carta; self.owner=owner; self.pid=pid
  super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary)
 async def callback(self,i):
  d=partidas.get(self.pid)
  if not d: return
  if i.user.id!=self.owner: await i.response.send_message("No es tu turno",ephemeral=True); return
  if d["turno"]!=self.owner: await i.response.send_message(f"Esperá, es turno de {d['nombres'][d['turno']]} que está pensando...",ephemeral=True); return
  if self.owner in d["jugadas"]: await i.response.send_message("Ya tiraste",ephemeral=True); return
  d["jugadas"][self.owner]=self.carta; self.disabled=True
  await i.response.edit_message(view=self.view)
  await i.followup.send(f"{i.user.mention} tiró {self.carta[0]} de {self.carta[1]}")
  if len(d["jugadas"])==2:
   u1,u2=list(d["jugadas"].keys()); c1=d["jugadas"][u1]; c2=d["jugadas"][u2]
   vy=v(c1[0],c1[1]); vb=v(c2[0],c2[1])
   if vy>vb: d["puntos"][u1]+=1; txt=f"✅ {d['nombres'][u1]} gana! {c1[0]} vs {c2[0]} ({d['puntos'][u1]}-{d['puntos'][u2]})"
   elif vb>vy: d["puntos"][u2]+=1; txt=f"✅ {d['nombres'][u2]} gana! ({d['puntos'][u1]}-{d['puntos'][u2]})"
   else: txt="🤝 Empate!"
   d["jugadas"]={}
   if d["puntos"][u1]>=2 or d["puntos"][u2]>=2:
    ganador=u1 if d["puntos"][u1]>d["puntos"][u2] else u2
    add_coins(ganador,250); txt+=f"\n🎉 {d['nombres'][ganador]} GANA +250!"; partidas.pop(self.pid,None)
    await i.followup.send(txt)
   else:
    d["turno"]= u1 if d["turno"]==u2 else u2
    t_path=tab_user(d["turno"])
    files=[]
    if t_path and os.path.exists(t_path): files.append(discord.File(t_path,filename="tablero.jpg"))
    emb=discord.Embed(title=f"TRUCO {d['nombres'][u1]} vs {d['nombres'][u2]}",description=f"{txt}\n➡️ Turno de {d['nombres'][d['turno']]} - Ve su tablero",color=0xe74c3c)
    if files: emb.set_image(url="attachment://tablero.jpg")
    await i.followup.send(embed=emb, files=files if files else None)
  else:
   d["turno"]= [x for x in d["puntos"].keys() if x!=self.owner][0]
   t_path=tab_user(d["turno"])
   files=[]
   if t_path and os.path.exists(t_path): files.append(discord.File(t_path,filename="tablero.jpg"))
   emb=discord.Embed(title="TRUCO 1vs1",description=f"➡️ Turno de {d['nombres'][d['turno']]} - Ahora ve SU tablero",color=0xe74c3c)
   if files: emb.set_image(url="attachment://tablero.jpg")
   await i.followup.send(embed=emb, files=files if files else None)

class ViewAmigos(discord.ui.View):
 def __init__(self,pid,j1,j2,m1,m2):
  super().__init__(timeout=600)
  self.pid=pid
  for c in m1: self.add_item(CartaAmigo(c,j1,pid))
  for c in m2: 
   b=CartaAmigo(c,j2,pid); b.row=1; self.add_item(b)
  truco=discord.ui.Button(label="TRUCO",style=discord.ButtonStyle.danger,row=2)
  envido=discord.ui.Button(label="ENVIDO",style=discord.ButtonStyle.success,row=2)
  async def truco_cb(inter):
   if inter.user.id not in [j1,j2]: return
   for child in self.children:
    if child.label in ["TRUCO","ENVIDO"]: child.disabled=True
   await inter.response.edit_message(view=self)
   await inter.followup.send(f"{inter.user.mention} cantó TRUCO!",view=TrucoRespAmigo(pid))
  async def envido_cb(inter):
   if inter.user.id not in [j1,j2]: return
   if partidas[pid].get("envido_jugado"): await inter.response.send_message("Ya cantaron envido",ephemeral=True); return
   for child in self.children:
    if child.label in ["TRUCO","ENVIDO"]: child.disabled=True
   partidas[pid]["envido_jugado"]=True
   await inter.response.edit_message(view=self)
   await inter.followup.send(f"{inter.user.mention} cantó ENVIDO!",view=EnvidoRespAmigo(pid))
  truco.callback=truco_cb; envido.callback=envido_cb
  self.add_item(truco); self.add_item(envido)
  self.add_item(ExpOpen(j1))
  self.add_item(S(j1))

@tree.command(name="jugar",description="Jugar vs bot +250 o vs amigo")
async def jugar(i:discord.Interaction, oponente: discord.Member = None):
 if oponente and oponente.id!=i.user.id and not oponente.bot:
  m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m)
  mj=[m.pop() for _ in range(3)]; mo=[m.pop() for _ in range(3)]
  pid=f"{i.user.id}_{oponente.id}_{random.randint(1,99999)}"
  partidas[pid]={"jugadas":{},"puntos":{i.user.id:0,oponente.id:0},"nombres":{i.user.id:i.user.display_name,oponente.id:oponente.display_name},"turno":i.user.id,"mano":{i.user.id:mj, oponente.id:mo},"envido_jugado":False}
  t_path=tab_user(i.user.id)
  files=[]
  if t_path and os.path.exists(t_path): files.append(discord.File(t_path,filename="tablero.jpg"))
  emb=discord.Embed(title=f"TRUCO {i.user.display_name} vs {oponente.display_name}",description=f"A 2 puntos\n➡️ Turno de {i.user.display_name} - Ve SU tablero",color=0xe74c3c)
  if files: emb.set_image(url="attachment://tablero.jpg")
  await i.response.send_message(embed=emb,view=ViewAmigos(pid,i.user.id,oponente.id,mj,mo),files=files if files else None)
  return
 m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m)
 mj=[m.pop() for _ in range(3)]; mb=[m.pop() for _ in range(3)]
 partidas[i.user.id]={"bot":mb,"mano_jugador":mj,"mano_bot":mb.copy(),"pj":0,"pb":0,"truco_nivel":1,"envido_jugado":False}
 t=tab_user(i.user.id); a=av()
 emb=discord.Embed(title="TRUCO - a 2 puntos",description=f"{i.user.mention} Mano: {', '.join([f'{c[0]} de {c[1]}' for c in mj])}\nEnvido tuyo: {calc_envido(mj)} | Truco vale 1",color=0x1e8449)
 fs=[]
 if t and os.path.exists(t): fs.append(discord.File(t,filename="t.jpg")); emb.set_image(url="attachment://t.jpg")
 if a and os.path.exists(a): fs.append(discord.File(a,filename="b.jpg")); emb.set_thumbnail(url="attachment://b.jpg")
 await i.response.send_message(embed=emb,view=V(i.user.id,mj),files=fs if fs else None)

@tree.command(name="tienda",description="Tienda con 3 apartados")
async def tienda(i:discord.Interaction):
 ensure_user(i.user.id)
 data=load_u(); coins=data.get(str(i.user.id),{}).get("coins",0)
 await i.response.send_message(embed=discord.Embed(title=f"🛒 TIENDA - {coins} coins",description="Usa los botones de abajo para cambiar: TABLEROS / PODERES / EXPRESIONES\n\nEn EXPRESIONES si equipas uno nuevo se va el anterior (equipado unico)",color=0xf1c40f),view=TiendaView(i.user.id,"tableros"), ephemeral=True)

@tree.command(name="comprar",description="Comprar")
async def comprar(i:discord.Interaction, tablero: str):
 key=tablero.lower()
 for k in PRECIOS:
  if k in key or key in k: key=k; break
 if key not in PRECIOS: await i.response.send_message("No existe"); return
 data=ensure_user(i.user.id); s=str(i.user.id)
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
 data=ensure_user(i.user.id); s=str(i.user.id)
 if s not in data or (key!="default" and key not in data[s]["owned"]): await i.response.send_message("No lo tenes"); return
 data[s]["equipado"]=key; save_u(data)
 t=tab_user(i.user.id)
 if t and os.path.exists(t):
  await i.response.send_message(f"Equipaste {key}",file=discord.File(t,filename="tab.jpg"))
 else: await i.response.send_message(f"Equipaste {key}")

@tree.command(name="perfil",description="Perfil")
async def perfil(i:discord.Interaction):
 ensure_user(i.user.id)
 data=load_u(); s=str(i.user.id)
 c=data.get(s,{}).get("coins",0)
 poderes=data.get(s,{}).get("poderes",{})
 exp=data.get(s,{}).get("exp_equipado","DEFAULT")
 await i.response.send_message(f"💰 {c} coins\n🎭 Expresion equipada: {exp}\n✨ Poderes: {poderes}")

@tree.command(name="codigos",description="Codigo")
async def codigos(i:discord.Interaction, codigo: str):
 code_upper=codigo.upper()
 code_original=codigo
 data=ensure_user(i.user.id); s=str(i.user.id)
 data=load_u(); s=str(i.user.id)
 # buscar code sin importar mayusculas
 found=None
 for k in CODIGOS:
  if k.upper()==code_upper: found=k; break
 if not found:
  await i.response.send_message("❌ Codigo invalido"); return
 if found in data[s]["codigos"]:
  await i.response.send_message("Ya canjeado"); return
  
 if found=="SPRITE":
  data[s]["owned"].append("espiritus") if "espiritus" not in data[s]["owned"] else None
  data[s]["equipado"]="espiritus"
  data[s]["codigos"].append(found); save_u(data)
  t=buscar_tablero("espiritus")
  await i.response.send_message(f"✅ Code {found} canjeado! Desbloqueaste TABLERO ESPIRITUS",file=discord.File(t,filename="esp.jpg") if t and os.path.exists(t) else None)
  return
 if found=="VICTORY ROYALE":
  data[s]["owned"].append("fortnite") if "fortnite" not in data[s]["owned"] else None
  data[s]["equipado"]="fortnite"
  data[s]["codigos"].append(found); save_u(data)
  t=buscar_tablero("fortnite")
  await i.response.send_message(f"✅ Code {found} canjeado! Desbloqueaste TABLERO FORTNITE #1 Victory Royale",file=discord.File(t,filename="fort.jpg") if t and os.path.exists(t) else None)
  return
 if found in ["TRUCO!","1_ESPADA"]:
  if found=="TRUCO!": data[s]["poderes"]["MAGO"]=data[s]["poderes"].get("MAGO",0)+1
  if found=="1_ESPADA": data[s]["poderes"]["MAGO"]=data[s]["poderes"].get("MAGO",0)+1
  data[s]["codigos"].append(found); save_u(data)
  await i.response.send_message(f"✅ Code {found} -> +1 MAGO! Tenes {data[s]['poderes']['MAGO']}"); return

 data[s]["coins"]+=CODIGOS[found]; data[s]["codigos"].append(found); save_u(data)
 await i.response.send_message(f"+{CODIGOS[found]} coins! Total {data[s]['coins']}")

@tree.command(name="ayuda",description="Ayuda")
async def ayuda(i:discord.Interaction):
 e=discord.Embed(title="AYUDA ACTU DEFINITIVA",description="/jugar - vs bot / @amigo\n/tienda -> 3 apartados: TABLEROS / PODERES x1 x10 / EXPRESIONES (equipado unico, se reemplaza)\n/codigos SPRITE = espiritus, VICTORY ROYALE = fortnite\n/equipar y /comprar siguen\nTableros: canchas 1000, springtrap 1250, creeper/minecraft 1500",color=0x9b59b6)
 await i.response.send_message(embed=e)

@bot.event
async def on_ready():
 await tree.sync()
 print("ACTU DEFINITIVA: Precios iguales canchas, springtrap 1250, creeper/minecraft 1500, VICTORY ROYALE, poderes x1/x10, expresiones reemplazo")

bot.run(os.getenv("DISCORD_TOKEN"))

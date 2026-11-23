import discord, random, os, json, asyncio
from discord import app_commands
from discord.app_commands import Choice
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

# FIX: gamer SACADO de venta, solo por codigo GAMER
PRECIOS={"river":1000,"boca":1000,"san lorenzo":1000,"racing":1000,"springtrap":1250,"creeper":1500,"minecraft":1500,"diamante":1800,"oro":1200}
CODIGOS={"TRUCO2026":1000,"navidad_se_acerca":350,"7_ORO":350,"TRUCO!":0,"1_ESPADA":0,"SPRITE":0,"VICTORY ROYALE":0,"GAMER":0}
PODERES_PRECIO={"MAGO":{"x1":400,"x10":3500},"OJO":{"x1":350,"x10":3000},"ESCUDO":{"x1":500,"x10":4500},"LADRON":{"x1":450,"x10":4000}}
EXPRESIONES_TIENDA={"DEFAULT":{"precio":0,"txt":["HOLA","GG"]},"AMIGABLE":{"precio":150,"txt":["HOLA","GG"]},"KAOMOJI":{"precio":250,"txt":["WOW"]},"ARTE":{"precio":400,"txt":["ARTE"]}}

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
  data[s]={"coins":0,"equipado":"default","owned":["default"],"codigos":[],"poderes":{"MAGO":0,"OJO":0,"ESCUDO":0,"LADRON":0},"owned_exp":["DEFAULT"],"exp_equipado":"DEFAULT","wins_bot":0,"wins_amigo":0}
 data[s].setdefault("poderes",{"MAGO":0,"OJO":0,"ESCUDO":0,"LADRON":0})
 data[s].setdefault("owned_exp",["DEFAULT"])
 data[s].setdefault("exp_equipado","DEFAULT")
 data[s].setdefault("wins_bot",0)
 data[s].setdefault("wins_amigo",0)
 save_u(data)
 return data

def add_coins(uid,cant):
 data=load_u(); s=str(uid)
 ensure_user(uid); data=load_u()
 data[s]["coins"]=data[s].get("coins",0)+cant
 save_u(data); return data[s]["coins"]

def add_win(uid,tipo):
 data=load_u(); s=str(uid)
 ensure_user(uid); data=load_u()
 if tipo=="bot": data[s]["wins_bot"]=data[s].get("wins_bot",0)+1
 else: data[s]["wins_amigo"]=data[s].get("wins_amigo",0)+1
 save_u(data)

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
 if eq=="default": return "tableros/Tablero.jpg" if os.path.exists("tableros/Tablero.jpg") else None
 t=buscar_tablero(eq)
 return t if t and os.path.exists(t) else "tableros/Tablero.jpg"

def av():
 for x in ["bot_rojo.png","tableros/bot_rojo.png"]:
  if os.path.exists(x): return x
 return None

# --- EQUIPAR DESPLEGABLE ---
class TableroSelect(discord.ui.Select):
 def __init__(self,owner):
  self.owner=owner
  data=load_u(); s=str(owner)
  owned=data.get(s,{}).get("owned",["default"]) if s in data else ["default"]
  if "default" not in owned: owned=["default"]+owned
  nombres_lindos={"default":"Default","river":"River","boca":"Boca","san lorenzo":"San Lorenzo","racing":"Racing","springtrap":"Springtrap","creeper":"Creeper","minecraft":"Minecraft","diamante":"Diamante","oro":"Oro","gamer":"GAMER (Secreto)","espiritus":"ESPIRITUS (Secreto - SPRITE)","fortnite":"FORTNITE (Secreto - VICTORY ROYALE)"}
  options=[]
  for tab in owned:
   # SOLO muestra los secretos SI los canjeaste (porque solo recorre owned)
   label=nombres_lindos.get(tab, tab.upper())
   emoji="🔒" if tab in ["gamer","espiritus","fortnite"] else "🃏"
   options.append(discord.SelectOption(label=label, value=tab, emoji=emoji))
  super().__init__(placeholder="📋 TABLEROS - Incluye SECRETOS si los canjeaste", min_values=1, max_values=1, options=options[:25])
 async def callback(self,i):
  if i.user.id!=self.owner: return
  data=load_u(); s=str(i.user.id)
  data[s]["equipado"]=self.values[0]; save_u(data)
  t=tab_user(i.user.id)
  if t and os.path.exists(t):
   await i.response.send_message(f"✅ Equipaste TABLERO **{self.values[0].upper()}**", file=discord.File(t,filename="tablero.jpg"), ephemeral=True)
  else:
   await i.response.send_message(f"✅ Equipaste TABLERO **{self.values[0].upper()}**", ephemeral=True)

class ExpresionSelect(discord.ui.Select):
 def __init__(self,owner):
  self.owner=owner
  data=load_u(); s=str(owner)
  owned=data.get(s,{}).get("owned_exp",["DEFAULT"]) if s in data else ["DEFAULT"]
  options=[discord.SelectOption(label=exp, value=exp, emoji="💬") for exp in owned]
  super().__init__(placeholder="💬 EXPRESIONES - Equipado unico", min_values=1, max_values=1, options=options[:25])
 async def callback(self,i):
  if i.user.id!=self.owner: return
  data=load_u(); s=str(i.user.id)
  data[s]["exp_equipado"]=self.values[0]; save_u(data)
  await i.response.send_message(f"✅ Equipaste EXPRESION **{self.values[0]}**", ephemeral=True)

class EquiparView(discord.ui.View):
 def __init__(self,owner):
  super().__init__(timeout=180)
  self.add_item(TableroSelect(owner))
  self.add_item(ExpresionSelect(owner))

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
  if i.user.id!=self.owner: return
  data=load_u(); s=str(i.user.id)
  if self.nombre in data[s]["owned"]:
   data[s]["equipado"]=self.nombre; save_u(data)
   await i.response.edit_message(embed=discord.Embed(title=f"Equipaste {self.nombre.upper()} ✅",color=0x2ecc71),view=TiendaView(self.owner,"tableros"))
  else:
   if data[s]["coins"]<self.precio: await i.response.send_message(f"Te faltan {self.precio-data[s]['coins']} coins",ephemeral=True); return
   data[s]["coins"]-=self.precio; data[s]["owned"].append(self.nombre); save_u(data)
   await i.response.edit_message(embed=discord.Embed(title=f"Compraste {self.nombre.upper()} ✅",color=0xf1c40f),view=TiendaView(self.owner,"tableros"))

class BotonPoder(discord.ui.Button):
 def __init__(self,nombre,tipo,precio,owner):
  self.nombre=nombre; self.tipo=tipo; self.precio=precio; self.owner=owner
  super().__init__(label=f"{nombre} {tipo} - {precio}",style=discord.ButtonStyle.primary)
 async def callback(self,i):
  if i.user.id!=self.owner: return
  data=load_u(); s=str(i.user.id)
  if data[s]["coins"]<self.precio: await i.response.send_message(f"Te faltan",ephemeral=True); return
  cant=1 if self.tipo=="x1" else 10
  data[s]["coins"]-=self.precio; data[s]["poderes"][self.nombre]+=cant; save_u(data)
  await i.response.send_message(f"Compraste {self.nombre} {self.tipo}! Aparece en partida",ephemeral=True)

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
  if self.nombre in data[s]["owned_exp"]:
   data[s]["exp_equipado"]=self.nombre; save_u(data)
   await i.response.edit_message(embed=discord.Embed(title=f"Equipaste {self.nombre} ✅",color=0x2ecc71),view=TiendaView(self.owner,"expresiones"))
  else:
   data[s]["coins"]-=self.precio; data[s]["owned_exp"].append(self.nombre); save_u(data)
   await i.response.edit_message(embed=discord.Embed(title=f"Compraste {self.nombre} ✅",color=0xf1c40f),view=TiendaView(self.owner,"expresiones"))

class TiendaView(discord.ui.View):
 def __init__(self,owner,categoria="tableros"):
  super().__init__(timeout=300)
  self.owner=owner
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

class TrucoResp(discord.ui.View):
 def __init__(self,owner): super().__init__(timeout=30); self.owner=owner
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b): d=partidas.get(self.owner); d["truco_nivel"]+=1; await i.response.send_message("QUIERO!"); self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b): d=partidas.get(self.owner); d["pj"]=2; await i.response.send_message("NO QUIERO!"); self.stop()
class EnvidoResp(discord.ui.View):
 def __init__(self,owner): super().__init__(timeout=30); self.owner=owner
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b): d=partidas.get(self.owner); d["pj"]+=2; await i.response.send_message("QUIERO ENVIDO"); d["envido_jugado"]=True; self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b): d=partidas.get(self.owner); d["pj"]+=1; await i.response.send_message("+1"); self.stop()
class TrucoRespAmigo(discord.ui.View):
 def __init__(self,pid): super().__init__(timeout=30); self.pid=pid
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b): await i.response.send_message("QUIERO!"); self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b): d=partidas.get(self.pid); ganador=[x for x in d["puntos"].keys() if x!=i.user.id][0]; d["puntos"][ganador]+=1; await i.response.send_message("NO QUIERO!"); self.stop()
class EnvidoRespAmigo(discord.ui.View):
 def __init__(self,pid): super().__init__(timeout=30); self.pid=pid
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b): d=partidas.get(self.pid); d["puntos"][list(d["mano"].keys())[0]]+=2; await i.response.send_message("+2!"); self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b): d=partidas.get(self.pid); ganador=[x for x in d["puntos"].keys() if x!=i.user.id][0]; d["puntos"][ganador]+=1; await i.response.send_message("+1"); self.stop()
class ExpBtn(discord.ui.Button):
 def __init__(self,txt,label,o): self.txt=txt; self.o=o; super().__init__(label=label,style=discord.ButtonStyle.secondary)
 async def callback(self,i): await i.response.send_message(f"{i.user.display_name}: {self.txt}")
class ExpView(discord.ui.View):
 def __init__(self,o):
  super().__init__(timeout=60)
  data=load_u(); s=str(o); pack=data.get(s,{}).get("exp_equipado","DEFAULT"); txts=EXPRESIONES_TIENDA.get(pack,EXPRESIONES_TIENDA["DEFAULT"])["txt"]
  for t in txts[:4]: self.add_item(ExpBtn(t,t[:20],o))
class C(discord.ui.Button):
 def __init__(self,carta,owner): self.carta=carta; self.owner=owner; super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary,row=0)
 async def callback(self,i):
  if i.user.id!=self.owner: return
  d=partidas.get(self.owner); self.disabled=True; await i.response.edit_message(view=self.view)
  await i.followup.send(f"Tiraste {self.carta[0]} de {self.carta[1]}"); await asyncio.sleep(1)
  cb=d["bot"].pop(0); vy=v(self.carta[0],self.carta[1]); vb=v(cb[0],cb[1])
  if vy>vb: d["pj"]+=1; txt=f"Ganaste {d['pj']}-{d['pb']}"
  else: d["pb"]+=1; txt=f"Perdiste {d['pj']}-{d['pb']}"
  if d["pj"]>=2 or d["pb"]>=2 or len(d["bot"])==0:
   if d["pj"]>d["pb"]: add_coins(self.owner,250); add_win(self.owner,"bot"); txt+=f" GANASTE +250!"
   partidas.pop(self.owner,None)
  await i.followup.send(txt)
class T(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="TRUCO",style=discord.ButtonStyle.danger,row=1)
 async def callback(self,i): await i.response.edit_message(view=self.view); await i.followup.send("TRUCO!",view=TrucoResp(self.o))
class E(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="ENVIDO",style=discord.ButtonStyle.success,row=1)
 async def callback(self,i): await i.response.edit_message(view=self.view); await i.followup.send("ENVIDO!",view=EnvidoResp(self.o))
class S(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="SALIR",style=discord.ButtonStyle.secondary,row=1)
 async def callback(self,i): partidas.pop(self.o,None); await i.response.edit_message(content="Saliste",view=None)
class ExpOpen(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="Expresiones",style=discord.ButtonStyle.secondary,row=1)
 async def callback(self,i): await i.response.send_message("Elegi:",view=ExpView(self.o),ephemeral=True)
class V(discord.ui.View):
 def __init__(self,o,m): super().__init__(timeout=600); [self.add_item(C(c,o)) for c in m]; self.add_item(T(o)); self.add_item(E(o)); self.add_item(ExpOpen(o)); self.add_item(S(o))
class CartaAmigo(discord.ui.Button):
 def __init__(self,carta,owner,pid): self.carta=carta; self.owner=owner; self.pid=pid; super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary)
 async def callback(self,i):
  d=partidas.get(self.pid)
  if not d or i.user.id!=self.owner: return
  d["jugadas"][self.owner]=self.carta; self.disabled=True; await i.response.edit_message(view=self.view)
  if len(d["jugadas"])==2:
   u1,u2=list(d["jugadas"].keys()); ganador=u1 if v(d["jugadas"][u1][0],d["jugadas"][u1][1])>v(d["jugadas"][u2][0],d["jugadas"][u2][1]) else u2
   add_coins(ganador,250); add_win(ganador,"amigo"); partidas.pop(self.pid,None)
   await i.followup.send(f"Gana {d['nombres'][ganador]} +250!")
class ViewAmigos(discord.ui.View):
 def __init__(self,pid,j1,j2,m1,m2):
  super().__init__(timeout=600); self.pid=pid
  for c in m1: self.add_item(CartaAmigo(c,j1,pid))
  for c in m2: self.add_item(CartaAmigo(c,j2,pid))
  truco=discord.ui.Button(label="TRUCO",style=discord.ButtonStyle.danger,row=2); envido=discord.ui.Button(label="ENVIDO",style=discord.ButtonStyle.success,row=2)
  async def truco_cb(inter): await inter.response.edit_message(view=self); await inter.followup.send("TRUCO!",view=TrucoRespAmigo(pid))
  async def envido_cb(inter): await inter.response.edit_message(view=self); await inter.followup.send("ENVIDO!",view=EnvidoRespAmigo(pid))
  truco.callback=truco_cb; envido.callback=envido_cb; self.add_item(truco); self.add_item(envido)

@tree.command(name="jugar",description="Jugar vs bot o amigo")
async def jugar(i:discord.Interaction, oponente: discord.Member = None):
 if oponente and oponente.id!=i.user.id and not oponente.bot:
  m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m); mj=[m.pop() for _ in range(3)]; mo=[m.pop() for _ in range(3)]
  pid=f"{i.user.id}_{oponente.id}_{random.randint(1,99999)}"
  partidas[pid]={"jugadas":{},"puntos":{i.user.id:0,oponente.id:0},"nombres":{i.user.id:i.user.display_name,oponente.id:oponente.display_name},"turno":i.user.id,"mano":{i.user.id:mj, oponente.id:mo},"envido_jugado":False}
  await i.response.send_message(embed=discord.Embed(title=f"TRUCO {i.user.display_name} vs {oponente.display_name}",color=0xe74c3c),view=ViewAmigos(pid,i.user.id,oponente.id,mj,mo)); return
 m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m); mj=[m.pop() for _ in range(3)]; mb=[m.pop() for _ in range(3)]
 partidas[i.user.id]={"bot":mb,"mano_jugador":mj,"mano_bot":mb.copy(),"pj":0,"pb":0,"truco_nivel":1,"envido_jugado":False}
 await i.response.send_message(embed=discord.Embed(title="TRUCO",color=0x1e8449),view=V(i.user.id,mj))

@tree.command(name="tienda",description="Tienda de truco")
@app_commands.choices(categoria=[
    Choice(name="TABLEROS", value="tableros"),
    Choice(name="PODERES", value="poderes"),
    Choice(name="EXPRESIONES", value="expresiones"),
])
async def tienda(i:discord.Interaction, categoria: str):
 await i.response.defer(ephemeral=True)
 ensure_user(i.user.id)
 data=load_u(); coins=data.get(str(i.user.id),{}).get("coins",0)
 embed=discord.Embed(title=f"🛒 TIENDA {categoria.upper()} - {coins} coins",color=0xf1c40f)
 if categoria=="tableros": embed.description="Compra y equipa tableros (GAMER solo por codigo)"
 elif categoria=="poderes": embed.description="Compra poderes x1 y x10 - aparecen en partida"
 else: embed.description="Expresiones - equipado unico"
 await i.followup.send(embed=embed,view=TiendaView(i.user.id,categoria),ephemeral=True)

@tree.command(name="ranking",description="Ranking")
async def ranking(i:discord.Interaction):
 await i.response.defer()
 data=load_u()
 if not data: await i.followup.send("No hay datos"); return
 top=sorted(data.items(), key=lambda x: x[1].get("wins_bot",0)+x[1].get("wins_amigo",0), reverse=True)[:10]
 desc=""
 for idx,(uid,info) in enumerate(top,1):
  try: user=await bot.fetch_user(int(uid)); nombre=user.display_name
  except: nombre=f"ID {uid}"
  total=info.get("wins_bot",0)+info.get("wins_amigo",0)
  desc+=f"**{idx}. {nombre}** - {total} wins (Bot {info.get('wins_bot',0)} | Amigo {info.get('wins_amigo',0)})\n"
 await i.followup.send(embed=discord.Embed(title="🏆 RANKING",description=desc,color=0xf1c40f))

@tree.command(name="equipar",description="Equipar tus cosas con desplegable")
async def equipar(i:discord.Interaction):
 await i.response.defer(ephemeral=True)
 ensure_user(i.user.id)
 data=load_u(); s=str(i.user.id)
 owned_tabs=data.get(s,{}).get("owned",["default"])
 owned_exps=data.get(s,{}).get("owned_exp",["DEFAULT"])
 poderes=data.get(s,{}).get("poderes",{})
 emb=discord.Embed(title="🎒 EQUIPAR",description=f"TABLEROS: {len(owned_tabs)} (SECRETOS solo aparecen si los canjeaste)\nEXPRESIONES: {len(owned_exps)}\nPODERES: {poderes} (aparecen en partida, no se equipan)\n\nUsa los desplegables:",color=0x2ecc71)
 await i.followup.send(embed=emb,view=EquiparView(i.user.id),ephemeral=True)

@tree.command(name="perfil",description="Perfil")
async def perfil(i:discord.Interaction):
 ensure_user(i.user.id); data=load_u(); s=str(i.user.id)
 await i.response.send_message(f"💰 {data[s]['coins']} 🏆 Bot {data[s]['wins_bot']} Amigo {data[s]['wins_amigo']}")

@tree.command(name="codigos",description="Canjear codigo - VICTORY ROYALE es el de fortnite")
async def codigos(i:discord.Interaction, codigo: str):
 await i.response.defer()
 ensure_user(i.user.id); data=load_u(); s=str(i.user.id)
 code_upper=codigo.upper()
 found=None
 for k in CODIGOS:
  if k.upper()==code_upper: found=k; break
 if not found:
  await i.followup.send("❌ Codigo invalido"); return
 if found in data[s]["codigos"]:
  await i.followup.send("❌ Ya canjeado"); return

 if found=="SPRITE":
  data[s]["owned"].append("espiritus") if "espiritus" not in data[s]["owned"] else None
  data[s]["equipado"]="espiritus"; data[s]["codigos"].append(found); save_u(data)
  t=buscar_tablero("espiritus")
  emb=discord.Embed(title="✅ CANJEADO!",description="🎉 **Conseguiste el tablero SECRETO de ESPIRITUS!**",color=0x9b59b6)
  if t and os.path.exists(t): await i.followup.send(embed=emb,file=discord.File(t,filename="esp.jpg"))
  else: await i.followup.send(embed=emb)
  return
 if found=="VICTORY ROYALE":
  data[s]["owned"].append("fortnite") if "fortnite" not in data[s]["owned"] else None
  data[s]["equipado"]="fortnite"; data[s]["codigos"].append(found); save_u(data)
  t=buscar_tablero("fortnite")
  emb=discord.Embed(title="✅ CANJEADO!",description="🎉 **Conseguiste el tablero SECRETO de FORTNITE!**\nUsa /equipar para verlo, es con VICTORY ROYALE",color=0x9b59b6)
  if t and os.path.exists(t): await i.followup.send(embed=emb,file=discord.File(t,filename="fortnite.jpg"))
  else: await i.followup.send(embed=emb)
  return
 if found=="GAMER":
  data[s]["owned"].append("gamer") if "gamer" not in data[s]["owned"] else None
  data[s]["equipado"]="gamer"; data[s]["codigos"].append(found); save_u(data)
  t=buscar_tablero("gamer")
  emb=discord.Embed(title="✅ CANJEADO!",description="🎮 **Conseguiste el tablero SECRETO GAMER!**",color=0x00ff00)
  if t and os.path.exists(t): await i.followup.send(embed=emb,file=discord.File(t,filename="gamer.jpg"))
  else: await i.followup.send(embed=emb)
  return
 if found in ["TRUCO!","1_ESPADA"]:
  data[s]["poderes"]["MAGO"]=data[s]["poderes"].get("MAGO",0)+1; data[s]["codigos"].append(found); save_u(data)
  await i.followup.send(f"✨ **Conseguiste 1 poder MAGO!** Total: {data[s]['poderes']['MAGO']}"); return

 data[s]["coins"]+=CODIGOS[found]; data[s]["codigos"].append(found); save_u(data)
 await i.followup.send(f"💰 **+{CODIGOS[found]} coins!** Total: {data[s]['coins']}")

@tree.command(name="ayuda",description="Ayuda")
async def ayuda(i:discord.Interaction):
 await i.response.send_message(embed=discord.Embed(title="AYUDA",description="/tienda tableros/poderes/expresiones\n/equipar desplegable TABLEROS+EXPRESIONES (secretos solo si canjeados)\n/codigos: SPRITE, VICTORY ROYALE=fortnite, GAMER=gamer\nGAMER no se vende\n/ranking",color=0x9b59b6))

@bot.event
async def on_ready():
 await tree.sync()
 print("FIX COMPLETO: gamer no venta + VICTORY ROYALE + equipar secretos solo si canjeado")

bot.run(os.getenv("DISCORD_TOKEN"))

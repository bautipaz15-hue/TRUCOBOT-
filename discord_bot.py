import discord, random, os, json, asyncio, time, requests
from discord import app_commands
from discord.app_commands import Choice
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def h(): return "ok BOT TRUCO V6.2 FIX CARTAS PRIVADAS + NO TOCAR OTRAS PARTIDAS"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
Thread(target=run_flask, daemon=True).start()

def keep_alive_v5():
    while True:
        time.sleep(600)
        try:
            url = os.environ.get("RENDER_EXTERNAL_URL", "https://trucobot-athd.onrender.com")
            requests.get(url, timeout=10)
            print("SELF PING V6.2 OK")
        except: pass
Thread(target=keep_alive_v5, daemon=True).start()

intents=discord.Intents.default()
intents.message_content=True
bot=discord.Client(intents=intents)
tree=app_commands.CommandTree(bot)
partidas={}
salas_jugar={}
ultimo_comando={}
TIMEOUT_SEGUNDOS=120

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

PRECIOS={"river":1000,"boca":1000,"san lorenzo":1000,"racing":1000,"springtrap":1250,"creeper":1500,"minecraft":1500,"diamante":1800,"oro":1200}
CODIGOS={"TRUCO2026":1000,"navidad_se_acerca":350,"7_ORO":350,"TRUCO!":0,"1_ESPADA":0,"SPRITE":0,"VICTORY ROYALE":0,"GAMER":0}
PODERES_PRECIO={"MAGO":{"x1":400,"x10":3500},"OJO":{"x1":350,"x10":3000},"ESCUDO":{"x1":500,"x10":4500},"LADRON":{"x1":450,"x10":4000}}
EXPRESIONES_TIENDA={
 "DEFAULT":{"precio":0,"txt":["HOLA 👋","GG 😎","¿ESTAS BUSCANDO EN GOOGLE COMO SE JUEGA? 🤓","TRUCO! 🔥"]},
 "AMIGABLE":{"precio":150,"txt":["HOLA","GG"]},
 "KAOMOJI":{"precio":250,"txt":["WOW"]},
 "ARTE":{"precio":400,"txt":["───▄▀▀▀▄▄▄▄▄▄▄▀▀▀▄───\n───█▒▒░░░░░░░░░▒▒█───\n────█░░█░░░░░█░░█────\n─▄▄──█░░░▀█▀░░░█──▄▄─\n█░░█─▀▄░░░░░░░▄▀─█░░█","░▄▀▄▀▀▀▀▄▀▄░░░░░░░░░\n░█░░░░░░░░▀▄░░░░░░▄░\n█░░▀░░▀░░░░░▀▄▄░░█░█\n█░▄░█▀░▄░░░░░░░▀▀░░█\n█░░▀▀▀▀░░░░░░░░░░░░█\n█░░░░░░░░░░░░░░░░░░█\n█░░░░░░░░░░░░░░░░░░█\n░█░░▄▄░░▄▄▄▄░░▄▄░░█░\n░█░▄▀█░▄▀░░█░▄▀█░▄▀░\n░░▀░░░▀░░░░░▀░░░▀░░░"]}
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
 nombre=nombre.lower().strip().replace("_"," ").replace("-"," ")
 if "san" in nombre and "lorenzo" in nombre: nombre="san lorenzo"
 if "sanlorenzo" in nombre: nombre="san lorenzo"
 mapa={"default":["tablero.jpg","default"],"river":["river"],"boca":["boca"],"san lorenzo":["san lorenzo","sanlorenzo","san_lorenzo","casla","cuervo"],"racing":["racing"],"springtrap":["springtrap"],"creeper":["creeper"],"minecraft":["minecraft"],"diamante":["diamante"],"oro":["oro"],"gamer":["gamer"],"espiritus":["espiritus","sprite"],"fortnite":["fortnite","victory"]}
 posibles=mapa.get(nombre,[nombre])
 for f in os.listdir("tableros"):
  fl=f.lower()
  for p in posibles:
   if p in fl: return os.path.join("tableros",f)
 for f in os.listdir("tableros"):
  if nombre in f.lower(): return os.path.join("tableros",f)
 return "tableros/Tablero.jpg" if os.path.exists("tableros/Tablero.jpg") else None
def tab_user(uid):
 data=load_u(); s=str(uid)
 eq=data.get(s,{}).get("equipado","default") if s in data else "default"
 t=buscar_tablero(eq)
 if t and os.path.exists(t): return t
 return "tableros/Tablero.jpg" if os.path.exists("tableros/Tablero.jpg") else None
def check_spam(uid):
 ahora=time.time()
 ultimo=ultimo_comando.get(uid,0)
 if ahora-ultimo < 3: return False
 ultimo_comando[uid]=ahora
 return True

def get_file_embed_titulo(emb, uid):
    tpath = tab_user(uid)
    if tpath and os.path.exists(tpath):
        file = discord.File(tpath, filename="tablero.jpg")
        emb.set_image(url="attachment://tablero.jpg")
        return file, emb
    return None, emb

class JugarDeNuevoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🔄 JUGAR DE NUEVO", style=discord.ButtonStyle.success, emoji="🃏")
    async def replay(self, i, b):
        ensure_user(i.user.id)
        emb = discord.Embed(title="🎮 ELEGÍ MODO DE JUEGO", description="1V1 (2) | TRIO (6) | ESCUADRON (8)\nBOT arranca de una!\nRETRUCO, VALE 4, PODERES ✅", color=0x2ecc71)
        await i.response.send_message(embed=emb, view=JugarMenuView(i.user.id))

class TableroSelect(discord.ui.Select):
 def __init__(self,owner):
  self.owner=owner
  data=load_u(); s=str(owner)
  owned=data.get(s,{}).get("owned",["default"]) if s in data else ["default"]
  if "default" not in owned: owned=["default"]+owned
  nombres_lindos={"default":"Default","river":"River","boca":"Boca","san lorenzo":"San Lorenzo","racing":"Racing","springtrap":"Springtrap","creeper":"Creeper","minecraft":"Minecraft","diamante":"Diamante","oro":"Oro","gamer":"GAMER (Secreto)","espiritus":"ESPIRITUS (Secreto)","fortnite":"FORTNITE (Secreto)"}
  options=[]
  for tab in owned:
   label=nombres_lindos.get(tab, tab.upper())
   emoji="🔒" if tab in ["gamer","espiritus","fortnite"] else "🃏"
   options.append(discord.SelectOption(label=label, value=tab, emoji=emoji))
  super().__init__(placeholder="📋 TABLEROS", min_values=1, max_values=1, options=options[:25])
 async def callback(self,i):
  if i.user.id!=self.owner: return
  data=load_u(); s=str(i.user.id)
  data[s]["equipado"]=self.values[0]; save_u(data)
  await i.response.send_message(f"✅ Equipaste {self.values[0].upper()}", ephemeral=True)
class ExpresionSelect(discord.ui.Select):
 def __init__(self,owner):
  self.owner=owner
  data=load_u(); s=str(owner)
  owned=data.get(s,{}).get("owned_exp",["DEFAULT"]) if s in data else ["DEFAULT"]
  options=[]
  for exp in owned:
   lbl = exp[:20] if "\n" not in exp else "ARTE 🎨"
   options.append(discord.SelectOption(label=lbl, value=exp, emoji="💬"))
  super().__init__(placeholder="💬 EXPRESIONES", min_values=1, max_values=1, options=options[:25])
 async def callback(self,i):
  if i.user.id!=self.owner: return
  data=load_u(); s=str(i.user.id)
  data[s]["exp_equipado"]=self.values[0]; save_u(data)
  await i.response.send_message(f"✅ Equipaste EXPRESION", ephemeral=True)
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
  if i.user.id!=self.owner: await i.response.send_message("No es tu tienda",ephemeral=True); return
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
  if i.user.id!=self.owner: await i.response.send_message("No es tu tienda",ephemeral=True); return
  data=load_u(); s=str(i.user.id)
  if data[s]["coins"]<self.precio: await i.response.send_message(f"Te faltan",ephemeral=True); return
  cant=1 if self.tipo=="x1" else 10
  data[s]["coins"]-=self.precio; data[s]["poderes"][self.nombre]+=cant; save_u(data)
  await i.response.send_message(f"Compraste {self.nombre} {self.tipo}!",ephemeral=True)
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

class TrucoRespAmigo(discord.ui.View):
 def __init__(self,pid, nivel): super().__init__(timeout=30); self.pid=pid; self.nivel=nivel
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b):
  d=partidas.get(self.pid)
  if not d: return
  if i.user.id not in d["jugadores"]: await i.response.send_message("❌ No sos parte de esta partida",ephemeral=True); return
  d["last_action"]=time.time()
  if self.nivel==1: d["truco_nivel"]=2
  elif self.nivel==2: d["truco_nivel"]=3
  elif self.nivel==3: d["truco_nivel"]=4
  await i.response.send_message(f"🔥 QUIERO! Ahora vale **{d['truco_nivel']}**"); self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b):
  d=partidas.get(self.pid)
  if not d: return
  if i.user.id not in d["jugadores"]: await i.response.send_message("❌ No sos parte de esta partida",ephemeral=True); return
  ganador_id = [x for x in d["jugadores"] if x!=i.user.id][0] if len(d["jugadores"])>1 else list(d["puntos"].keys())[0]
  if d.get("tipo")=="larga":
      add_coins(ganador_id,100)
      await i.response.send_message(f"❌ NO QUIERO! {d['nombres'][ganador_id]} gana **+100 Trucoins**")
  else:
      add_coins(ganador_id,100)
      await i.response.send_message(f"❌ NO QUIERO! {d['nombres'][ganador_id]} gana mano + 100 Trucoins")
  d["puntos"][ganador_id]+=d.get("truco_nivel",1)
  if d.get("tipo")=="corta":
      partidas.pop(self.pid,None)
  self.stop()

class EnvidoRespAmigo(discord.ui.View):
 def __init__(self,pid): super().__init__(timeout=30); self.pid=pid
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b):
  d=partidas.get(self.pid)
  if not d: return
  if i.user.id not in d["jugadores"]: await i.response.send_message("❌ No es tu partida",ephemeral=True); return
  d["last_action"]=time.time()
  envidos={uid: calc_envido(d["manos"][uid]) for uid in d["jugadores"]}
  ganador = max(envidos, key=lambda k: envidos[k])
  d["puntos"][ganador]+=2
  await i.response.send_message(f"💰 QUIERO! Envidos: {envidos} -> Gana {d['nombres'][ganador]} +2"); self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b):
  d=partidas.get(self.pid)
  if not d: return
  if i.user.id not in d["jugadores"]: await i.response.send_message("❌ No es tu partida",ephemeral=True); return
  d["last_action"]=time.time()
  cantor = d.get("envido_cantor")
  if cantor: d["puntos"][cantor]+=1
  await i.response.send_message(f"💰 NO QUIERO! +1 para cantor"); self.stop()

class ExpBtn(discord.ui.Button):
 def __init__(self,txt,label,o): 
  self.txt=txt; self.o=o
  super().__init__(label=label,style=discord.ButtonStyle.secondary)
 async def callback(self,i): 
  if i.user.id!=self.o: await i.response.send_message("❌ No es tu partida",ephemeral=True); return
  if "\n" in self.txt:
   await i.response.send_message(f"**{i.user.display_name}:**\n```\n{self.txt}\n```")
  else:
   await i.response.send_message(f"{i.user.display_name}: {self.txt}")

class ExpView(discord.ui.View):
 def __init__(self,o):
  super().__init__(timeout=60)
  data=load_u(); s=str(o)
  pack=data.get(s,{}).get("exp_equipado","DEFAULT")
  txts=EXPRESIONES_TIENDA.get(pack,EXPRESIONES_TIENDA["DEFAULT"])["txt"]
  for idx, t in enumerate(txts[:5]):
   label = f"ARTE {idx+1} 🎨" if "\n" in t else t[:20]
   self.add_item(ExpBtn(t,label,o))

class C(discord.ui.Button):
 def __init__(self,carta,owner): self.carta=carta; self.owner=owner; super().__init__(label=f"{carta[0]} de {carta[1]} 🃏",style=discord.ButtonStyle.primary,row=0)
 async def callback(self,i):
  if i.user.id!=self.owner: await i.response.send_message("❌ No es tu carta",ephemeral=True); return
  if not check_spam(self.owner): await i.response.send_message("⏳ Anti-spam, espera 3 seg",ephemeral=True); return
  d=partidas.get(self.owner)
  if not d: return
  d["last_action"]=time.time()
  self.disabled=True
  await i.response.edit_message(view=self.view)
  await i.followup.send(f"🃏 Tiraste **{self.carta[0]} de {self.carta[1]}**")
  m = await i.followup.send("🤖 **BOT PENSANDO...**")
  await asyncio.sleep(1.2)
  try: await m.delete()
  except: pass
  if len(d["bot"]) == 0: return
  cb=d["bot"].pop(0)
  if self.carta in d["mano_jugador"]: d["mano_jugador"].remove(self.carta)
  vy=v(self.carta[0],self.carta[1]); vb=v(cb[0],cb[1])
  if vy>vb: d["pj"]+=1; txt=f"✨ **GANASTE 1 PUNTO!** 😎\n🤖 Bot: {cb[0]} de {cb[1]}\n📊 **{d['pj']} - {d['pb']}**"
  elif vy<vb: d["pb"]+=1; txt=f"💔 **PERDISTE 1 PUNTO** 😔\n🤖 Bot: {cb[0]} de {cb[1]}\n📊 **{d['pj']} - {d['pb']}**"
  else: txt=f"🤝 Empate\n🤖 Bot: {cb[0]} de {cb[1]}\n📊 **{d['pj']} - {d['pb']}**"
  if d["pj"]>=2 or d["pb"]>=2 or len(d["mano_jugador"])==0:
   if d["pj"]>d["pb"]: add_coins(self.owner,250); add_win(self.owner,"bot"); txt=f"🏆 **¡GANASTE +250!** 🎉\n📊 Final: {d['pj']}-{d['pb']}"
   else: txt=f"😭 **PERDISTE LA PARTIDA** 😔\n📊 Final: {d['pj']}-{d['pb']}"
   for child in self.view.children: child.disabled=True
   try: await i.edit_original_response(view=self.view)
   except: pass
   partidas.pop(self.owner,None)
   await i.followup.send(txt, view=JugarDeNuevoView())
   return
  await i.followup.send(txt)

class T(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="TRUCO 🔥",style=discord.ButtonStyle.danger,row=1)
 async def callback(self,i):
  if i.user.id!=self.o: await i.response.send_message("❌ No es tu turno",ephemeral=True); return
  d=partidas.get(self.o)
  if not d or d.get("truco_jugado"): return
  d["last_action"]=time.time()
  nivel_actual=d.get("truco_nivel",1)
  if nivel_actual>=4: await i.response.send_message("Ya es VALE 4",ephemeral=True); return
  d["truco_jugado"]=True
  for child in self.view.children:
   if isinstance(child, (T,E)): child.disabled=True
  await i.response.edit_message(view=self.view)
  if random.random() < 0.65:
   d["truco_nivel"]=nivel_actual+1
   labels={2:"TRUCO vale 2",3:"RETRUCO vale 3",4:"VALE 4"}
   await i.followup.send(f"🤖 Bot: **¡QUIERO {labels[d['truco_nivel']]}!** 😎")
   d["truco_jugado"]=False
   for child in self.view.children:
     if isinstance(child, T): child.disabled=False
   try: await i.edit_original_response(view=self.view)
   except: pass
  else:
   d["pj"]+=nivel_actual
   await i.followup.send(f"🤖 Bot: **NO QUIERO** 😔\n✨ **GANASTE {nivel_actual} PUNTO!** 😎\n📊 {d['pj']}-{d['pb']}")

class E(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="ENVIDO 💰",style=discord.ButtonStyle.success,row=1)
 async def callback(self,i):
  if i.user.id!=self.o: await i.response.send_message("❌ No es tu carta",ephemeral=True); return
  d=partidas.get(self.o)
  if not d or d.get("envido_jugado"): await i.response.send_message("Envido solo al principio",ephemeral=True); return
  d["last_action"]=time.time()
  d["envido_jugado"]=True
  for child in self.view.children:
   if isinstance(child, E): child.disabled=True
  await i.response.edit_message(view=self.view)
  mi_envido = calc_envido(d["mano_jugador_orig"])
  bot_envido = calc_envido(d["mano_bot_orig"])
  await i.followup.send(f"💰 Cantaste ENVIDO! Vos tenés **{mi_envido}**")
  await asyncio.sleep(0.7)
  quiere = random.random() < 0.6
  if not quiere:
   d["pj"]+=1
   await i.followup.send(f"🤖 Bot: Tengo {bot_envido} -> **NO QUIERO** 😔\n✨ **GANASTE 1 PUNTO!** 😎\n📊 {d['pj']}-{d['pb']}")
  else:
   await i.followup.send(f"🤖 Bot: Tengo **{bot_envido}** -> **¡QUIERO!** 😎")
   await asyncio.sleep(0.5)
   if mi_envido > bot_envido: d["pj"]+=2; await i.followup.send(f"✨ **GANASTE ENVIDO {mi_envido} vs {bot_envido}** 😎 +2\n📊 {d['pj']}-{d['pb']}")
   elif mi_envido < bot_envido: d["pb"]+=2; await i.followup.send(f"💔 **PERDISTE ENVIDO {mi_envido} vs {bot_envido}** 😔 +2 bot\n📊 {d['pj']}-{d['pb']}")
   else: await i.followup.send(f"🤝 Empate {mi_envido} vs {bot_envido}")
  for child in self.view.children:
   if isinstance(child, T): child.disabled=False
  try: await i.edit_original_response(view=self.view)
  except: pass

class PoderBtn(discord.ui.Button):
 def __init__(self,o,nombre): self.o=o; self.nombre=nombre; super().__init__(label=f"🔥 {nombre}",style=discord.ButtonStyle.danger,row=2)
 async def callback(self,i):
  if i.user.id!=self.o: await i.response.send_message("❌ No es tu poder",ephemeral=True); return
  data=load_u(); s=str(self.o)
  if data[s]["poderes"].get(self.nombre,0)<=0: await i.response.send_message(f"No tenes {self.nombre}",ephemeral=True); return
  data[s]["poderes"][self.nombre]-=1; save_u(data)
  await i.response.send_message(f"🔥 Usaste PODER {self.nombre}!",ephemeral=True)

class S(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="IRSE AL MAZO 🚪",style=discord.ButtonStyle.secondary,row=1)
 async def callback(self,i):
  if i.user.id!=self.o: await i.response.send_message("❌ No es tu partida",ephemeral=True); return
  d=partidas.get(self.o)
  if not d: return
  partidas.pop(self.o,None)
  await i.response.edit_message(content="🚪 Te fuiste al mazo 😔",view=None)

class ExpOpen(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="Expresiones 💬",style=discord.ButtonStyle.secondary,row=1)
 async def callback(self,i): 
  if i.user.id!=self.o: await i.response.send_message("❌ No es tu partida",ephemeral=True); return
  await i.response.send_message("💬 Elegi:",view=ExpView(self.o),ephemeral=True)

class V(discord.ui.View):
 def __init__(self,o,m):
  super().__init__(timeout=600)
  [self.add_item(C(c,o)) for c in m]
  self.add_item(T(o)); self.add_item(E(o)); self.add_item(ExpOpen(o)); self.add_item(S(o))
  data=load_u(); s=str(o)
  for poder in ["MAGO","OJO","ESCUDO","LADRON"]:
   if data.get(s,{}).get("poderes",{}).get(poder,0)>0:
     self.add_item(PoderBtn(o,poder))

# --- V6.2 FIX: CARTAS PRIVADAS ---
class CartaAmigoV4(discord.ui.Button):
 def __init__(self,carta,owner,pid):
  self.carta=carta; self.owner=owner; self.pid=pid
  super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary)
 async def callback(self,i):
  if i.user.id!=self.owner:
      await i.response.send_message("❌ No es tu carta! No podés tocar la mano del rival.", ephemeral=True)
      return
  d=partidas.get(self.pid)
  if not d:
      await i.response.send_message("❌ Esta partida ya terminó.", ephemeral=True)
      return
  if i.user.id not in d["jugadores"]:
      await i.response.send_message("❌ No sos parte de esta partida.", ephemeral=True)
      return
  if not check_spam(self.owner): await i.response.send_message("⏳ Anti-spam",ephemeral=True); return
  d["last_action"]=time.time()
  if self.owner in d["jugadas_ronda"]: await i.response.send_message("Ya jugaste esta ronda",ephemeral=True); return
  d["jugadas_ronda"][self.owner]=self.carta
  self.disabled=True
  try: await i.response.edit_message(view=self.view)
  except: pass
  await i.followup.send(f"🃏 {d['nombres'][self.owner]} tiró carta", ephemeral=True)
  await i.channel.send(f"🃏 {d['nombres'][self.owner]} tiró carta boca abajo")
  if len(d["jugadas_ronda"])==len(d["jugadores"]):
      mejor=None; ganador=None
      texto_ronda = ""
      for uid,carta in d["jugadas_ronda"].items():
          val=v(carta[0],carta[1])
          texto_ronda += f"**{d['nombres'][uid]}**: {carta[0]} de {carta[1]} | "
          if mejor is None or val>mejor: mejor=val; ganador=uid
      d["rondas_ganadas"][ganador]+=1
      await i.followup.send(f"🏁 Cartas reveladas: {texto_ronda}\nRonda para **{d['nombres'][ganador]}**")
      d["jugadas_ronda"]={}
      if max(d["rondas_ganadas"].values())>=2 or sum(d["rondas_ganadas"].values())>=3:
          ganador_mano = max(d["rondas_ganadas"], key=lambda k: d["rondas_ganadas"][k])
          puntos_mano = d.get("truco_nivel",1)
          d["puntos"][ganador_mano]+=puntos_mano
          await i.channel.send(f"🏆 Mano para **{d['nombres'][ganador_mano]}** +{puntos_mano} pts\nMarcador: { {d['nombres'][k]:v for k,v in d['puntos'].items()} }")
          if d["tipo"]=="corta":
              add_coins(ganador_mano,250); add_win(ganador_mano,"amigo")
              await i.channel.send(f"🎉 **GANA PARTIDA CORTA {d['nombres'][ganador_mano]} +250 Trucoins**", view=JugarDeNuevoView())
              partidas.pop(self.pid,None)
              return
          else:
              if d["puntos"][ganador_mano]>=d["puntos_para_ganar"]:
                  add_coins(ganador_mano,500); add_win(ganador_mano,"amigo")
                  await i.channel.send(f"👑 **¡{d['nombres'][ganador_mano]} GANA LA BATALLA LARGA! +500 Trucoins** 👑", view=JugarDeNuevoView())
                  partidas.pop(self.pid,None)
                  return
              else:
                  await nueva_mano_v4(self.pid,i.channel)

async def nueva_mano_v4(pid, channel):
 d=partidas.get(pid)
 if not d: return
 m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m)
 for uid in d["jugadores"]:
     d["manos"][uid]=[m.pop() for _ in range(3)]
 d["jugadas_ronda"]={}; d["rondas_ganadas"]={uid:0 for uid in d["jugadores"]}
 d["truco_nivel"]=1; d["envido_jugado"]=False; d["last_action"]=time.time()
 emb=discord.Embed(title=f"🃏 NUEVA MANO - {d['tipo'].upper()} a {d.get('puntos_para_ganar','1 mano')} pts", description=f"Jugadores: {', '.join([d['nombres'][uid] for uid in d['jugadores']])}\nMarcador: { {d['nombres'][k]:v for k,v in d['puntos'].items()} }\n\n👇 Cartas privadas enviadas", color=0xe74c3c)
 file, emb = get_file_embed_titulo(emb, d["jugadores"][0])
 if file: await channel.send(embed=emb, file=file, view=ViewAmigosPublico(pid))
 else: await channel.send(embed=emb, view=ViewAmigosPublico(pid))
 for uid in d["jugadores"]:
     try:
         emb_priv = discord.Embed(title=f"🃏 TUS CARTAS PRIVADAS", description=f"Solo vos ves esto - Partida {pid[:6]}", color=0x3498db)
         await channel.send(f"<@{uid}>", embed=emb_priv, view=ViewAmigosV4(pid, owner_id=uid))
     except: pass

class TrucoAmigoV4(discord.ui.Button):
 def __init__(self,pid,owner):
  self.pid=pid; self.owner=owner
  super().__init__(label="TRUCO 🔥",style=discord.ButtonStyle.danger,row=2)
 async def callback(self,i):
  if i.user.id not in partidas.get(self.pid,{}).get("jugadores",[]): await i.response.send_message("❌ No sos parte de esta partida",ephemeral=True); return
  d=partidas.get(self.pid)
  if not d: return
  nivel=d.get("truco_nivel",1)
  if nivel>=4: await i.response.send_message("Ya es VALE 4",ephemeral=True); return
  d["last_action"]=time.time()
  await i.response.send_message(f"🔥 **{d['nombres'][i.user.id]}** canta {'TRUCO' if nivel==1 else 'RETRUCO' if nivel==2 else 'VALE 4'}! Vale {nivel+1}", view=TrucoRespAmigo(self.pid,nivel))

class EnvidoAmigoV4(discord.ui.Button):
 def __init__(self,pid,owner):
  self.pid=pid; self.owner=owner
  super().__init__(label="ENVIDO 💰",style=discord.ButtonStyle.success,row=2)
 async def callback(self,i):
  if i.user.id not in partidas.get(self.pid,{}).get("jugadores",[]): await i.response.send_message("❌ No sos parte de esta partida",ephemeral=True); return
  d=partidas.get(self.pid)
  if not d or d.get("envido_jugado"): await i.response.send_message("Envido solo al principio",ephemeral=True); return
  if len(d["jugadas_ronda"])!=0: await i.response.send_message("Envido solo al principio de mano",ephemeral=True); return
  d["last_action"]=time.time()
  d["envido_jugado"]=True; d["envido_cantor"]=i.user.id
  envido_p = calc_envido(d["manos"][i.user.id])
  await i.response.send_message(f"💰 **{d['nombres'][i.user.id]}** canta ENVIDO! Tiene {envido_p}", view=EnvidoRespAmigo(self.pid))

class SalirAmigoV4(discord.ui.Button):
 def __init__(self,pid,owner):
  self.pid=pid; self.owner=owner
  super().__init__(label="IRSE AL MAZO 🚪",style=discord.ButtonStyle.secondary,row=2)
 async def callback(self,i):
  if i.user.id not in partidas.get(self.pid,{}).get("jugadores",[]): await i.response.send_message("❌ No sos parte de esta partida",ephemeral=True); return
  d=partidas.get(self.pid)
  if not d: return
  if d["tipo"]=="corta":
      await i.response.send_message(f"🚪 {d['nombres'][i.user.id]} se fue al mazo - Partida termina SIN monedas")
      partidas.pop(self.pid,None)
  else:
      otros=[uid for uid in d["jugadores"] if uid!=i.user.id]
      for uid in otros: add_coins(uid,100)
      await i.response.send_message(f"🚪 {d['nombres'][i.user.id]} ABANDONO! {', '.join([d['nombres'][u] for u in otros])} +100 Trucoins")
      if len(otros)==1: partidas.pop(self.pid,None)
      else: d["jugadores"]=otros; d["last_action"]=time.time()

class ViewAmigosV4(discord.ui.View):
 def __init__(self,pid, owner_id=None):
  super().__init__(timeout=600); self.pid=pid
  d=partidas.get(pid)
  if not d: return
  if owner_id and owner_id in d["manos"]:
      for carta in d["manos"][owner_id]:
          self.add_item(CartaAmigoV4(carta,owner_id,pid))
  else:
      first=d["jugadores"][0]
      if first in d["manos"]:
          for carta in d["manos"][first]:
              self.add_item(CartaAmigoV4(carta,first,pid))
  first=d["jugadores"][0]
  self.add_item(TrucoAmigoV4(pid,first))
  self.add_item(EnvidoAmigoV4(pid,first))
  self.add_item(SalirAmigoV4(pid,first))
  self.add_item(ExpOpen(first))

class ViewAmigosPublico(discord.ui.View):
 def __init__(self,pid):
  super().__init__(timeout=600); self.pid=pid
  d=partidas.get(pid)
  if not d: return
  first=d["jugadores"][0]
  self.add_item(TrucoAmigoV4(pid,first))
  self.add_item(EnvidoAmigoV4(pid,first))
  self.add_item(SalirAmigoV4(pid,first))
  self.add_item(ExpOpen(first))

class JugarMenuView(discord.ui.View):
 def __init__(self, owner_id):
  super().__init__(timeout=180)
  self.owner_id=owner_id
 @discord.ui.button(label="⚔️ 1V1", style=discord.ButtonStyle.primary, row=0)
 async def b_1v1(self,i,b): await self.crear_sala(i, "1v1", 2)
 @discord.ui.button(label="👥 TRIO", style=discord.ButtonStyle.primary, row=0)
 async def b_trio(self,i,b): await self.crear_sala(i, "trio", 6)
 @discord.ui.button(label="🛡️ ESCUADRON", style=discord.ButtonStyle.primary, row=0)
 async def b_esc(self,i,b): await self.crear_sala(i, "escuadron", 8)
 @discord.ui.button(label="🤖 BOT", style=discord.ButtonStyle.success, row=1)
 async def b_bot(self,i,b): await self.iniciar_bot(i, "bot")
 @discord.ui.button(label="🤖 BOT TRIO", style=discord.ButtonStyle.success, row=1)
 async def b_bot_trio(self,i,b): await self.iniciar_bot(i, "bot_trio")
 @discord.ui.button(label="🤖 BOT ESCUADRON", style=discord.ButtonStyle.success, row=1)
 async def b_bot_esc(self,i,b): await self.iniciar_bot(i, "bot_escuadron")
 async def crear_sala(self, i, modo, necesarios):
  if i.user.id!=self.owner_id: await i.response.send_message("No es tu menu",ephemeral=True); return
  pid=f"lobby_{i.channel.id}"
  salas_jugar[pid]={"modo":modo,"necesarios":necesarios,"jugadores":[i.user.id],"nombres":{i.user.id:i.user.display_name},"creador":i.user.id,"creador_nombre":i.user.display_name,"last":time.time()}
  emb=discord.Embed(title=f"⚔️ SALA {modo.upper()} CREADA ({1}/{necesarios})", description=f"🔥 **{i.user.display_name} TE HA RETADO A UN TRUCO!**\n\nModo: **{modo.upper()}**\nEsperando {necesarios-1} jugadores más...", color=0xe74c3c)
  file, emb = get_file_embed_titulo(emb, i.user.id)
  if file: await i.response.edit_message(embed=emb, attachments=[file], view=SalaEsperaView(pid))
  else: await i.response.edit_message(embed=emb, view=SalaEsperaView(pid))
  await i.followup.send(f"🔥 @everyone **{i.user.display_name} TE RETO A UN TRUCO! Modo {modo.upper()} - Tocá ESTOY LISTO!**")
 async def iniciar_bot(self, i, modo):
  if i.user.id!=self.owner_id: return
  ensure_user(i.user.id)
  m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m); mj=[m.pop() for _ in range(3)]; mb=[m.pop() for _ in range(3)]
  partidas[i.user.id]={"bot":mb.copy(),"mano_jugador":mj.copy(),"mano_jugador_orig":mj.copy(),"mano_bot_orig":mb.copy(),"mano_bot":mb.copy(),"pj":0,"pb":0,"truco_nivel":1,"envido_jugado":False,"truco_jugado":False,"last_action":time.time()}
  emb=discord.Embed(title=f"🃏 TRUCO vs {modo.upper()} 🤖", description=f"Modo {modo} - Bot piensa", color=0x1e8449)
  file, emb = get_file_embed_titulo(emb, i.user.id)
  view=V(i.user.id,mj)
  if file: await i.response.edit_message(embed=emb, attachments=[file], view=view)
  else: await i.response.edit_message(embed=emb, view=view)

class SalaEsperaView(discord.ui.View):
 def __init__(self, pid):
  super().__init__(timeout=300); self.pid=pid
 @discord.ui.button(label="✅ ESTOY LISTO", style=discord.ButtonStyle.success)
 async def listo(self,i,b):
  sala=salas_jugar.get(self.pid)
  if not sala: await i.response.send_message("Sala ya no existe",ephemeral=True); return
  if i.user.id not in sala["jugadores"]:
   sala["jugadores"].append(i.user.id); sala["nombres"][i.user.id]=i.user.display_name
  sala["last"]=time.time()
  if len(sala["jugadores"])>=sala["necesarios"]:
   jugadores=sala["jugadores"]; nombres=sala["nombres"]
   manos={}; m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m)
   for uid in jugadores: manos[uid]=[m.pop() for _ in range(3)]
   partidas[self.pid]={"jugadores":jugadores,"manos":manos,"jugadas_ronda":{},"rondas_ganadas":{uid:0 for uid in jugadores},"puntos":{uid:0 for uid in jugadores},"puntos_para_ganar":1,"tipo":"corta","nombres":nombres,"truco_nivel":1,"envido_jugado":False,"last_action":time.time()}
   salas_jugar.pop(self.pid,None)
   emb=discord.Embed(title=f"🃏 PARTIDA {sala['modo'].upper()} INICIADA", description=f"Jugadores: {', '.join(nombres.values())}\nCartas privadas enviadas 👇", color=0x2ecc71)
   file, emb = get_file_embed_titulo(emb, jugadores[0])
   if file: await i.response.edit_message(embed=emb, attachments=[file], view=ViewAmigosPublico(self.pid))
   else: await i.response.edit_message(embed=emb, view=ViewAmigosPublico(self.pid))
   for uid in jugadores:
       await i.followup.send(f"<@{uid}> **TUS CARTAS PRIVADAS:**", view=ViewAmigosV4(self.pid, owner_id=uid))
  else:
   emb=discord.Embed(title=f"⚔️ SALA {sala['modo'].upper()} ({len(sala['jugadores'])}/{sala['necesarios']})", description=f"Creador: {sala['creador_nombre']}\nJugadores: {', '.join(sala['nombres'].values())}\n\nFaltan {sala['necesarios']-len(sala['jugadores'])}", color=0xe74c3c)
   await i.response.edit_message(embed=emb, view=self)
   await i.followup.send(f"✅ {i.user.display_name} se unió! ({len(sala['jugadores'])}/{sala['necesarios']})")
 @discord.ui.button(label="📩 INVITAR A TODOS", style=discord.ButtonStyle.primary)
 async def invitar(self,i,b):
  sala=salas_jugar.get(self.pid)
  if not sala: return
  await i.response.send_message(f"🔥🔥 @everyone {sala['creador_nombre']} TE HA RETADO A UN TRUCO! Modo {sala['modo'].upper()} - Tocá ESTOY LISTO!")
 @discord.ui.button(label="❌ CANCELAR SALA", style=discord.ButtonStyle.danger)
 async def cancelar(self,i,b):
  sala=salas_jugar.get(self.pid)
  if not sala: return
  if i.user.id!=sala["creador"]: await i.response.send_message("Solo el creador puede cancelar ❌",ephemeral=True); return
  salas_jugar.pop(self.pid,None)
  await i.response.edit_message(embed=discord.Embed(title="❌ SALA CANCELADA", description=f"Cancelada por {sala['creador_nombre']}", color=0x95a5a6), view=None)

async def timeout_checker():
 while True:
   await asyncio.sleep(30)
   ahora=time.time()
   to_del=[]
   for pid,d in list(partidas.items()):
     if ahora - d.get("last_action",ahora) > TIMEOUT_SEGUNDOS:
         to_del.append(pid)
   for pid in to_del:
     partidas.pop(pid,None)
     print(f"TIMEOUT V6.2: Partida {pid} terminada 2min")
   to_del2=[]
   for pid,d in list(salas_jugar.items()):
     if ahora - d.get("last",ahora) > 300:
         to_del2.append(pid)
   for pid in to_del2: salas_jugar.pop(pid,None)

@tree.command(name="jugar",description="Jugar - Menu V6.2 Fix privado")
async def jugar(i:discord.Interaction):
 ensure_user(i.user.id)
 if not check_spam(i.user.id):
   await i.response.send_message("⏳ No spamees! Espera 3 seg",ephemeral=True); return
 emb=discord.Embed(title="🎮 ELEGÍ MODO DE JUEGO - TRUCO V6.2", description="1V1 (2) | TRIO (6) | ESCUADRON (8)\nBOT arranca de una\nCartas privadas FIX ✅", color=0x9b59b6)
 await i.response.send_message(embed=emb, view=JugarMenuView(i.user.id))

@tree.command(name="truco",description="Partida CORTA")
async def truco_cmd(i:discord.Interaction, rival1: discord.Member, rival2: discord.Member = None, rival3: discord.Member = None):
 ensure_user(i.user.id)
 if not check_spam(i.user.id): await i.response.send_message("⏳ Anti-spam",ephemeral=True); return
 jugadores=[i.user.id]
 for r in [rival1,rival2,rival3]:
   if r and r.id!=i.user.id and not r.bot and r.id not in jugadores: jugadores.append(r.id)
 if len(jugadores)<2: await i.response.send_message("Necesitas al menos 1 rival",ephemeral=True); return
 pid=f"corta_{random.randint(10000,999999)}"
 manos={}; m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m); nombres={}
 for uid in jugadores: manos[uid]=[m.pop() for _ in range(3)]
 nombres[i.user.id]=i.user.display_name
 if rival1: nombres[rival1.id]=rival1.display_name
 if rival2: nombres[rival2.id]=rival2.display_name
 if rival3: nombres[rival3.id]=rival3.display_name
 partidas[pid]={"jugadores":jugadores,"manos":manos,"jugadas_ronda":{},"rondas_ganadas":{uid:0 for uid in jugadores},"puntos":{uid:0 for uid in jugadores},"puntos_para_ganar":1,"tipo":"corta","nombres":nombres,"truco_nivel":1,"envido_jugado":False,"last_action":time.time()}
 emb=discord.Embed(title=f"🃏 TRUCO CORTO {' vs '.join(nombres.values())}", description=f"Cartas privadas enviadas abajo", color=0xe74c3c)
 file, emb = get_file_embed_titulo(emb, i.user.id)
 if file: await i.response.send_message(embed=emb, file=file, view=ViewAmigosPublico(pid))
 else: await i.response.send_message(embed=emb, view=ViewAmigosPublico(pid))
 for uid in jugadores:
     await i.followup.send(f"<@{uid}> tus cartas:", view=ViewAmigosV4(pid, owner_id=uid))

@tree.command(name="batalla",description="Batalla LARGA 15 o 30")
@app_commands.choices(puntos=[Choice(name="15 puntos", value=15), Choice(name="30 puntos", value=30)])
async def batalla(i:discord.Interaction, rival1: discord.Member, puntos: int, rival2: discord.Member = None, rival3: discord.Member = None):
 ensure_user(i.user.id)
 if not check_spam(i.user.id): await i.response.send_message("⏳ Anti-spam",ephemeral=True); return
 jugadores=[i.user.id]
 for r in [rival1,rival2,rival3]:
   if r and r.id!=i.user.id and not r.bot and r.id not in jugadores: jugadores.append(r.id)
 if len(jugadores)<2: await i.response.send_message("Necesitas al menos 1 rival",ephemeral=True); return
 pid=f"larga_{random.randint(10000,999999)}"
 manos={}; m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m); nombres={}
 for uid in jugadores: manos[uid]=[m.pop() for _ in range(3)]
 nombres[i.user.id]=i.user.display_name
 if rival1: nombres[rival1.id]=rival1.display_name
 if rival2: nombres[rival2.id]=rival2.display_name
 if rival3: nombres[rival3.id]=rival3.display_name
 partidas[pid]={"jugadores":jugadores,"manos":manos,"jugadas_ronda":{},"rondas_ganadas":{uid:0 for uid in jugadores},"puntos":{uid:0 for uid in jugadores},"puntos_para_ganar":puntos,"tipo":"larga","nombres":nombres,"truco_nivel":1,"envido_jugado":False,"last_action":time.time()}
 emb=discord.Embed(title=f"⚔️ BATALLA LARGA {puntos} PTS - {' vs '.join(nombres.values())}", description=f"Cartas privadas abajo", color=0xf1c40f)
 file, emb = get_file_embed_titulo(emb, i.user.id)
 if file: await i.response.send_message(embed=emb, file=file, view=ViewAmigosPublico(pid))
 else: await i.response.send_message(embed=emb, view=ViewAmigosPublico(pid))
 for uid in jugadores:
     await i.followup.send(f"<@{uid}> tus cartas:", view=ViewAmigosV4(pid, owner_id=uid))

@tree.command(name="tienda",description="Tienda")
@app_commands.choices(categoria=[Choice(name="TABLEROS", value="tableros"),Choice(name="PODERES", value="poderes"),Choice(name="EXPRESIONES", value="expresiones"),])
async def tienda(i:discord.Interaction, categoria: str):
 await i.response.defer(ephemeral=True)
 ensure_user(i.user.id)
 data=load_u(); coins=data.get(str(i.user.id),{}).get("coins",0)
 embed=discord.Embed(title=f"🛒 TIENDA {categoria.upper()} - {coins} coins",color=0xf1c40f)
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
  desc+=f"**{idx}. {nombre}** - {total} wins\n"
 await i.followup.send(embed=discord.Embed(title="🏆 RANKING",description=desc,color=0xf1c40f))

@tree.command(name="equipar",description="Equipar")
async def equipar(i:discord.Interaction):
 await i.response.defer(ephemeral=True)
 ensure_user(i.user.id)
 emb=discord.Embed(title="🎒 EQUIPAR",description=f"TABLEROS",color=0x2ecc71)
 await i.followup.send(embed=emb,view=EquiparView(i.user.id),ephemeral=True)

@tree.command(name="perfil",description="Perfil")
async def perfil(i:discord.Interaction):
 ensure_user(i.user.id); data=load_u(); s=str(i.user.id)
 await i.response.send_message(f"💰 {data[s]['coins']} 🏆 Bot {data[s]['wins_bot']} Amigo {data[s]['wins_amigo']}")

@tree.command(name="codigos",description="Canjear codigo")
async def codigos(i:discord.Interaction, codigo: str):
 await i.response.defer(ephemeral=True)
 ensure_user(i.user.id); data=load_u(); s=str(i.user.id)
 code_upper=codigo.strip().upper()
 found=None
 for k in CODIGOS:
  if k.upper()==code_upper: found=k; break
 if not found: await i.followup.send("❌ Codigo invalido", ephemeral=True); return
 if found in data[s]["codigos"]: await i.followup.send("❌ Ya canjeado", ephemeral=True); return
 if found in ["TRUCO!","1_ESPADA"]:
  data[s]["poderes"]["MAGO"]=data[s]["poderes"].get("MAGO",0)+1; data[s]["codigos"].append(found); save_u(data)
  await i.followup.send(f"✨ +1 MAGO!", ephemeral=True); return
 data[s]["coins"]+=CODIGOS[found]; data[s]["codigos"].append(found); save_u(data)
 await i.followup.send(f"💰 +{CODIGOS[found]} coins!", ephemeral=True)

@tree.command(name="ayuda",description="Ayuda V6.2")
async def ayuda(i:discord.Interaction):
 await i.response.send_message(embed=discord.Embed(title="AYUDA V6.2 FIX PRIVADO",description="/jugar -> 1V1 TRIO ESCUADRON BOT + cartas privadas + anti tocar otras partidas + timeout 2min",color=0x9b59b6))

@bot.event
async def on_ready():
 await tree.sync()
 print("V6.2 FIX CARTAS PRIVADAS + ANTI OTRAS PARTIDAS")
 bot.loop.create_task(timeout_checker())

bot.run(os.getenv("DISCORD_TOKEN"))

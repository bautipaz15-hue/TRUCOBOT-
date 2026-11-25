import discord, random, os, json, asyncio, time, requests
from discord import app_commands
from discord.app_commands import Choice
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def h(): return "ok BOT TRUCO V6.5 UNIFICADO + SAVE"

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
Thread(target=run_flask, daemon=True).start()
def keep_alive():
    while True:
        time.sleep(600)
        try: requests.get(os.environ.get("RENDER_EXTERNAL_URL", "https://trucobot-athd.onrender.com"), timeout=10)
        except: pass
Thread(target=keep_alive, daemon=True).start()

intents=discord.Intents.default(); intents.message_content=True
bot=discord.Client(intents=intents); tree=app_commands.CommandTree(bot)
partidas={}; salas_jugar={}; ultimo_comando={}; TIMEOUT_SEGUNDOS=120
PALOS=["espada","basto","oro","copa"]; NUMS=[1,2,3,4,5,6,7,10,11,12]
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
 if max_e==0: max_e=max([envido_valor(c[0]) for c in mano]) if mano else 0
 return max_e

PRECIOS={"river":1000,"boca":1000,"san lorenzo":1000,"racing":1000,"springtrap":1250,"creeper":1500,"minecraft":1500,"diamante":1800,"oro":1200}
CODIGOS={"TRUCO2026":1000,"navidad_se_acerca":350,"7_ORO":350,"TRUCO!":0,"1_ESPADA":0,"SPRITE":0,"VICTORY ROYALE":0,"GAMER":0}
PODERES_PRECIO={"MAGO":{"x1":400,"x10":3500},"OJO":{"x1":350,"x10":3000},"ESCUDO":{"x1":500,"x10":4500},"LADRON":{"x1":450,"x10":4000}}

# --- FIX PROGRESO GUARDADO ---
os.makedirs("data", exist_ok=True)
FILE="data/usuarios.json"
if os.path.exists("usuarios.json") and not os.path.exists(FILE):
    try: 
        with open("usuarios.json","r") as a, open(FILE,"w") as b: b.write(a.read())
    except: pass

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
  save_u(data)
 return data
def add_coins(uid,cant):
 data=load_u(); s=str(uid); ensure_user(uid); data=load_u()
 data[s]["coins"]=data[s].get("coins",0)+cant; save_u(data)
def add_win(uid,tipo):
 data=load_u(); s=str(uid); ensure_user(uid); data=load_u()
 if tipo=="bot": data[s]["wins_bot"]=data[s].get("wins_bot",0)+1
 else: data[s]["wins_amigo"]=data[s].get("wins_amigo",0)+1
 save_u(data)
def buscar_tablero(nombre):
 if not os.path.exists("tableros"): return None
 nombre=nombre.lower()
 if "san" in nombre and "lorenzo" in nombre: nombre="san lorenzo"
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
 if ahora-ultimo_comando.get(uid,0) < 2: return False
 ultimo_comando[uid]=ahora; return True

def get_file_embed_titulo(emb, uid):
    tpath = tab_user(uid)
    if tpath and os.path.exists(tpath):
        file = discord.File(tpath, filename="tablero.jpg")
        emb.set_image(url="attachment://tablero.jpg")
        return file, emb
    return None, emb

class JugarDeNuevoView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔄 JUGAR DE NUEVO", style=discord.ButtonStyle.success, emoji="🃏")
    async def replay(self, i, b):
        ensure_user(i.user.id)
        emb = discord.Embed(title="🎮 ELEGÍ MODO", description="1V1 (2) | TRIO (6) | ESCUADRON (8)", color=0x2ecc71)
        await i.response.send_message(embed=emb, view=JugarMenuView(i.user.id))

class ManoPrivadaView(discord.ui.View):
    def __init__(self, pid, owner_id):
        super().__init__(timeout=120)
        d = partidas.get(pid)
        if not d or owner_id not in d["manos"]: return
        jugadas = list(d.get("jugadas_ronda", {}).values())
        jugadas += d.get(f"cartas_jugadas_{owner_id}", [])
        for carta in d["manos"][owner_id]:
            if carta not in jugadas:
                self.add_item(CartaAmigoV4(carta, owner_id, pid))

class VerMazoBtn(discord.ui.Button):
    def __init__(self, pid, owner_id, label=None):
        self.pid=pid; self.owner_id=owner_id
        super().__init__(label=label or "🃏 VER MAZO", style=discord.ButtonStyle.primary, emoji="👁️", row=1)
    async def callback(self, i):
        if i.user.id != self.owner_id:
            await i.response.send_message(f"❌ Este botón es de {partidas.get(self.pid,{}).get('nombres',{}).get(self.owner_id,'otro')}", ephemeral=True); return
        d = partidas.get(self.pid)
        if not d or i.user.id not in d["jugadores"]: await i.response.send_message("❌ Partida terminada", ephemeral=True); return
        mano = d["manos"].get(i.user.id, [])
        jugadas = d.get(f"cartas_jugadas_{i.user.id}", [])
        mano_restante = [c for c in mano if c not in jugadas and c not in d.get("jugadas_ronda",{}).values()]
        if not mano_restante: await i.response.send_message("⏳ Ya no tenés cartas", ephemeral=True); return
        texto = ", ".join([f"{c[0]} de {c[1]}" for c in mano_restante])
        emb = discord.Embed(title="🃏 TU MAZO PRIVADO (solo vos)", description=f"**Cartas:** {texto}\n**Envido:** {calc_envido(mano_restante)} pts", color=0x3498db)
        await i.response.send_message(embed=emb, view=ManoPrivadaView(self.pid, self.owner_id), ephemeral=True)

# TIENDA SIMPLE
class TableroSelect(discord.ui.Select):
 def __init__(self,owner): self.owner=owner; owned=load_u().get(str(owner),{}).get("owned",["default"]); super().__init__(placeholder="📋 TABLEROS", min_values=1, max_values=1, options=[discord.SelectOption(label=o.upper(), value=o) for o in owned[:25]])
 async def callback(self,i):
  if i.user.id!=self.owner: return
  data=load_u(); data[str(i.user.id)]["equipado"]=self.values[0]; save_u(data)
  await i.response.send_message(f"✅ Equipaste {self.values[0].upper()}", ephemeral=True)
class EquiparView(discord.ui.View):
 def __init__(self,owner): super().__init__(timeout=180); self.add_item(TableroSelect(owner))
class BotonTienda(discord.ui.Button):
 def __init__(self,nombre,precio,owner): self.nombre=nombre; self.precio=precio; self.owner=owner; super().__init__(label=f"{nombre.upper()} - {precio}",style=discord.ButtonStyle.primary)
 async def callback(self,i):
  if i.user.id!=self.owner: return
  data=load_u(); s=str(i.user.id)
  if data[s]["coins"]<self.precio: await i.response.send_message("Te faltan coins",ephemeral=True); return
  data[s]["coins"]-=self.precio; data[s]["owned"].append(self.nombre); save_u(data)
  await i.response.send_message(f"✅ Compraste {self.nombre.upper()}",ephemeral=True)
class TiendaView(discord.ui.View):
 def __init__(self,owner,categoria="tableros"):
  super().__init__(timeout=300)
  if categoria=="tableros":
   for n,p in PRECIOS.items(): self.add_item(BotonTienda(n,p,owner))

class TrucoRespAmigo(discord.ui.View):
 def __init__(self,pid, nivel, cantor_id): super().__init__(timeout=30); self.pid=pid; self.nivel=nivel; self.cantor_id=cantor_id
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b):
  d=partidas.get(self.pid)
  if not d: return
  if i.user.id == self.cantor_id: await i.response.send_message("❌ No podés decir QUIERO a tu propio TRUCO!",ephemeral=True); return
  if d.get("truco_pendiente") is None: await i.response.send_message("❌ Ya no hay truco pendiente",ephemeral=True); return
  d["last_action"]=time.time()
  if self.nivel==1: d["truco_nivel"]=2
  elif self.nivel==2: d["truco_nivel"]=3
  elif self.nivel==3: d["truco_nivel"]=4
  d["truco_pendiente"]=None
  await i.response.send_message(f"🔥 {d['nombres'][i.user.id]} dice QUIERO! Vale {d['truco_nivel']}"); self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b):
  d=partidas.get(self.pid)
  if not d: return
  if i.user.id == self.cantor_id: await i.response.send_message("❌ No podés rechazar tu propio truco",ephemeral=True); return
  ganador_id = self.cantor_id; d["truco_pendiente"]=None; add_coins(ganador_id,100)
  await i.response.send_message(f"❌ NO QUIERO! {d['nombres'][ganador_id]} gana"); d["puntos"][ganador_id]+=d.get("truco_nivel",1)
  if d.get("tipo")=="corta": partidas.pop(self.pid,None)
  self.stop()

class EnvidoRespAmigo(discord.ui.View):
 def __init__(self,pid, cantor_id): super().__init__(timeout=30); self.pid=pid; self.cantor_id=cantor_id
 @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success)
 async def quiero(self,i,b):
  d=partidas.get(self.pid)
  if not d: return
  if i.user.id == self.cantor_id: await i.response.send_message("❌ No podés decir QUIERO a tu propio ENVIDO!",ephemeral=True); return
  if d.get("envido_pendiente") is None: return
  d["last_action"]=time.time(); d["envido_pendiente"]=None
  envidos={uid: calc_envido(d["manos"][uid]) for uid in d["jugadores"]}
  ganador = max(envidos, key=lambda k: envidos[k]); d["puntos"][ganador]+=2
  await i.response.send_message(f"💰 QUIERO! Envidos: {envidos} -> Gana {d['nombres'][ganador]} +2"); self.stop()
 @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger)
 async def no(self,i,b):
  d=partidas.get(self.pid)
  if not d: return
  if i.user.id == self.cantor_id: await i.response.send_message("❌ No podés rechazar tu propio envido",ephemeral=True); return
  d["envido_pendiente"]=None; cantor = d.get("envido_cantor")
  if cantor: d["puntos"][cantor]+=1
  await i.response.send_message(f"💰 NO QUIERO! +1 para {d['nombres'][cantor]}"); self.stop()

class C(discord.ui.Button):
 def __init__(self,carta,owner): self.carta=carta; self.owner=owner; super().__init__(label=f"{carta[0]} de {carta[1]} 🃏",style=discord.ButtonStyle.primary,row=0)
 async def callback(self,i):
  if i.user.id!=self.owner: await i.response.send_message("❌ No es tu carta",ephemeral=True); return
  d=partidas.get(self.owner)
  if not d: return
  if d.get("truco_pendiente") or d.get("envido_pendiente"): await i.response.send_message("⏳ Esperá que respondan!",ephemeral=True); return
  d["last_action"]=time.time(); self.disabled=True; await i.response.edit_message(view=self.view)
  await i.followup.send(f"🃏 Tiraste {self.carta[0]} de {self.carta[1]}")
  m = await i.followup.send("🤖 PENSANDO..."); await asyncio.sleep(1.2)
  try: await m.delete()
  except: pass
  if len(d["bot"])==0: return
  cb=d["bot"].pop(0)
  if self.carta in d["mano_jugador"]: d["mano_jugador"].remove(self.carta)
  vy=v(self.carta[0],self.carta[1]); vb=v(cb[0],cb[1])
  if vy>vb: d["pj"]+=1; txt=f"✨ GANASTE! Bot: {cb[0]} de {cb[1]} 📊 {d['pj']}-{d['pb']}"
  elif vy<vb: d["pb"]+=1; txt=f"💔 PERDISTE! Bot: {cb[0]} de {cb[1]} 📊 {d['pj']}-{d['pb']}"
  else: txt=f"🤝 Empate 📊 {d['pj']}-{d['pb']}"
  if d["pj"]>=2 or d["pb"]>=2 or len(d["mano_jugador"])==0:
   if d["pj"]>d["pb"]: add_coins(self.owner,250); add_win(self.owner,"bot"); txt=f"🏆 GANASTE +250! Final: {d['pj']}-{d['pb']}"
   else: txt=f"😭 PERDISTE Final: {d['pj']}-{d['pb']}"
   partidas.pop(self.owner,None); await i.followup.send(txt, view=JugarDeNuevoView()); return
  await i.followup.send(txt)
class T(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="TRUCO 🔥",style=discord.ButtonStyle.danger,row=1)
 async def callback(self,i):
  if i.user.id!=self.o: return
  d=partidas.get(self.o)
  if not d or d.get("truco_pendiente"): return
  d["truco_nivel"]=min(4,d.get("truco_nivel",1)+1); await i.followup.send(f"🤖 Bot: QUIERO! Vale {d['truco_nivel']}")
class E(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="ENVIDO 💰",style=discord.ButtonStyle.success,row=1)
 async def callback(self,i):
  if i.user.id!=self.o: return
  d=partidas.get(self.o); d["pj"]+=1; await i.followup.send(f"Bot: NO QUIERO +1")
class S(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="IRSE AL MAZO 🚪",style=discord.ButtonStyle.secondary,row=1)
 async def callback(self,i): partidas.pop(self.o,None); await i.response.edit_message(content="🚪 Te fuiste al mazo",view=None)
class ExpOpen(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="Expresiones 💬",style=discord.ButtonStyle.secondary,row=1)
 async def callback(self,i): await i.response.send_message("💬", ephemeral=True)
class V(discord.ui.View):
 def __init__(self,o,m):
  super().__init__(timeout=600)
  [self.add_item(C(c,o)) for c in m]
  self.add_item(T(o)); self.add_item(E(o)); self.add_item(ExpOpen(o)); self.add_item(S(o))

class CartaAmigoV4(discord.ui.Button):
 def __init__(self,carta,owner,pid):
  self.carta=carta; self.owner=owner; self.pid=pid
  super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary)
 async def callback(self,i):
  if i.user.id!=self.owner: await i.response.send_message("❌ No es tu carta!", ephemeral=True); return
  d=partidas.get(self.pid)
  if not d or i.user.id not in d["jugadores"]: await i.response.send_message("❌ Partida terminada", ephemeral=True); return
  if d.get("truco_pendiente"): await i.response.send_message(f"⏳ Hay TRUCO pendiente!", ephemeral=True); return
  if d.get("envido_pendiente"): await i.response.send_message(f"⏳ Hay ENVIDO pendiente!", ephemeral=True); return
  if self.owner in d["jugadas_ronda"]: await i.response.send_message("Ya jugaste esta ronda",ephemeral=True); return
  d["last_action"]=time.time()
  if self.carta in d["manos"][self.owner]: d["manos"][self.owner].remove(self.carta)
  d.setdefault(f"cartas_jugadas_{self.owner}", []).append(self.carta)
  d["jugadas_ronda"][self.owner]=self.carta
  await i.response.send_message(f"🃏 Tiraste {self.carta[0]} de {self.carta[1]} (solo vos ves esto)", ephemeral=True)
  await i.channel.send(f"🃏 {d['nombres'][self.owner]} tiró carta boca abajo 🎴")
  if len(d["jugadas_ronda"])==len(d["jugadores"]):
      mejor=None; ganador=None; texto_ronda=""
      for uid,carta in d["jugadas_ronda"].items():
          val=v(carta[0],carta[1]); texto_ronda+=f"**{d['nombres'][uid]}**: {carta[0]} de {carta[1]} | "
          if mejor is None or val>mejor: mejor=val; ganador=uid
      d["rondas_ganadas"][ganador]+=1
      await i.channel.send(f"🏁 Cartas: {texto_ronda}\nRonda para **{d['nombres'][ganador]}**")
      d["jugadas_ronda"]={}
      if max(d["rondas_ganadas"].values())>=2 or sum(d["rondas_ganadas"].values())>=3:
          ganador_mano = max(d["rondas_ganadas"], key=lambda k: d["rondas_ganadas"][k])
          puntos_mano = d.get("truco_nivel",1)
          d["puntos"][ganador_mano]+=puntos_mano
          await i.channel.send(f"🏆 Mano para **{d['nombres'][ganador_mano]}** +{puntos_mano} pts | { {d['nombres'][k]:v for k,v in d['puntos'].items()} }")
          if d["tipo"]=="corta":
              add_coins(ganador_mano,250); add_win(ganador_mano,"amigo")
              await i.channel.send(f"🎉 **GANA {d['nombres'][ganador_mano]} +250**", view=JugarDeNuevoView())
              partidas.pop(self.pid,None); return
          else:
              if d["puntos"][ganador_mano]>=d["puntos_para_ganar"]:
                  add_coins(ganador_mano,500); await i.channel.send(f"👑 **¡{d['nombres'][ganador_mano]} GANA +500!**", view=JugarDeNuevoView())
                  partidas.pop(self.pid,None); return
              else: await nueva_mano_v4(self.pid,i.channel)

async def nueva_mano_v4(pid, channel):
 d=partidas.get(pid)
 if not d: return
 m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m)
 for uid in d["jugadores"]: d["manos"][uid]=[m.pop() for _ in range(3)]; d.pop(f"cartas_jugadas_{uid}", None)
 d["jugadas_ronda"]={}; d["rondas_ganadas"]={uid:0 for uid in d["jugadores"]}; d["truco_nivel"]=1; d["envido_jugado"]=False; d["truco_pendiente"]=None; d["envido_pendiente"]=None; d["last_action"]=time.time()
 emb=discord.Embed(title=f"🃏 NUEVA MANO - {d['tipo'].upper()} | ID {pid[:6]}", description=f"Jugadores: {', '.join([d['nombres'][uid] for uid in d['jugadores']])}\nMarcador: { {d['nombres'][k]:v for k,v in d['puntos'].items()} }", color=0xe74c3c)
 file, emb = get_file_embed_titulo(emb, d["jugadores"][0])
 msg_id = d.get("mensaje_id")
 if msg_id:
     try:
         msg = await channel.fetch_message(msg_id)
         if file: await msg.edit(embed=emb, attachments=[file], view=PartidaUnificadaView(pid))
         else: await msg.edit(embed=emb, view=PartidaUnificadaView(pid))
         return
     except: pass
 if file: msg = await channel.send(embed=emb, file=file, view=PartidaUnificadaView(pid))
 else: msg = await channel.send(embed=emb, view=PartidaUnificadaView(pid))
 d["mensaje_id"]=msg.id

class TrucoAmigoV4(discord.ui.Button):
 def __init__(self,pid,owner): self.pid=pid; self.owner=owner; super().__init__(label="TRUCO 🔥",style=discord.ButtonStyle.danger,row=0)
 async def callback(self,i):
  d=partidas.get(self.pid)
  if not d or i.user.id not in d["jugadores"]: await i.response.send_message("❌ No sos parte",ephemeral=True); return
  if d.get("truco_pendiente") or d.get("envido_pendiente"): await i.response.send_message("⏳ Ya hay canto pendiente!",ephemeral=True); return
  nivel=d.get("truco_nivel",1)
  if nivel>=4: await i.response.send_message("Ya es VALE 4",ephemeral=True); return
  d["last_action"]=time.time(); d["truco_pendiente"]={"cantor":i.user.id, "nivel":nivel}
  await i.response.send_message(f"🔥 **{d['nombres'][i.user.id]}** canta {'TRUCO' if nivel==1 else 'RETRUCO' if nivel==2 else 'VALE 4'}! Vale {nivel+1}", view=TrucoRespAmigo(self.pid,nivel,i.user.id))

class EnvidoAmigoV4(discord.ui.Button):
 def __init__(self,pid,owner): self.pid=pid; self.owner=owner; super().__init__(label="ENVIDO 💰",style=discord.ButtonStyle.success,row=0)
 async def callback(self,i):
  d=partidas.get(self.pid)
  if not d or i.user.id not in d["jugadores"]: await i.response.send_message("❌ No sos parte",ephemeral=True); return
  if d.get("envido_pendiente") or d.get("truco_pendiente"): await i.response.send_message("Ya hay canto pendiente",ephemeral=True); return
  if d.get("envido_jugado"): await i.response.send_message("Envido solo al principio",ephemeral=True); return
  if len(d["jugadas_ronda"])!=0: await i.response.send_message("Envido solo al principio",ephemeral=True); return
  d["last_action"]=time.time(); d["envido_jugado"]=True; d["envido_cantor"]=i.user.id; d["envido_pendiente"]={"cantor":i.user.id}
  envido_p = calc_envido(d["manos"][i.user.id])
  await i.response.send_message(f"💰 **{d['nombres'][i.user.id]}** canta ENVIDO! Tiene {envido_p}", view=EnvidoRespAmigo(self.pid,i.user.id))

class SalirAmigoV4(discord.ui.Button):
 def __init__(self,pid,owner): self.pid=pid; self.owner=owner; super().__init__(label="IRSE AL MAZO 🚪",style=discord.ButtonStyle.secondary,row=2)
 async def callback(self,i):
  d=partidas.get(self.pid)
  if not d or i.user.id not in d["jugadores"]: await i.response.send_message("❌ No sos parte",ephemeral=True); return
  if d["tipo"]=="corta": await i.response.send_message(f"🚪 {d['nombres'][i.user.id]} se fue"); partidas.pop(self.pid,None)
  else: otros=[uid for uid in d["jugadores"] if uid!=i.user.id]; [add_coins(uid,100) for uid in otros]; await i.response.send_message(f"🚪 ABANDONO +100 para resto"); partidas.pop(self.pid,None) if len(otros)==1 else d.update({"jugadores":otros})

# V6.5 UNIFICADO: TODO EN UN MENSAJE
class PartidaUnificadaView(discord.ui.View):
    def __init__(self, pid):
        super().__init__(timeout=600)
        self.pid = pid
        d = partidas.get(pid)
        if not d: return
        for uid in d["jugadores"]:
            nombre = d["nombres"].get(uid, "Jugador")[:12]
            self.add_item(VerMazoBtn(pid, uid, label=f"🃏 MAZO {nombre}"))
        first = d["jugadores"][0]
        self.add_item(TrucoAmigoV4(pid, first))
        self.add_item(EnvidoAmigoV4(pid, first))
        self.add_item(SalirAmigoV4(pid, first))

class JugarMenuView(discord.ui.View):
 def __init__(self, owner_id): super().__init__(timeout=180); self.owner_id=owner_id
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
  emb=discord.Embed(title=f"⚔️ SALA {modo.upper()} CREADA ({1}/{necesarios})", description=f"🔥 **{i.user.display_name} TE HA RETADO A UN TRUCO!**", color=0xe74c3c)
  file, emb = get_file_embed_titulo(emb, i.user.id)
  if file: await i.response.edit_message(embed=emb, attachments=[file], view=SalaEsperaView(pid))
  else: await i.response.edit_message(embed=emb, view=SalaEsperaView(pid))
  await i.followup.send(f"🔥 @everyone **{i.user.display_name} TE RETO A UN TRUCO! Modo {modo.upper()}**")
 async def iniciar_bot(self, i, modo):
  if i.user.id!=self.owner_id: return
  ensure_user(i.user.id)
  m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m); mj=[m.pop() for _ in range(3)]; mb=[m.pop() for _ in range(3)]
  partidas[i.user.id]={"bot":mb.copy(),"mano_jugador":mj.copy(),"mano_jugador_orig":mj.copy(),"mano_bot_orig":mb.copy(),"mano_bot":mb.copy(),"pj":0,"pb":0,"truco_nivel":1,"envido_jugado":False,"truco_jugado":False,"last_action":time.time()}
  emb=discord.Embed(title=f"🃏 TRUCO vs {modo.upper()} 🤖", description=f"Modo {modo}", color=0x1e8449)
  file, emb = get_file_embed_titulo(emb, i.user.id)
  view=V(i.user.id,mj)
  if file: await i.response.edit_message(embed=emb, attachments=[file], view=view)
  else: await i.response.edit_message(embed=emb, view=view)

class SalaEsperaView(discord.ui.View):
 def __init__(self, pid): super().__init__(timeout=300); self.pid=pid
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
   partidas[self.pid]={"jugadores":jugadores,"manos":manos,"jugadas_ronda":{},"rondas_ganadas":{uid:0 for uid in jugadores},"puntos":{uid:0 for uid in jugadores},"puntos_para_ganar":1,"tipo":"corta","nombres":nombres,"truco_nivel":1,"envido_jugado":False,"truco_pendiente":None,"envido_pendiente":None,"last_action":time.time(), "mensaje_id": None}
   salas_jugar.pop(self.pid,None)
   emb=discord.Embed(title=f"🃏 PARTIDA {sala['modo'].upper()} INICIADA - ID {self.pid[:6]}", description=f"**Jugadores:** {', '.join(nombres.values())}\nTodo en ESTE mensaje - Tocá tu MAZO", color=0x2ecc71)
   file, emb = get_file_embed_titulo(emb, jugadores[0])
   view = PartidaUnificadaView(self.pid)
   if file: await i.response.edit_message(embed=emb, attachments=[file], view=view)
   else: await i.response.edit_message(embed=emb, view=view)
   try:
       msg = await i.original_response()
       partidas[self.pid]["mensaje_id"] = msg.id
   except: pass
   await i.followup.send(f"✅ Partida `{self.pid[:6]}` iniciada!", ephemeral=True)
  else:
   emb=discord.Embed(title=f"⚔️ SALA {sala['modo'].upper()} ({len(sala['jugadores'])}/{sala['necesarios']})", description=f"Jugadores: {', '.join(sala['nombres'].values())}", color=0xe74c3c)
   await i.response.edit_message(embed=emb, view=self)
   await i.followup.send(f"✅ {i.user.display_name} se unió! ({len(sala['jugadores'])}/{sala['necesarios']})", ephemeral=True)
 @discord.ui.button(label="📩 INVITAR A TODOS", style=discord.ButtonStyle.primary)
 async def invitar(self,i,b): await i.response.send_message(f"🔥 @everyone {salas_jugar.get(self.pid,{}).get('creador_nombre','Alguien')} TE RETO!", ephemeral=False)
 @discord.ui.button(label="❌ CANCELAR SALA", style=discord.ButtonStyle.danger)
 async def cancelar(self,i,b):
  sala=salas_jugar.get(self.pid)
  if not sala: return
  if i.user.id!=sala["creador"]: await i.response.send_message("Solo el creador puede cancelar",ephemeral=True); return
  salas_jugar.pop(self.pid,None)
  await i.response.edit_message(embed=discord.Embed(title="❌ SALA CANCELADA", color=0x95a5a6), view=None)

async def timeout_checker():
 while True:
   await asyncio.sleep(30)
   ahora=time.time()
   for pid in list(partidas.keys()):
     if ahora - partidas[pid].get("last_action",ahora) > TIMEOUT_SEGUNDOS: partidas.pop(pid,None)
   for pid in list(salas_jugar.keys()):
     if ahora - salas_jugar[pid].get("last",ahora) > 300: salas_jugar.pop(pid,None)

@tree.command(name="jugar",description="Jugar")
async def jugar(i:discord.Interaction):
 ensure_user(i.user.id)
 emb=discord.Embed(title="🎮 ELEGÍ MODO - V6.5 UNIFICADO", description="1V1 (2) | TRIO (6) | ESCUADRON (8) - Todo en 1 mensaje + SAVE", color=0x9b59b6)
 await i.response.send_message(embed=emb, view=JugarMenuView(i.user.id))

@tree.command(name="truco",description="Partida CORTA")
async def truco_cmd(i:discord.Interaction, rival1: discord.Member, rival2: discord.Member = None, rival3: discord.Member = None):
 ensure_user(i.user.id)
 jugadores=[i.user.id]
 for r in [rival1,rival2,rival3]:
   if r and r.id!=i.user.id and not r.bot and r.id not in jugadores: jugadores.append(r.id)
 pid=f"corta_{random.randint(10000,999999)}"
 manos={}; m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m); nombres={}
 for uid in jugadores: manos[uid]=[m.pop() for _ in range(3)]
 nombres[i.user.id]=i.user.display_name
 if rival1: nombres[rival1.id]=rival1.display_name
 if rival2: nombres[rival2.id]=rival2.display_name
 if rival3: nombres[rival3.id]=rival3.display_name
 partidas[pid]={"jugadores":jugadores,"manos":manos,"jugadas_ronda":{},"rondas_ganadas":{uid:0 for uid in jugadores},"puntos":{uid:0 for uid in jugadores},"puntos_para_ganar":1,"tipo":"corta","nombres":nombres,"truco_nivel":1,"envido_jugado":False,"truco_pendiente":None,"envido_pendiente":None,"last_action":time.time(), "mensaje_id": None}
 emb=discord.Embed(title=f"🃏 TRUCO CORTO {' vs '.join(nombres.values())} | ID {pid[:6]}", description=f"Todo en este mensaje", color=0xe74c3c)
 file, emb = get_file_embed_titulo(emb, i.user.id)
 if file: msg = await i.response.send_message(embed=emb, file=file, view=PartidaUnificadaView(pid))
 else: await i.response.send_message(embed=emb, view=PartidaUnificadaView(pid))
 try:
     msg = await i.original_response()
     partidas[pid]["mensaje_id"]=msg.id
 except: pass

@tree.command(name="batalla",description="Batalla LARGA")
@app_commands.choices(puntos=[Choice(name="15 puntos", value=15), Choice(name="30 puntos", value=30)])
async def batalla(i:discord.Interaction, rival1: discord.Member, puntos: int, rival2: discord.Member = None, rival3: discord.Member = None):
 ensure_user(i.user.id)
 jugadores=[i.user.id]
 for r in [rival1,rival2,rival3]:
   if r and r.id!=i.user.id and not r.bot and r.id not in jugadores: jugadores.append(r.id)
 pid=f"larga_{random.randint(10000,999999)}"
 manos={}; m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m); nombres={}
 for uid in jugadores: manos[uid]=[m.pop() for _ in range(3)]
 nombres[i.user.id]=i.user.display_name
 if rival1: nombres[rival1.id]=rival1.display_name
 if rival2: nombres[rival2.id]=rival2.display_name
 if rival3: nombres[rival3.id]=rival3.display_name
 partidas[pid]={"jugadores":jugadores,"manos":manos,"jugadas_ronda":{},"rondas_ganadas":{uid:0 for uid in jugadores},"puntos":{uid:0 for uid in jugadores},"puntos_para_ganar":puntos,"tipo":"larga","nombres":nombres,"truco_nivel":1,"envido_jugado":False,"truco_pendiente":None,"envido_pendiente":None,"last_action":time.time(), "mensaje_id": None}
 emb=discord.Embed(title=f"⚔️ BATALLA LARGA {puntos} PTS | ID {pid[:6]}", description=f"Todo en este mensaje", color=0xf1c40f)
 file, emb = get_file_embed_titulo(emb, i.user.id)
 if file: await i.response.send_message(embed=emb, file=file, view=PartidaUnificadaView(pid))
 else: await i.response.send_message(embed=emb, view=PartidaUnificadaView(pid))
 try:
     msg = await i.original_response()
     partidas[pid]["mensaje_id"]=msg.id
 except: pass

@tree.command(name="tienda",description="Tienda")
@app_commands.choices(categoria=[Choice(name="TABLEROS", value="tableros"),Choice(name="PODERES", value="poderes")])
async def tienda(i:discord.Interaction, categoria: str):
 await i.response.defer(ephemeral=True)
 data=load_u(); coins=data.get(str(i.user.id),{}).get("coins",0)
 embed=discord.Embed(title=f"🛒 TIENDA {categoria.upper()} - {coins} coins",color=0xf1c40f)
 await i.followup.send(embed=embed,view=TiendaView(i.user.id,categoria),ephemeral=True)

@tree.command(name="ranking",description="Ranking")
async def ranking(i:discord.Interaction):
 await i.response.defer()
 data=load_u()
 top=sorted(data.items(), key=lambda x: x[1].get("wins_bot",0)+x[1].get("wins_amigo",0), reverse=True)[:10]
 desc="\n".join([f"{idx}. {info.get('wins_bot',0)+info.get('wins_amigo',0)} wins - ID {uid}" for idx,(uid,info) in enumerate(top,1)])
 await i.followup.send(embed=discord.Embed(title="🏆 RANKING",description=desc,color=0xf1c40f))

@tree.command(name="equipar",description="Equipar")
async def equipar(i:discord.Interaction):
 await i.response.defer(ephemeral=True)
 await i.followup.send(embed=discord.Embed(title="🎒 EQUIPAR",color=0x2ecc71),view=EquiparView(i.user.id),ephemeral=True)

@tree.command(name="perfil",description="Perfil")
async def perfil(i:discord.Interaction):
 ensure_user(i.user.id); data=load_u(); s=str(i.user.id)
 await i.response.send_message(f"💰 {data[s]['coins']} 🏆 Bot {data[s]['wins_bot']} Amigo {data[s]['wins_amigo']} | Tableros: {len(data[s]['owned'])}")

@tree.command(name="codigos",description="Canjear un codigo secreto")
async def codigos(i:discord.Interaction, codigo: str):
 await i.response.defer(ephemeral=True)
 ensure_user(i.user.id); data=load_u(); s=str(i.user.id)
 code_upper=codigo.strip().upper()
 found=None
 for k in CODIGOS:
  if k.upper()==code_upper: found=k; break
 if not found: await i.followup.send("❌ Codigo invalido", ephemeral=True); return
 if found in data[s]["codigos"]: await i.followup.send("❌ Ya canjeado", ephemeral=True); return
 if found=="SPRITE":
  if "espiritus" not in data[s]["owned"]: data[s]["owned"].append("espiritus")
  data[s]["equipado"]="espiritus"; data[s]["codigos"].append(found); save_u(data)
  await i.followup.send("✅ Canjeado! Tablero ESPIRITUS secreto!", ephemeral=True); return
 if found=="VICTORY ROYALE":
  if "fortnite" not in data[s]["owned"]: data[s]["owned"].append("fortnite")
  data[s]["equipado"]="fortnite"; data[s]["codigos"].append(found); save_u(data)
  await i.followup.send("✅ Canjeado! Tablero FORTNITE secreto!", ephemeral=True); return
 if found=="GAMER":
  if "gamer" not in data[s]["owned"]: data[s]["owned"].append("gamer")
  data[s]["equipado"]="gamer"; data[s]["codigos"].append(found); save_u(data)
  await i.followup.send("✅ Canjeado! Tablero GAMER secreto!", ephemeral=True); return
 if found in ["TRUCO!","1_ESPADA"]:
  data[s]["poderes"]["MAGO"]=data[s]["poderes"].get("MAGO",0)+1; data[s]["codigos"].append(found); save_u(data)
  await i.followup.send(f"✨ +1 MAGO!", ephemeral=True); return
 data[s]["coins"]+=CODIGOS[found]; data[s]["codigos"].append(found); save_u(data)
 await i.followup.send(f"💰 +{CODIGOS[found]} coins! Total: {data[s]['coins']}", ephemeral=True)

@tree.command(name="ayuda",description="Ayuda V6.5")
async def ayuda(i:discord.Interaction):
 await i.response.send_message(embed=discord.Embed(title="AYUDA V6.5 UNIFICADO",description="/jugar -> 1 mensaje por partida con ID\nVER MAZO por jugador en mismo mensaje\nProgreso guardado en data/usuarios.json\nNo repetir cartas + bloqueo truco propio",color=0x9b59b6))

@bot.event
async def on_ready():
 await tree.sync()
 print("V6.5 UNIFICADO + SAVE + NO REPETIR + CODIGOS")
 bot.loop.create_task(timeout_checker())

bot.run(os.getenv("DISCORD_TOKEN"))

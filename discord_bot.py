import discord, random, os, json, asyncio, time, requests
from discord import app_commands
from discord.app_commands import Choice
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def h(): return "ok BOT TRUCO V9.3.1 FIX"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
Thread(target=run_flask, daemon=True).start()
def keep_alive():
    while True:
        time.sleep(600)
        try: requests.get(os.environ.get("RENDER_EXTERNAL_URL", "https://trucobot-athd.onrender.com"), timeout=10)
        except: pass
Thread(target=keep_alive, daemon=True).start()

intents=discord.Intents.default()
intents.message_content=True
bot=discord.Client(intents=intents)
tree=app_commands.CommandTree(bot)
partidas={}
salas_jugar={}
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
    if max_e==0: max_e=max([envido_valor(c[0]) for c in mano]) if mano else 0
    return max_e
def calc_flor(mano):
    if len(mano)<3: return None
    if mano[0][1]==mano[1][1]==mano[2][1]: return 20+sum([envido_valor(c[0]) for c in mano])
    return None
def bot_elige_carta(mano_bot, carta_rival):
    orden = sorted(mano_bot, key=lambda c: v(c[0],c[1]))
    vr = v(carta_rival[0],carta_rival[1])
    for c in orden:
        if v(c[0],c[1]) > vr: return c
    return orden[0]

PRECIOS={"river":1000,"boca":1000,"san lorenzo":1000,"racing":1000,"springtrap":1250,"creeper":1500,"minecraft":1500,"diamante":1800,"oro":1200,"huggy_wuggy":1250,"mommy_long_legs":1250,"catnap":1250,"wobbly_life":1000,"geometry_dash":1000,"gta":1250,"gta_6":1250,"plants_vs_zombies":1250}

RECUPERACION={
    "joakops2015_69807": {"coins": 3000, "tableros": ["diamante", "springtrap", "san lorenzo"], "equipado": "diamante"},
    "green1109": {"coins": 500, "tableros": ["san lorenzo"], "equipado": "san lorenzo"}
}
def normaliza(s): return str(s).lower().strip()
def es_match(nombre_discord, key_recuperacion):
    nd=normaliza(nombre_discord); kr=normaliza(key_recuperacion)
    return kr in nd or nd in kr or kr.replace("_","") in nd.replace("_","")

LOTES={"poppy_playtime":{"boards":["huggy_wuggy","mommy_long_legs","catnap"],"precio":3000,"nombre":"POPPY PLAYTIME LOTE (3)"}}
CODIGOS={"TRUCO2026":1000,"navidad_se_acerca":350,"7_ORO":350,"TRUCO!":0,"1_ESPADA":0,"SPRITE":0,"VICTORY ROYALE":0,"GAMER":0,"DISCULPAS_POR_LOS_PROGRESOS_PERDIDOS":500,"PELUSA_GOD_XDDD":"pelu","THE_PROTOTIPE_ITS_HERE":"prototipo"}
PODERES_PRECIO={"MAGO":{"x1":400,"x10":3500},"OJO":{"x1":350,"x10":3000},"ESCUDO":{"x1":500,"x10":4500},"LADRON":{"x1":450,"x10":4000}}
EXPRESIONES={"FELIZ":200,"ENOJADO":200,"LLORANDO":200,"FUEGO":300,"RISA":300,"CORAZON":500}

os.makedirs("data", exist_ok=True)
FILE="data/usuarios.json"
FILE_BACKUP="data/usuarios_backup.json"

SAVE_URL_FIJA = "https://kvdb.io/6x7a9TrucoBotV93Backup2026/usuarios"
def get_save_url(): return SAVE_URL_FIJA
SAVE_URL = get_save_url()

def load_u():
    try:
        r=requests.get(SAVE_URL, timeout=8)
        if r.status_code==200:
            j=r.json()
            if isinstance(j, dict):
                try:
                    with open(FILE,"w") as f: json.dump(j,f,indent=2)
                    with open(FILE_BACKUP,"w") as f: json.dump(j,f,indent=2)
                except: pass
                if len(j)>0: return j
    except: pass
    if os.path.exists(FILE):
        try: 
            with open(FILE,"r") as f: return json.load(f)
        except: pass
    if os.path.exists(FILE_BACKUP):
        try: 
            with open(FILE_BACKUP,"r") as f: d=json.load(f)
            with open(FILE,"w") as fw: json.dump(d,fw,indent=2); return d
        except: pass
    return {}

def save_u(d):
    try: 
        with open(FILE,"w") as f: json.dump(d,f,indent=2)
    except: pass
    try: 
        with open(FILE_BACKUP,"w") as f: json.dump(d,f,indent=2)
    except: pass
    try: requests.put(SAVE_URL, json=d, timeout=8)
    except: pass

def ensure_user(uid, nombre_lookup=None):
    data=load_u(); s=str(uid)
    creado=False
    if s not in data:
        data[s]={"coins":0,"equipado":"default","owned":["default"],"codigos":[],"poderes":{"MAGO":0,"OJO":0,"ESCUDO":0,"LADRON":0},"owned_exp":["DEFAULT"],"exp_equipado":"DEFAULT","wins_bot":0,"wins_amigo":0,"recuperado":False}
        creado=True
    if "recuperado" not in data[s]:
        data[s]["recuperado"]=False
    try:
        if nombre_lookup and not data[s].get("recuperado", False):
            for key, rec in RECUPERACION.items():
                if es_match(nombre_lookup, key):
                    data[s]["coins"]=rec.get("coins",0)
                    for tb in rec.get("tableros",[]):
                        tb_low=tb.lower()
                        if tb_low not in [o.lower() for o in data[s].get("owned",[])]:
                            data[s]["owned"].append(tb_low)
                    if rec.get("equipado"):
                        data[s]["equipado"]=rec.get("equipado").lower()
                    data[s]["recuperado"]=True
                    print(f"RECUPERADO POR UNICA VEZ {nombre_lookup} -> {rec}")
                    save_u(data)
                    break
    except Exception as e:
        print(f"Error recuperacion: {e}")
    if creado:
        save_u(data)
    return data

def add_coins(uid,cant):
    data=load_u(); s=str(uid)
    if s not in data: ensure_user(uid); data=load_u()
    data[s]["coins"]=data[s].get("coins",0)+cant; save_u(data)
def add_win(uid,tipo):
    data=load_u(); s=str(uid)
    if s not in data: ensure_user(uid); data=load_u()
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
    data=load_u(); s=str(uid); eq=data.get(s,{}).get("equipado","default") if s in data else "default"; t=buscar_tablero(eq)
    if t and os.path.exists(t): return t
    return "tableros/Tablero.jpg" if os.path.exists("tableros/Tablero.jpg") else None
def get_file_embed_titulo(emb, uid):
    tpath = tab_user(uid)
    if tpath and os.path.exists(tpath): file = discord.File(tpath, filename="tablero.jpg"); emb.set_image(url="attachment://tablero.jpg"); return file, emb
    return None, emb

class JugarDeNuevoView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="JUGAR DE NUEVO", style=discord.ButtonStyle.success, emoji="🃏")
    async def replay(self, i, b):
        try: await i.response.defer()
        except: pass
        ensure_user(i.user.id, f"{i.user.name} {i.user.display_name}"); emb = discord.Embed(title="ELEGI MODO", description="1V1 (2) | TRIO (6) | ESCUADRON (8)", color=0x2ecc71)
        await i.followup.send(embed=emb, view=JugarMenuView(i.user.id))

class ManoPrivadaView(discord.ui.View):
    def __init__(self, pid, owner_id):
        super().__init__(timeout=120); d = partidas.get(pid)
        if not d or owner_id not in d["manos"]: return
        jugadas = list(d.get("jugadas_ronda", {}).values()) + d.get(f"cartas_jugadas_{owner_id}", [])
        for carta in d["manos"][owner_id]:
            if carta not in jugadas: self.add_item(CartaAmigoV4(carta, owner_id, pid))

class VerMazoBtn(discord.ui.Button):
    def __init__(self, pid, owner_id, label=None): self.pid=pid; self.owner_id=owner_id; super().__init__(label=label or "VER MAZO", style=discord.ButtonStyle.primary, emoji="👁️", row=1)
    async def callback(self, i):
        try: await i.response.defer(ephemeral=True)
        except: pass
        d = partidas.get(self.pid)
        mano = d["manos"].get(i.user.id, []); jugadas = d.get(f"cartas_jugadas_{i.user.id}", [])
        mano_restante = [c for c in mano if c not in jugadas and c not in d.get("jugadas_ronda",{}).values()]
        if not mano_restante: await i.followup.send("Ya no tenes cartas", ephemeral=True); return
        texto = ", ".join([f"{c[0]} de {c[1]}" for c in mano_restante])
        emb = discord.Embed(title="TU MAZO PRIVADO", description=f"Cartas: {texto}\nEnvido: {calc_envido(mano_restante)} | Flor: {calc_flor(d['manos'][i.user.id]) or 'No'}", color=0x3498db)
        await i.followup.send(embed=emb, view=ManoPrivadaView(self.pid, self.owner_id), ephemeral=True)

class TableroSelect(discord.ui.Select):
    def __init__(self,owner): self.owner=owner; owned=load_u().get(str(owner),{}).get("owned",["default"]); super().__init__(placeholder="TABLEROS - /equipar unico lugar", min_values=1, max_values=1, options=[discord.SelectOption(label=o.upper(), value=o) for o in owned[:25]])
    async def callback(self,i):
        try: await i.response.defer(ephemeral=True)
        except: pass
        data=load_u(); data[str(i.user.id)]["equipado"]=self.values[0]; save_u(data); await i.followup.send(f"Equipaste {self.values[0].upper()}", ephemeral=True)

class EquiparView(discord.ui.View):
    def __init__(self,owner): super().__init__(timeout=180); self.add_item(TableroSelect(owner))

class BotonTienda(discord.ui.Button):
    def __init__(self,nombre,precio,owner): 
        self.nombre=nombre; self.precio=precio; self.owner=owner
        data=load_u(); owned=data.get(str(owner),{}).get("owned",[])
        ya= nombre.lower() in [o.lower() for o in owned]
        label = f"{nombre.upper()} - YA TENES" if ya else f"{nombre.upper()} - {precio}"
        style = discord.ButtonStyle.secondary if ya else discord.ButtonStyle.primary
        super().__init__(label=label,style=style, disabled=ya)
    async def callback(self,i):
        try: await i.response.defer(ephemeral=True)
        except: pass
        data=load_u(); s=str(i.user.id)
        if data[s]["coins"]<self.precio: await i.followup.send("Te faltan coins",ephemeral=True); return
        data[s]["coins"]-=self.precio; data[s]["owned"].append(self.nombre); save_u(data); await i.followup.send(f"Compraste {self.nombre.upper()}",ephemeral=True)

class BotonLote(discord.ui.Button):
    def __init__(self,owner): 
        self.owner=owner
        data=load_u(); owned=[o.lower() for o in data.get(str(owner),{}).get("owned",[])]
        lote=LOTES["poppy_playtime"]
        tiene_todo=all(b in owned for b in lote["boards"])
        label = f"{lote['nombre']} - YA TENES" if tiene_todo else f"{lote['nombre']} - {lote['precio']}"
        super().__init__(label=label,style=discord.ButtonStyle.success if not tiene_todo else discord.ButtonStyle.secondary, disabled=tiene_todo)
    async def callback(self,i):
        try: await i.response.defer(ephemeral=True)
        except: pass
        data=load_u(); s=str(i.user.id); lote=LOTES["poppy_playtime"]
        if data[s]["coins"]<lote["precio"]: await i.followup.send(f"Te faltan coins",ephemeral=True); return
        data[s]["coins"]-=lote["precio"]
        for b in lote["boards"]:
            if b.lower() not in [o.lower() for o in data[s]["owned"]]: data[s]["owned"].append(b)
        save_u(data); await i.followup.send(f"Compraste LOTE {lote['nombre']}",ephemeral=True)

class BotonPoder(discord.ui.Button):
    def __init__(self,nombre,precio,owner,tipo):
        self.nombre=nombre; self.precio=precio; self.owner=owner; self.tipo=tipo
        super().__init__(label=f"{nombre} {tipo} - {precio}",style=discord.ButtonStyle.primary)
    async def callback(self,i):
        try: await i.response.defer(ephemeral=True)
        except: pass
        data=load_u(); s=str(i.user.id)
        if data[s]["coins"]<self.precio: await i.followup.send("Te faltan coins",ephemeral=True); return
        data[s]["coins"]-=self.precio
        cant=10 if self.tipo=="x10" else 1
        data[s]["poderes"][self.nombre]=data[s]["poderes"].get(self.nombre,0)+cant
        save_u(data); await i.followup.send(f"Compraste {self.nombre} {self.tipo}",ephemeral=True)

class BotonExp(discord.ui.Button):
    def __init__(self,nombre,precio,owner):
        self.nombre=nombre; self.precio=precio; self.owner=owner
        data=load_u(); owned_exp=data.get(str(owner),{}).get("owned_exp",[])
        ya=nombre in owned_exp or nombre.lower() in [x.lower() for x in owned_exp]
        super().__init__(label=f"{nombre.upper()} - {'YA TENES' if ya else precio}",style=discord.ButtonStyle.secondary if ya else discord.ButtonStyle.primary, disabled=ya)
    async def callback(self,i):
        try: await i.response.defer(ephemeral=True)
        except: pass
        data=load_u(); s=str(i.user.id)
        if data[s]["coins"]<self.precio: await i.followup.send("Te faltan coins",ephemeral=True); return
        data[s]["coins"]-=self.precio
        if self.nombre not in data[s]["owned_exp"]: data[s]["owned_exp"].append(self.nombre)
        save_u(data); await i.followup.send(f"Compraste expresion {self.nombre.upper()}!",ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self,owner,categoria="tableros"):
        super().__init__(timeout=300)
        if categoria=="tableros":
            self.add_item(BotonLote(owner))
            for n,p in PRECIOS.items(): self.add_item(BotonTienda(n,p,owner))
        elif categoria=="poderes":
            for nombre, precios in PODERES_PRECIO.items():
                self.add_item(BotonPoder(nombre, precios["x1"], owner, "x1"))
                self.add_item(BotonPoder(nombre, precios["x10"], owner, "x10"))
        elif categoria=="expresiones":
            for n,p in EXPRESIONES.items(): self.add_item(BotonExp(n,p,owner))

class TrucoRespAmigo(discord.ui.View):
    def __init__(self,pid, nivel, cantor_id): super().__init__(timeout=60); self.pid=pid; self.nivel=nivel; self.cantor_id=cantor_id
    @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success, row=0)
    async def quiero(self,i,b):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.pid)
        if not d or d.get("truco_pendiente") is None: return
        if i.user.id == self.cantor_id: await i.followup.send("No podes querer tu propio truco",ephemeral=True); return
        d["last_action"]=time.time()
        if self.nivel==1: d["truco_nivel"]=2
        elif self.nivel==2: d["truco_nivel"]=3
        elif self.nivel==3: d["truco_nivel"]=4
        d["truco_pendiente"]=None; await i.followup.send(f"🔥 {d['nombres'][i.user.id]} QUIERO! Vale {d['truco_nivel']}"); self.stop()
    @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger, row=0)
    async def no(self,i,b):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.pid); ganador_id = self.cantor_id; pts = d.get("truco_nivel",1); d["truco_pendiente"]=None; d["puntos"][ganador_id]+=pts
        await i.followup.send(f"❌ NO QUIERO! {d['nombres'][ganador_id]} gana {pts} pts")
        if d.get("tipo")=="corta" or d["puntos"][ganador_id]>=d.get("puntos_para_ganar",15): partidas.pop(self.pid,None)
        self.stop()
    @discord.ui.button(label="RETRUCO",style=discord.ButtonStyle.primary, row=1)
    async def retruco(self,i,b):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.pid)
        if self.nivel!=1: await i.followup.send("Retruco solo despues de Truco",ephemeral=True); return
        d["truco_pendiente"]={"cantor":i.user.id, "nivel":2}; await i.followup.send(f"🔥 {d['nombres'][i.user.id]} canta RETRUCO! Vale 3", view=TrucoRespAmigo(self.pid,2,i.user.id)); self.stop()
    @discord.ui.button(label="VALE 4",style=discord.ButtonStyle.primary, row=1)
    async def vale4(self,i,b):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.pid)
        if self.nivel!=2: await i.followup.send("Vale 4 solo despues de Retruco",ephemeral=True); return
        d["truco_pendiente"]={"cantor":i.user.id, "nivel":3}; await i.followup.send(f"💥 {d['nombres'][i.user.id]} canta VALE 4!", view=TrucoRespAmigo(self.pid,3,i.user.id)); self.stop()

class EnvidoRespAmigo(discord.ui.View):
    def __init__(self,pid, cantor_id): super().__init__(timeout=60); self.pid=pid; self.cantor_id=cantor_id
    @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success, row=0)
    async def quiero(self,i,b):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.pid)
        if not d or d.get("envido_pendiente") is None: return
        tipo = d["envido_pendiente"].get("tipo","envido"); envidos={uid: calc_envido(d["manos"][uid]) for uid in d["jugadores"]}; ganador = max(envidos, key=lambda k: envidos[k])
        if tipo=="envido": pts=2
        elif tipo=="real": pts=3
        else: pts = d["puntos_para_ganar"] - max(d["puntos"].values()) if d.get("tipo")!="corta" else 5
        d["puntos"][ganador]+=pts; d["envido_pendiente"]=None; d["envido_jugado"]=True; await i.followup.send(f"💰 QUIERO {tipo.upper()}! {envidos} -> Gana {d['nombres'][ganador]} +{pts}"); self.stop()
    @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger, row=0)
    async def no(self,i,b):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.pid); d["envido_pendiente"]=None; d["envido_jugado"]=True; cantor = d.get("envido_cantor")
        if cantor: d["puntos"][cantor]+=1; await i.followup.send(f"💰 NO QUIERO! +1 para {d['nombres'][cantor]}"); self.stop()
    @discord.ui.button(label="REAL ENVIDO",style=discord.ButtonStyle.primary, row=1)
    async def real(self,i,b):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.pid); d["envido_pendiente"]={"cantor":i.user.id, "tipo":"real"}; await i.followup.send(f"💰 {d['nombres'][i.user.id]} canta REAL ENVIDO!", view=EnvidoRespAmigo(self.pid,i.user.id)); self.stop()
    @discord.ui.button(label="FALTA ENVIDO",style=discord.ButtonStyle.primary, row=1)
    async def falta(self,i,b):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.pid); d["envido_pendiente"]={"cantor":i.user.id, "tipo":"falta"}; await i.followup.send(f"💰💰 {d['nombres'][i.user.id]} canta FALTA ENVIDO!", view=EnvidoRespAmigo(self.pid,i.user.id)); self.stop()

class FlorRespAmigo(discord.ui.View):
    def __init__(self,pid, cantor_id, nivel): super().__init__(timeout=60); self.pid=pid; self.cantor_id=cantor_id; self.nivel=nivel
    @discord.ui.button(label="QUIERO",style=discord.ButtonStyle.success, row=0)
    async def quiero(self,i,b):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.pid); flor_cantor = calc_flor(d["manos"][self.cantor_id]); flor_mio = calc_flor(d["manos"][i.user.id])
        if self.nivel==1: pts=3
        elif self.nivel==2: pts=6
        else: pts = d["puntos_para_ganar"] - max(d["puntos"].values()) if d.get("tipo")!="corta" else 3
        ganador = self.cantor_id if (flor_cantor or 0) >= (flor_mio or 0) else i.user.id
        d["puntos"][ganador]+=pts; d["flor_pendiente"]=None; d["envido_jugado"]=True
        await i.followup.send(f"🌸 QUIERO! {flor_cantor} vs {flor_mio} -> Gana {d['nombres'][ganador]} +{pts}")
        if self.nivel==3: partidas.pop(self.pid,None)
        self.stop()
    @discord.ui.button(label="NO QUIERO",style=discord.ButtonStyle.danger, row=0)
    async def no(self,i,b):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.pid)
        if self.nivel==1: pts=3
        elif self.nivel==2: pts=4
        else: pts=6
        d["puntos"][self.cantor_id]+=pts; d["flor_pendiente"]=None; d["envido_jugado"]=True
        await i.followup.send(f"🌸 NO QUIERO! +{pts} para {d['nombres'][self.cantor_id]}"); self.stop()
    @discord.ui.button(label="CONTRAFLOR",style=discord.ButtonStyle.primary, row=1)
    async def contraflor(self,i,b):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.pid)
        if self.nivel!=1: await i.followup.send("Solo despues de Flor",ephemeral=True); return
        if not calc_flor(d["manos"][i.user.id]): await i.followup.send("Necesitas Flor!",ephemeral=True); return
        d["flor_pendiente"]={"cantor":i.user.id, "nivel":2}; await i.followup.send(f"🌸🌸 {d['nombres'][i.user.id]} canta CONTRAFLOR! Vale 6", view=FlorRespAmigo(self.pid,i.user.id,2)); self.stop()
    @discord.ui.button(label="CONTRAFLOR AL RESTO",style=discord.ButtonStyle.primary, row=1)
    async def resto(self,i,b):
        try: await i.response.defer()
        except: pass
        if self.nivel!=2: await i.followup.send("Al resto solo despues de Contraflor",ephemeral=True); return
        d["flor_pendiente"]={"cantor":i.user.id, "nivel":3}; await i.followup.send(f"🔥 {d['nombres'][i.user.id]} CONTRAFLOR AL RESTO!", view=FlorRespAmigo(self.pid,i.user.id,3)); self.stop()

class C(discord.ui.Button):
    def __init__(self,carta,owner): self.carta=carta; self.owner=owner; super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary,row=0)
    async def callback(self,i):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.owner)
        if not d or d.get("truco_pendiente") or d.get("envido_pendiente") or d.get("flor_pendiente"): await i.followup.send("Espera canto!",ephemeral=True); return
        d["last_action"]=time.time(); self.disabled=True
        try: await i.edit_original_response(view=self.view)
        except: pass
        await i.followup.send(f"Tiraste {self.carta[0]} de {self.carta[1]}"); m = await i.followup.send("BOT PENSANDO..."); await asyncio.sleep(0.8)
        try: await m.delete()
        except: pass
        if len(d["bot"])==0: return
        cb=bot_elige_carta(d["bot"], self.carta); d["bot"].remove(cb)
        if self.carta in d["mano_jugador"]: d["mano_jugador"].remove(self.carta)
        vy=v(self.carta[0],self.carta[1]); vb=v(cb[0],cb[1])
        if vy>vb: d["pj"]+=1; txt=f"GANASTE! Bot: {cb[0]} de {cb[1]} {d['pj']}-{d['pb']}"
        elif vy<vb: d["pb"]+=1; txt=f"PERDISTE! Bot: {cb[0]} de {cb[1]} {d['pj']}-{d['pb']}"
        else: txt=f"Empate {d['pj']}-{d['pb']}"
        if d["pj"]>=2 or d["pb"]>=2 or len(d["mano_jugador"])==0:
            if d["pj"]>d["pb"]: add_coins(self.owner,250); add_win(self.owner,"bot"); txt=f"GANASTE +250! {d['pj']}-{d['pb']}"
            else: txt=f"PERDISTE {d['pj']}-{d['pb']}"
            partidas.pop(self.owner,None); await i.followup.send(txt, view=JugarDeNuevoView()); return
        await i.followup.send(txt)

class T(discord.ui.Button):
    def __init__(self,o): self.o=o; super().__init__(label="TRUCO",style=discord.ButtonStyle.danger,row=1)
    async def callback(self,i):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.o)
        if not d or d.get("truco_pendiente"): return
        d["truco_nivel"]=min(4,d.get("truco_nivel",1)+1); await i.followup.send(f"Bot: QUIERO! Vale {d['truco_nivel']}")
class E(discord.ui.Button):
    def __init__(self,o): self.o=o; super().__init__(label="ENVIDO",style=discord.ButtonStyle.success,row=1)
    async def callback(self,i):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.o); d["pj"]+=1; await i.followup.send(f"Bot: NO QUIERO +1")
class S(discord.ui.Button):
    def __init__(self,o): self.o=o; super().__init__(label="IRSE AL MAZO",style=discord.ButtonStyle.secondary,row=1)
    async def callback(self,i): 
        try: await i.response.defer()
        except: pass
        partidas.pop(self.o,None); await i.followup.send("Te fuiste al mazo")
class V(discord.ui.View):
    def __init__(self,o,m): super().__init__(timeout=None); [self.add_item(C(c,o)) for c in m]; self.add_item(T(o)); self.add_item(E(o)); self.add_item(S(o))

class CartaAmigoV4(discord.ui.Button):
    def __init__(self,carta,owner,pid): self.carta=carta; self.owner=owner; self.pid=pid; super().__init__(label=f"{carta[0]} de {carta[1]}",style=discord.ButtonStyle.primary)
    async def callback(self,i):
        try: await i.response.defer(ephemeral=True)
        except: pass
        d=partidas.get(self.pid)
        if not d or i.user.id not in d["jugadores"] or d.get("truco_pendiente") or d.get("envido_pendiente") or d.get("flor_pendiente"): await i.followup.send(f"Hay canto pendiente!", ephemeral=True); return
        if self.owner in d["jugadas_ronda"]: await i.followup.send("Ya jugaste",ephemeral=True); return
        d["last_action"]=time.time()
        if self.carta in d["manos"][self.owner]: d["manos"][self.owner].remove(self.carta)
        d.setdefault(f"cartas_jugadas_{self.owner}", []).append(self.carta); d["jugadas_ronda"][self.owner]=self.carta
        await i.followup.send(f"Tiraste {self.carta[0]} de {self.carta[1]} (solo vos)", ephemeral=True)
        await i.channel.send(f"{d['nombres'][self.owner]} tiro carta boca abajo")
        if len(d["jugadas_ronda"])==len(d["jugadores"]):
            mejor=None; ganador=None; texto_ronda=""
            for uid,carta in d["jugadas_ronda"].items():
                val=v(carta[0],carta[1]); texto_ronda+=f"**{d['nombres'][uid]}**: {carta[0]} de {carta[1]} | "
                if mejor is None or val>mejor: mejor=val; ganador=uid
            d["rondas_ganadas"][ganador]+=1; await i.channel.send(f"Cartas: {texto_ronda}\nRonda para **{d['nombres'][ganador]}**"); d["jugadas_ronda"]={}
            if max(d["rondas_ganadas"].values())>=2 or sum(d["rondas_ganadas"].values())>=3:
                ganador_mano = max(d["rondas_ganadas"], key=lambda k: d["rondas_ganadas"][k]); puntos_mano = d.get("truco_nivel",1); d["puntos"][ganador_mano]+=puntos_mano
                await i.channel.send(f"Mano para **{d['nombres'][ganador_mano]}** +{puntos_mano} pts | { {d['nombres'][k]:v for k,v in d['puntos'].items()} }")
                if d["tipo"]=="corta": add_coins(ganador_mano,250); add_win(ganador_mano,"amigo"); await i.channel.send(f"GANA {d['nombres'][ganador_mano]} +250", view=JugarDeNuevoView()); partidas.pop(self.pid,None); return
                else:
                    if d["puntos"][ganador_mano]>=d["puntos_para_ganar"]: add_coins(ganador_mano,500); await i.channel.send(f"{d['nombres'][ganador_mano]} GANA +500!", view=JugarDeNuevoView()); partidas.pop(self.pid,None); return
                    else: await nueva_mano_v4(self.pid,i.channel)

async def nueva_mano_v4(pid, channel):
    d=partidas.get(pid)
    if not d: return
    m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m)
    for uid in d["jugadores"]: d["manos"][uid]=[m.pop() for _ in range(3)]; d.pop(f"cartas_jugadas_{uid}", None)
    d["jugadas_ronda"]={}; d["rondas_ganadas"]={uid:0 for uid in d["jugadores"]}; d["truco_nivel"]=1; d["envido_jugado"]=False; d["truco_pendiente"]=None; d["envido_pendiente"]=None; d["flor_pendiente"]=None; d["last_action"]=time.time()
    flores={}
    for uid in d["jugadores"]:
        f=calc_flor(d["manos"][uid])
        if f: flores[uid]=f
    emb=discord.Embed(title=f"NUEVA MANO - {d['tipo'].upper()} | ID {pid[:6]}", description=f"Jugadores: {', '.join([d['nombres'][uid] for uid in d['jugadores']])}\nMarcador: { {d['nombres'][k]:v for k,v in d['puntos'].items()} }", color=0xe74c3c)
    file, emb = get_file_embed_titulo(emb, d["jugadores"][0])
    if file: msg = await channel.send(embed=emb, file=file, view=PartidaUnificadaView(pid))
    else: msg = await channel.send(embed=emb, view=PartidaUnificadaView(pid))
    d["mensaje_id"]=msg.id
    if flores:
        cantor=list(flores.keys())[0]
        d["flor_pendiente"]={"cantor":cantor, "nivel":1}
        await channel.send(f"🌸 FLOR AUTOMATICA! **{d['nombres'][cantor]}** tiene {flores[cantor]} pts", view=FlorRespAmigo(pid,cantor,1))

class TrucoAmigoV4(discord.ui.Button):
    def __init__(self,pid,owner): self.pid=pid; self.owner=owner; super().__init__(label="TRUCO",style=discord.ButtonStyle.danger,row=0)
    async def callback(self,i):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.pid)
        if not d or d.get("truco_pendiente") or d.get("envido_pendiente") or d.get("flor_pendiente"): return
        nivel=d.get("truco_nivel",1)
        if nivel>=4: await i.followup.send("Ya es VALE 4",ephemeral=True); return
        d["last_action"]=time.time(); d["truco_pendiente"]={"cantor":i.user.id, "nivel":nivel}
        await i.followup.send(f"**{d['nombres'][i.user.id]}** canta {'TRUCO' if nivel==1 else 'RETRUCO' if nivel==2 else 'VALE 4'}! Vale {nivel+1}", view=TrucoRespAmigo(self.pid,nivel,i.user.id))

class EnvidoAmigoV4(discord.ui.Button):
    def __init__(self,pid,owner): self.pid=pid; self.owner=owner; super().__init__(label="ENVIDO",style=discord.ButtonStyle.success,row=0)
    async def callback(self,i):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.pid)
        if not d or d.get("envido_pendiente") or d.get("truco_pendiente") or d.get("flor_pendiente"): await i.followup.send("Ya hay canto pendiente",ephemeral=True); return
        if d.get("envido_jugado") or len(d["jugadas_ronda"])!=0: await i.followup.send("Envido solo al principio",ephemeral=True); return
        d["last_action"]=time.time(); d["envido_cantor"]=i.user.id; d["envido_pendiente"]={"cantor":i.user.id, "tipo":"envido"}
        envido_p = calc_envido(d["manos"][i.user.id]); await i.followup.send(f"**{d['nombres'][i.user.id]}** canta ENVIDO! Tiene {envido_p}", view=EnvidoRespAmigo(self.pid,i.user.id))

class SalirAmigoV4(discord.ui.Button):
    def __init__(self,pid,owner): self.pid=pid; self.owner=owner; super().__init__(label="IRSE AL MAZO",style=discord.ButtonStyle.secondary,row=2)
    async def callback(self,i):
        try: await i.response.defer()
        except: pass
        d=partidas.get(self.pid)
        if d["tipo"]=="corta": await i.followup.send(f"{d['nombres'][i.user.id]} se fue"); partidas.pop(self.pid,None)
        else: otros=[uid for uid in d["jugadores"] if uid!=i.user.id]; [add_coins(uid,100) for uid in otros]; await i.followup.send(f"ABANDONO +100"); partidas.pop(self.pid,None) if len(otros)==1 else d.update({"jugadores":otros})

class PartidaUnificadaView(discord.ui.View):
    def __init__(self, pid):
        super().__init__(timeout=None); self.pid = pid; d = partidas.get(pid)
        if not d: return
        for uid in d["jugadores"]: nombre = d["nombres"].get(uid, "Jugador")[:12]; self.add_item(VerMazoBtn(pid, uid, label=f"MAZO {nombre}"))
        first = d["jugadores"][0]; self.add_item(TrucoAmigoV4(pid, first)); self.add_item(EnvidoAmigoV4(pid, first)); self.add_item(SalirAmigoV4(pid, first))

class JugarMenuView(discord.ui.View):
    def __init__(self, owner_id): super().__init__(timeout=180); self.owner_id=owner_id
    @discord.ui.button(label="1V1", style=discord.ButtonStyle.primary, row=0)
    async def b_1v1(self,i,b): 
        try: await i.response.defer()
        except: pass
        await self.crear_sala(i, "1v1", 2)
    @discord.ui.button(label="TRIO", style=discord.ButtonStyle.primary, row=0)
    async def b_trio(self,i,b): 
        try: await i.response.defer()
        except: pass
        await self.crear_sala(i, "trio", 6)
    @discord.ui.button(label="ESCUADRON", style=discord.ButtonStyle.primary, row=0)
    async def b_esc(self,i,b): 
        try: await i.response.defer()
        except: pass
        await self.crear_sala(i, "escuadron", 8)
    @discord.ui.button(label="BOT 1V1", style=discord.ButtonStyle.success, row=1)
    async def b_bot(self,i,b): 
        try: await i.response.defer()
        except: pass
        await self.iniciar_bot(i, "bot")
    @discord.ui.button(label="BOT TRIO", style=discord.ButtonStyle.success, row=1)
    async def b_bot_trio(self,i,b): 
        try: await i.response.defer()
        except: pass
        await self.iniciar_bot(i, "bot_trio")
    @discord.ui.button(label="BOT ESCUADRON", style=discord.ButtonStyle.success, row=1)
    async def b_bot_esc(self,i,b): 
        try: await i.response.defer()
        except: pass
        await self.iniciar_bot(i, "bot_escuadron")

    async def crear_sala(self, i, modo, necesarios):
        pid=f"lobby_{i.channel.id}"; salas_jugar[pid]={"modo":modo,"necesarios":necesarios,"jugadores":[i.user.id],"nombres":{i.user.id:i.user.display_name},"creador":i.user.id,"creador_nombre":i.user.display_name,"last":time.time()}
        emb=discord.Embed(title=f"SALA {modo.upper()} CREADA ({1}/{necesarios})", description=f"**{i.user.display_name} TE HA RETADO A UN TRUCO!**", color=0xe74c3c); file, emb = get_file_embed_titulo(emb, i.user.id)
        if file: await i.followup.send(embed=emb, file=file, view=SalaEsperaView(pid))
        else: await i.followup.send(embed=emb, view=SalaEsperaView(pid))
        await i.channel.send(f"@everyone **{i.user.display_name} TE RETO A UN TRUCO! Modo {modo.upper()}**")

    async def iniciar_bot(self, i, modo):
        ensure_user(i.user.id, f"{i.user.name} {i.user.display_name}"); m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m); mj=[m.pop() for _ in range(3)]; mb=[m.pop() for _ in range(3)]
        partidas[i.user.id]={"bot":mb.copy(),"mano_jugador":mj.copy(),"pj":0,"pb":0,"truco_nivel":1,"envido_jugado":False,"last_action":time.time()}
        emb=discord.Embed(title=f"TRUCO vs {modo.upper()}", description=f"Modo {modo} - Bot dificil", color=0x1e8449); file, emb = get_file_embed_titulo(emb, i.user.id); view=V(i.user.id,mj)
        if file: await i.followup.send(embed=emb, file=file, view=view)
        else: await i.followup.send(embed=emb, view=view)

class SalaEsperaView(discord.ui.View):
    def __init__(self, pid): super().__init__(timeout=None); self.pid=pid
    @discord.ui.button(label="ESTOY LISTO", style=discord.ButtonStyle.success)
    async def listo(self,i,b):
        try: await i.response.defer()
        except: pass
        sala=salas_jugar.get(self.pid)
        if not sala: await i.followup.send("Sala ya no existe",ephemeral=True); return
        if i.user.id not in sala["jugadores"]: sala["jugadores"].append(i.user.id); sala["nombres"][i.user.id]=i.user.display_name
        sala["last"]=time.time()
        if len(sala["jugadores"])>=sala["necesarios"]:
            jugadores=sala["jugadores"]; nombres=sala["nombres"]; manos={}; m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m)
            for uid in jugadores: manos[uid]=[m.pop() for _ in range(3)]
            partidas[self.pid]={"jugadores":jugadores,"manos":manos,"jugadas_ronda":{},"rondas_ganadas":{uid:0 for uid in jugadores},"puntos":{uid:0 for uid in jugadores},"puntos_para_ganar":1,"tipo":"corta","nombres":nombres,"truco_nivel":1,"envido_jugado":False,"truco_pendiente":None,"envido_pendiente":None,"flor_pendiente":None,"last_action":time.time(), "mensaje_id": None}
            salas_jugar.pop(self.pid,None); emb=discord.Embed(title=f"PARTIDA {sala['modo'].upper()} INICIADA", description=f"Jugadores: {', '.join(nombres.values())}", color=0x2ecc71); file, emb = get_file_embed_titulo(emb, jugadores[0]); view = PartidaUnificadaView(self.pid)
            if file: await i.followup.send(embed=emb, file=file, view=view)
            else: await i.followup.send(embed=emb, view=view)
        else: emb=discord.Embed(title=f"SALA {sala['modo'].upper()} ({len(sala['jugadores'])}/{sala['necesarios']})", description=f"Jugadores: {', '.join(sala['nombres'].values())}", color=0xe74c3c); await i.followup.send(embed=emb, view=self)
    @discord.ui.button(label="INVITAR A TODOS", style=discord.ButtonStyle.primary)
    async def invitar(self,i,b): 
        try: await i.response.defer()
        except: pass
        await i.followup.send(f"@everyone {salas_jugar.get(self.pid,{}).get('creador_nombre','Alguien')} TE RETO!")
    @discord.ui.button(label="CANCELAR SALA", style=discord.ButtonStyle.danger)
    async def cancelar(self,i,b):
        try: await i.response.defer()
        except: pass
        sala=salas_jugar.get(self.pid)
        if not sala: return
        if i.user.id!=sala["creador"]: await i.followup.send("Solo el creador puede cancelar",ephemeral=True); return
        salas_jugar.pop(self.pid,None); await i.followup.send(embed=discord.Embed(title="SALA CANCELADA", color=0x95a5a6))

async def timeout_checker():
    while True:
        await asyncio.sleep(30); ahora=time.time()
        for pid in list(partidas.keys()):
            if ahora - partidas[pid].get("last_action",ahora) > TIMEOUT_SEGUNDOS: partidas.pop(pid,None)
        for pid in list(salas_jugar.keys()):
            if ahora - salas_jugar[pid].get("last",ahora) > 300: salas_jugar.pop(pid,None)

@tree.command(name="jugar",description="Jugar")
async def jugar(i:discord.Interaction):
    ensure_user(i.user.id, f"{i.user.name} {i.user.display_name}"); emb=discord.Embed(title="ELEGI MODO - V9.3.1 FIX", description="1V1 (2) | TRIO (6) | ESCUADRON (8) | BOT TRIO | BOT ESCUADRON", color=0x9b59b6)
    await i.response.send_message(embed=emb, view=JugarMenuView(i.user.id))
@tree.command(name="truco",description="Partida CORTA")
async def truco_cmd(i:discord.Interaction, rival1: discord.Member, rival2: discord.Member = None, rival3: discord.Member = None):
    ensure_user(i.user.id, f"{i.user.name} {i.user.display_name}"); jugadores=[i.user.id]
    for r in [rival1,rival2,rival3]:
        if r and r.id!=i.user.id and not r.bot and r.id not in jugadores: jugadores.append(r.id)
    pid=f"corta_{random.randint(10000,999999)}"; manos={}; m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m); nombres={}
    for uid in jugadores: manos[uid]=[m.pop() for _ in range(3)]
    nombres[i.user.id]=i.user.display_name
    if rival1: nombres[rival1.id]=rival1.display_name
    if rival2: nombres[rival2.id]=rival2.display_name
    if rival3: nombres[rival3.id]=rival3.display_name
    partidas[pid]={"jugadores":jugadores,"manos":manos,"jugadas_ronda":{},"rondas_ganadas":{uid:0 for uid in jugadores},"puntos":{uid:0 for uid in jugadores},"puntos_para_ganar":1,"tipo":"corta","nombres":nombres,"truco_nivel":1,"envido_jugado":False,"truco_pendiente":None,"envido_pendiente":None,"flor_pendiente":None,"last_action":time.time(), "mensaje_id": None}
    emb=discord.Embed(title=f"TRUCO CORTO {' vs '.join(nombres.values())}", description=f"Full truco + Flor auto", color=0xe74c3c); file, emb = get_file_embed_titulo(emb, i.user.id)
    if file: await i.response.send_message(embed=emb, file=file, view=PartidaUnificadaView(pid))
    else: await i.response.send_message(embed=emb, view=PartidaUnificadaView(pid))
@tree.command(name="batalla",description="Batalla LARGA")
@app_commands.choices(puntos=[Choice(name="15 puntos", value=15), Choice(name="30 puntos", value=30)])
async def batalla(i:discord.Interaction, rival1: discord.Member, puntos: int, rival2: discord.Member = None, rival3: discord.Member = None):
    ensure_user(i.user.id, f"{i.user.name} {i.user.display_name}"); jugadores=[i.user.id]
    for r in [rival1,rival2,rival3]:
        if r and r.id!=i.user.id and not r.bot and r.id not in jugadores: jugadores.append(r.id)
    pid=f"larga_{random.randint(10000,999999)}"; manos={}; m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m); nombres={}
    for uid in jugadores: manos[uid]=[m.pop() for _ in range(3)]
    nombres[i.user.id]=i.user.display_name
    if rival1: nombres[rival1.id]=rival1.display_name
    if rival2: nombres[rival2.id]=rival2.display_name
    if rival3: nombres[rival3.id]=rival3.display_name
    partidas[pid]={"jugadores":jugadores,"manos":manos,"jugadas_ronda":{},"rondas_ganadas":{uid:0 for uid in jugadores},"puntos":{uid:0 for uid in jugadores},"puntos_para_ganar":puntos,"tipo":"larga","nombres":nombres,"truco_nivel":1,"envido_jugado":False,"truco_pendiente":None,"envido_pendiente":None,"flor_pendiente":None,"last_action":time.time(), "mensaje_id": None}
    emb=discord.Embed(title=f"BATALLA LARGA {puntos} PTS", description=f"Full truco + Flor auto", color=0xf1c40f); file, emb = get_file_embed_titulo(emb, i.user.id)
    if file: await i.response.send_message(embed=emb, file=file, view=PartidaUnificadaView(pid))
    else: await i.response.send_message(embed=emb, view=PartidaUnificadaView(pid))

@tree.command(name="tienda",description="Tienda")
@app_commands.choices(categoria=[Choice(name="TABLEROS", value="tableros"),Choice(name="PODERES", value="poderes"),Choice(name="EXPRESIONES", value="expresiones")])
async def tienda(i:discord.Interaction, categoria: str):
    await i.response.defer(ephemeral=True); data=load_u(); coins=data.get(str(i.user.id),{}).get("coins",0)
    embed=discord.Embed(title=f"TIENDA {categoria.upper()} - {coins} coins - V9.3.1",color=0xf1c40f); await i.followup.send(embed=embed,view=TiendaView(i.user.id,categoria),ephemeral=True)

@tree.command(name="regalar",description="Regalar tablero")
async def regalar(i:discord.Interaction, tablero: str, usuario: discord.Member):
    await i.response.defer(ephemeral=True); ensure_user(i.user.id, f"{i.user.name} {i.user.display_name}"); ensure_user(usuario.id, f"{usuario.name} {usuario.display_name}"); data=load_u(); s=str(i.user.id); s2=str(usuario.id); tablero=tablero.lower()
    if tablero in ["poppy_playtime","poppy","poppy_lote"]:
        precio=LOTES["poppy_playtime"]["precio"]
        if data[s]["coins"]<precio: await i.followup.send(f"Te faltan coins",ephemeral=True); return
        data[s]["coins"]-=precio
        for b in LOTES["poppy_playtime"]["boards"]:
            if b.lower() not in [o.lower() for o in data[s2]["owned"]]: data[s2]["owned"].append(b)
        save_u(data); await i.followup.send(f"Le regalaste LOTE POPPY a {usuario.display_name}!",ephemeral=True); return
    precio=PRECIOS.get(tablero)
    if not precio: await i.followup.send(f"No existe. Usa: {', '.join(PRECIOS.keys())} o poppy_playtime",ephemeral=True); return
    if data[s]["coins"]<precio: await i.followup.send(f"Te faltan coins",ephemeral=True); return
    if tablero.lower() in [o.lower() for o in data[s2].get("owned",[])]: await i.followup.send("Ya tiene ese tablero",ephemeral=True); return
    data[s]["coins"]-=precio
    if tablero not in data[s2]["owned"]: data[s2]["owned"].append(tablero)
    save_u(data); await i.followup.send(f"Le regalaste {tablero.upper()} a {usuario.display_name}!",ephemeral=True)

@tree.command(name="ranking",description="Ranking")
async def ranking(i:discord.Interaction):
    await i.response.defer(); data=load_u(); top=sorted(data.items(), key=lambda x: x[1].get("wins_bot",0)+x[1].get("wins_amigo",0), reverse=True)[:10]
    desc="\n".join([f"{idx}. {info.get('wins_bot',0)+info.get('wins_amigo',0)} wins - ID {uid}" for idx,(uid,info) in enumerate(top,1)])
    await i.followup.send(embed=discord.Embed(title="RANKING",description=desc,color=0xf1c40f))
@tree.command(name="equipar",description="Equipar - UNICO LUGAR")
async def equipar(i:discord.Interaction):
    await i.response.defer(ephemeral=True); await i.followup.send(embed=discord.Embed(title="EQUIPAR",color=0x2ecc71),view=EquiparView(i.user.id),ephemeral=True)
@tree.command(name="perfil",description="Perfil")
async def perfil(i:discord.Interaction):
    ensure_user(i.user.id, f"{i.user.name} {i.user.display_name}"); data=load_u(); s=str(i.user.id); await i.response.send_message(f"{data[s]['coins']} coins | Bot {data[s]['wins_bot']} Amigo {data[s]['wins_amigo']} | Tableros: {len(data[s]['owned'])} Exp: {len(data[s].get('owned_exp',[]))}")
@tree.command(name="codigos",description="Canjear codigo")
async def codigos(i:discord.Interaction, codigo: str):
    await i.response.defer(ephemeral=True); ensure_user(i.user.id, f"{i.user.name} {i.user.display_name}"); data=load_u(); s=str(i.user.id); code_upper=codigo.strip().upper(); found=None
    for k in CODIGOS:
        if k.upper()==code_upper: found=k; break
    if not found: await i.followup.send("Codigo invalido", ephemeral=True); return
    if found in data[s]["codigos"]: await i.followup.send("Ya canjeado", ephemeral=True); return
    if isinstance(CODIGOS[found], str):
        board=CODIGOS[found]
        if board not in data[s]["owned"]: data[s]["owned"].append(board)
        data[s]["equipado"]=board; data[s]["codigos"].append(found); save_u(data); await i.followup.send(f"Canjeado! Tablero {board.upper()}!", ephemeral=True); return
    if found=="SPRITE":
        if "espiritus" not in data[s]["owned"]: data[s]["owned"].append("espiritus")
        data[s]["equipado"]="espiritus"; data[s]["codigos"].append(found); save_u(data); await i.followup.send("Canjeado! Tablero ESPIRITUS!", ephemeral=True); return
    if found=="VICTORY ROYALE":
        if "fortnite" not in data[s]["owned"]: data[s]["owned"].append("fortnite")
        data[s]["equipado"]="fortnite"; data[s]["codigos"].append(found); save_u(data); await i.followup.send("Canjeado! Tablero FORTNITE!", ephemeral=True); return
    if found=="GAMER":
        if "gamer" not in data[s]["owned"]: data[s]["owned"].append("gamer")
        data[s]["equipado"]="gamer"; data[s]["codigos"].append(found); save_u(data); await i.followup.send("Canjeado! Tablero GAMER!", ephemeral=True); return
    if found in ["TRUCO!","1_ESPADA"]:
        data[s]["poderes"]["MAGO"]=data[s]["poderes"].get("MAGO",0)+1; data[s]["codigos"].append(found); save_u(data); await i.followup.send(f"+1 MAGO!", ephemeral=True); return
    data[s]["coins"]+=CODIGOS[found]; data[s]["codigos"].append(found); save_u(data); await i.followup.send(f"+{CODIGOS[found]} coins! Total: {data[s]['coins']}", ephemeral=True)
@tree.command(name="ayuda",description="Ayuda V9.3.1")
async def ayuda(i:discord.Interaction):
    await i.response.send_message(embed=discord.Embed(title="AYUDA V9.3.1 FIX",description="Restaura Bot Trio/Escuadron + Tienda Expresiones/Poderes + Flor Auto + Truco/Retruco/Vale4 + Envido/Real/Falta + Lote $3000",color=0x9b59b6))

@bot.event
async def on_ready():
    try:
        await tree.sync()
        for guild in bot.guilds:
            try:
                await tree.sync(guild=guild)
            except:
                pass
        print(f"V9.3.1 SYNC OK - URL FIJA ETERNA: {SAVE_URL} - {len(bot.guilds)} guilds")
    except Exception as e:
        print(f"Sync error ignorado: {e}")
    bot.loop.create_task(timeout_checker())

bot.run(os.getenv("DISCORD_TOKEN"))

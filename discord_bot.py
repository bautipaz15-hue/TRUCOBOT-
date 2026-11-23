import discord, random, os
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

def foto(n,p):
 if not os.path.exists("Cartas_reales"): return None
 for f in os.listdir("Cartas_reales"):
  if str(n) in f and p[0] in f.lower(): return os.path.join("Cartas_reales",f)
 return None

def tab(): 
 return "tableros/Tablero.jpg" if os.path.exists("tableros/Tablero.jpg") else None
def av():
 for x in ["bot_rojo.png","tableros/bot_rojo.png","bot_rojo.jpg"]:
  if os.path.exists(x): return x
 return None

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
  if vy>vb: txt=f"🏆 GANASTE con {self.carta[0]} de {self.carta[1]}"; d["pj"]+=1
  elif vb>vy: txt=f"😢 PERDISTE, gano bot con {cb[0]} de {cb[1]}"; d["pb"]+=1
  else: txt="🤝 Empate"
  fs=[]
  r1=foto(self.carta[0],self.carta[1]); r2=foto(cb[0],cb[1])
  if r1 and os.path.exists(r1): fs.append(discord.File(r1,filename="a.jpg"))
  if r2 and os.path.exists(r2): fs.append(discord.File(r2,filename="b.jpg"))
  fin=len(d["bot"])==0
  if fin:
   for c in self.view.children: c.disabled=True
   txt+=f"\n{'GANASTE' if d['pj']>d['pb'] else 'PERDISTE' if d['pb']>d['pj'] else 'EMPATE'} {d['pj']}-{d['pb']} -> /jugar"
   partidas.pop(self.owner,None)
  await i.response.edit_message(view=self.view)
  await i.followup.send(f"Vos {self.carta[0]} de {self.carta[1]} vs Bot {cb[0]} de {cb[1]}\n{txt}",files=fs if fs else None)

class T(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="TRUCO",style=discord.ButtonStyle.danger,row=1)
 async def callback(self,i):
  if i.user.id!=self.o: return
  await i.response.send_message(f"{i.user.mention} canto TRUCO!")
class E(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="ENVIDO",style=discord.ButtonStyle.success,row=1)
 async def callback(self,i):
  if i.user.id!=self.o: return
  await i.response.send_message(f"{i.user.mention} canto ENVIDO!")
class S(discord.ui.Button):
 def __init__(self,o): self.o=o; super().__init__(label="SALIR",style=discord.ButtonStyle.secondary,row=1)
 async def callback(self,i):
  if i.user.id!=self.o: return
  partidas.pop(self.o,None)
  for c in self.view.children: c.disabled=True
  await i.response.edit_message(content="Saliste",view=self.view)

class V(discord.ui.View):
 def __init__(self,o,m):
  super().__init__(timeout=600)
  for c in m: self.add_item(C(c,o))
  self.add_item(T(o)); self.add_item(E(o)); self.add_item(S(o))

@tree.command(name="jugar",description="Jugar")
async def jugar(i:discord.Interaction):
 m=[(n,p) for p in PALOS for n in NUMS]; random.shuffle(m)
 mj=[m.pop() for _ in range(3)]; mb=[m.pop() for _ in range(3)]
 partidas[i.user.id]={"bot":mb,"pj":0,"pb":0}
 t=tab(); a=av()
 emb=discord.Embed(title="TRUCO",description=f"Bot vs {i.user.mention}",color=0x1e8449)
 fs=[]
 if t: fs.append(discord.File(t,filename="t.jpg")); emb.set_image(url="attachment://t.jpg")
 if a: fs.append(discord.File(a,filename="b.jpg")); emb.set_thumbnail(url="attachment://b.jpg")
 await i.response.send_message(embed=emb,view=V(i.user.id,mj),files=fs if fs else None)

@tree.command(name="ayuda",description="Ayuda")
async def ayuda(i):
 e=discord.Embed(title="AYUDA",description="/jugar -> vs bot con tablero default y bot_rojo\nBotones: 3 cartas + TRUCO + ENVIDO + SALIR\nAl tirar te dice quien gana y muestra fotos\nAl terminar se bloquea todo",color=0x9b59b6)
 await i.response.send_message(embed=e)

@bot.event
async def on_ready():
 await tree.sync()
 print("listo")

bot.run(os.getenv("DISCORD_TOKEN"))

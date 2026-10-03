import threading,tkinter as tk,time
from tkinter import ttk,messagebox
from .agent import Agent
from .config import load_config
from .oauth import OAuth
from .pressure import calculate_pressure,reset_cycle
from .store import Store

class App:
    def __init__(self,root):
        self.root=root;root.title("TimePressure — AI Agent");root.geometry("780x540");self.config=load_config();self.store=Store(self.config.data_dir);self.state=self.store.init(self.config.target_cents,self.config.cycle_ms);self.oauth=OAuth();self.running=False
        s=ttk.Style();s.configure("Title.TLabel",font=("TkDefaultFont",22,"bold"));s.configure("Status.TLabel",font=("TkDefaultFont",32,"bold"))
        f=ttk.Frame(root,padding=24);f.pack(fill="both",expand=True);ttk.Label(f,text="TimePressure",style="Title.TLabel").pack(anchor="w");ttk.Label(f,text="Autonomous AI agent • OpenAI / ChatGPT").pack(anchor="w",pady=(0,18));self.status=ttk.Label(f,style="Status.TLabel");self.status.pack(anchor="w");self.info=ttk.Label(f);self.info.pack(anchor="w",pady=(0,18))
        r=ttk.Frame(f);r.pack(fill="x");self.login=ttk.Button(r,text="Continuar com ChatGPT",command=self.login_chatgpt);self.login.pack(side="left");self.start=ttk.Button(r,text="Iniciar IA",command=self.toggle);self.start.pack(side="left",padx=8);ttk.Button(r,text="Resetar",command=self.reset).pack(side="left")
        ttk.Label(f,text="Log da IA").pack(anchor="w",pady=(20,5));self.log=tk.Text(f,height=14,state="disabled",wrap="word");self.log.pack(fill="both",expand=True);self.refresh()
    def add(self,t):self.log.configure(state="normal");self.log.insert("end",t+"\n");self.log.see("end");self.log.configure(state="disabled")
    def login_chatgpt(self):
        self.login.configure(state="disabled")
        def w():
            try:self.oauth.login();self.root.after(0,lambda:self.add("✓ ChatGPT conectado. OAuth pronto para a IA."))
            except Exception as e:self.root.after(0,lambda:messagebox.showerror("OAuth",str(e)))
            finally:self.root.after(0,lambda:self.login.configure(state="normal"));self.root.after(0,self.refresh)
        threading.Thread(target=w,daemon=True).start()
    def toggle(self):
        if self.running:self.running=False;self.start.configure(text="Iniciar IA");return
        if not self.oauth.connected() and not self.config.api_key:messagebox.showwarning("ChatGPT","Conecte sua conta do ChatGPT primeiro.");return
        self.running=True;self.start.configure(text="Parar IA");threading.Thread(target=self.loop,daemon=True).start()
    def loop(self):
        a=Agent(self.config,self.store,self.state)
        while self.running and self.state.pressure.status!="dead":
            a.tick();self.root.after(0,self.refresh);thought=self.state.last_thought or "IA executou um ciclo.";self.root.after(0,lambda x=thought:self.add(x));time.sleep(self.config.tick_ms/1000)
        self.running=False;self.root.after(0,lambda:self.start.configure(text="Iniciar IA"))
    def reset(self):self.state.pressure=reset_cycle(self.state.pressure,time.time(),self.config.cycle_ms);self.store.save(self.state);self.refresh()
    def refresh(self):
        self.state.pressure=calculate_pressure(time.time(),self.state.pressure);p=self.state.pressure;connected=self.oauth.connected();self.status.configure(text=p.status.upper());self.info.configure(text=f"Pressão {p.pressure:.1f}% • Receita USD {p.cycle_revenue_cents/100:.2f}/{p.target_cents/100:.2f} • {max(0,int(p.deadline-time.time()))}s • ChatGPT: {'conectado' if connected else 'não conectado'}")

def launch():
    root=tk.Tk();App(root);root.mainloop()

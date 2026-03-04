import tkinter as tk
from tkinter import messagebox
import json, os
from datetime import datetime, timedelta

# DARK GLASS PALETTE 
BG        = "#050508"   # near-void black
GLASS     = "#0c0e16"   # card glass surface
GLASS2    = "#0f1420"   # slightly lighter glass
GLASS_HVR = "#141929"   # hover state
DONE_GL   = "#080f0d"   # done card glass
DONE_HVR  = "#0c1a17"   # done hover

CYAN      = "#00d4ff"   # electric cyan — primary glow
CYAN_DIM  = "#0099bb"   # dimmer cyan
CYAN_GLOW = "#00aacc"
BLUE      = "#1a6aff"   # royal blue accent
BLUE_HV   = "#3a8aff"
GREEN     = "#00e5a0"   # neon mint green
GREEN_DIM = "#00a070"
AMBER     = "#ffb020"   # warm amber
RED       = "#ff3a5c"   # hot red

TEXT      = "#e8f4ff"   # icy white
TEXT2     = "#6a8aaa"   # muted blue-white
DIM       = "#1e2d3d"   # very dim
BORDER    = "#0f2035"   # subtle border
BORDER_LT = "#1a3050"   # lighter border

FONT      = "Helvetica"
FONT_MONO = "Courier"
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")


# ROUNDED RECTANGLE HELPER 
def rrect(canvas, x1, y1, x2, y2, r, **kw):
    r = min(r, (x2-x1)//2, (y2-y1)//2)
    pts = [
        x1+r, y1,  x2-r, y1,
        x2,   y1,  x2,   y1+r,
        x2,   y2-r,x2,   y2,
        x2-r, y2,  x1+r, y2,
        x1,   y2,  x1,   y2-r,
        x1,   y1+r,x1,   y1,
        x1+r, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


# ROUNDED CARD WIDGET 
class RCard(tk.Canvas):
    """A canvas that draws a rounded-rect background and hosts child widgets."""
    def __init__(self, parent, fill=GLASS, border=BORDER_LT, radius=10, pad=12, **kw):
        super().__init__(parent, bg=BG, highlightthickness=0, bd=0, **kw)
        self._fill   = fill
        self._border = border
        self._r      = radius
        self._pad    = pad
        self._frame  = tk.Frame(self, bg=fill)
        self.bind("<Configure>", self._redraw)

    def inner(self):
        return self._frame

    def _redraw(self, e=None):
        self.delete("bg")
        w = self.winfo_width()  or int(self.cget("width"))
        h = self.winfo_height() or int(self.cget("height"))
        rrect(self, 1, 1, w-1, h-1, self._r+1, fill=self._border, outline="", tags="bg")
        rrect(self, 2, 2, w-2, h-2, self._r,   fill=self._fill,   outline="", tags="bg")
        self._frame.place(x=self._pad, y=8, width=w-self._pad*2, height=h-16)

    def set_fill(self, color):
        self._fill = color
        self._frame.config(bg=color)
        for w in self._frame.winfo_children():
            try: w.config(bg=color)
            except: pass
        self._redraw()


# PILL BUTTON
class PillBtn(tk.Canvas):
    def __init__(self, parent, text, bg, fg, hover, cmd, font_size=9, bold=True, px=14, py=6):
        super().__init__(parent, bg=BG, highlightthickness=0, bd=0,
                         cursor="hand2")
        self._text  = text
        self._bg    = bg
        self._fg    = fg
        self._hov   = hover
        self._cmd   = cmd
        self._fsize = font_size
        self._bold  = bold
        self._px    = px
        self._py    = py
        self._hot   = False
        self._measure()
        self.bind("<Configure>",      self._draw)
        self.bind("<ButtonRelease-1>", lambda e: self._cmd())
        self.bind("<Enter>",  self._enter)
        self.bind("<Leave>",  self._leave)

    def _measure(self):
        tmp = tk.Label(text=self._text,
                       font=(FONT, self._fsize, "bold" if self._bold else "normal"))
        tmp.update_idletasks()
        tw = tmp.winfo_reqwidth()
        th = tmp.winfo_reqheight()
        tmp.destroy()
        self.config(width=tw + self._px*2, height=th + self._py*2)

    def _draw(self, e=None):
        self.delete("all")
        w = self.winfo_width()  or int(self.cget("width"))
        h = self.winfo_height() or int(self.cget("height"))
        fill = self._hov if self._hot else self._bg
        rrect(self, 0, 0, w, h, h//2, fill=fill, outline="")
        self.create_text(w//2, h//2, text=self._text, fill=self._fg,
                         font=(FONT, self._fsize, "bold" if self._bold else "normal"))

    def _enter(self, e): self._hot = True;  self._draw()
    def _leave(self, e): self._hot = False; self._draw()


# DRUM ROLLER
class DrumRoller(tk.Frame):
    ITEM_H  = 46
    VISIBLE = 5

    def __init__(self, parent, items, width=110):
        super().__init__(parent, bg=GLASS2,
                         highlightthickness=1, highlightbackground=BORDER_LT)
        self.items = items
        self._idx  = 0; self._off = 0.0
        self._vy   = 0.0; self._prev = None; self._anim = None
        self._W = width; self._H = self.ITEM_H * self.VISIBLE
        self.canvas = tk.Canvas(self, width=self._W, height=self._H,
                                bg=GLASS2, highlightthickness=0, bd=0)
        self.canvas.pack()
        for ev, fn in [("<ButtonPress-1>",self._press),("<B1-Motion>",self._drag),
                       ("<ButtonRelease-1>",self._release),("<MouseWheel>",self._wheel)]:
            self.canvas.bind(ev, fn)
        self._draw()

    def get(self): return self.items[self._idx % len(self.items)]
    def set(self, v):
        try:    self._idx = self.items.index(v)
        except: self._idx = 0
        self._off = 0.0; self._draw()

    def _draw(self):
        c = self.canvas; c.delete("all")
        n, mid = len(self.items), self.VISIBLE//2
        by = mid * self.ITEM_H
        # selection band glowing blue tint
        rrect(c, 4, by+2, self._W-4, by+self.ITEM_H-2, 6,
              fill="#0a2040", outline="")
        c.create_line(8, by+2,           self._W-8, by+2,           fill=CYAN_DIM, width=1)
        c.create_line(8, by+self.ITEM_H-2, self._W-8, by+self.ITEM_H-2, fill=CYAN_DIM, width=1)
        for row in range(self.VISIBLE):
            ii   = (self._idx - mid + row) % n
            yc   = row*self.ITEM_H + self._off + self.ITEM_H/2
            dist = abs(row - mid)
            if   dist == 0: col, sz, wt = CYAN,    22, "bold"
            elif dist == 1: col, sz, wt = TEXT2,   14, "normal"
            else:           col, sz, wt = DIM,     10, "normal"
            c.create_text(self._W//2, yc, text=self.items[ii],
                          fill=col, font=(FONT, sz, wt))
        # fade overlays
        fh = self.ITEM_H * 1.5
        c.create_rectangle(0, 0,          self._W, fh,       fill=GLASS2, stipple="gray50", outline="")
        c.create_rectangle(0, self._H-fh, self._W, self._H,  fill=GLASS2, stipple="gray50", outline="")

    def _press(self, e): self._cancel(); self._prev = e.y; self._vy = 0.0
    def _drag(self, e):
        if self._prev is None: return
        dy = e.y-self._prev; self._vy = dy; self._prev = e.y; self._apply(dy)
    def _release(self, e): self._prev = None; self._fling()
    def _wheel(self, e):
        self._cancel()
        self._idx = (self._idx+(-1 if e.delta>0 else 1)) % len(self.items)
        self._off = 0.0; self._draw()
    def _apply(self, dy):
        self._off += dy; n = len(self.items)
        while self._off >  self.ITEM_H/2: self._off -= self.ITEM_H; self._idx=(self._idx-1)%n
        while self._off < -self.ITEM_H/2: self._off += self.ITEM_H; self._idx=(self._idx+1)%n
        self._draw()
    def _fling(self):
        if abs(self._vy)<0.5: self._snap(); return
        self._vy *= 0.80; self._apply(self._vy); self._anim = self.after(16, self._fling)
    def _snap(self):
        if abs(self._off)<0.8: self._off=0.0; self._draw(); return
        self._off *= 0.65; self._draw(); self._anim = self.after(16, self._snap)
    def _cancel(self):
        if self._anim: self.after_cancel(self._anim); self._anim = None


# TIME PICKER hereeeeeeeeeeeeeeeeeeee ITS SUPER ASS
class TimePicker(tk.Toplevel):
    def __init__(self, parent, callback, current=""):
        super().__init__(parent)
        self.title("Schedule")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.callback = callback
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()  // 2 - 205
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - 285
        self.geometry(f"410x580+{px}+{py}")
        self.update()
        self.grab_set()

        # Glow line at top
        tk.Frame(self, bg=CYAN, height=2).pack(fill="x")

        tk.Label(self, text="SCHEDULE TASK", font=(FONT, 13, "bold"),
                 bg=BG, fg=CYAN).pack(pady=(18, 2))
        tk.Label(self, text="tap days  ·  drag or scroll the rollers",
                 font=(FONT, 8), bg=BG, fg=TEXT2).pack(pady=(0, 14))

        today  = datetime.now().date()
        monday = today - timedelta(days=today.weekday())
        self._dates    = [monday + timedelta(days=i) for i in range(7)]
        self._sel_days = {today.strftime("%Y-%m-%d")}

        # Day pill strip
        strip = tk.Frame(self, bg=BG)
        strip.pack(fill="x", padx=14, pady=(0, 4))
        self._dbtns = []
        for col, d in enumerate(self._dates):
            ds       = d.strftime("%Y-%m-%d")
            name     = d.strftime("%A")[:3].upper()
            is_today = (d == today)
            lbl      = f"{name}\n★" if is_today else name
            btn = tk.Button(strip, text=lbl,
                            font=(FONT, 7, "bold"),
                            bg=BG, fg=TEXT2, bd=0,
                            padx=3, pady=5, cursor="hand2", relief="flat",
                            activebackground=BG,
                            command=lambda ds=ds: self._toggle_day(ds))
            btn.grid(row=0, column=col, padx=2, sticky="ew")
            strip.columnconfigure(col, weight=1)
            self._dbtns.append((btn, d))

        self._sel_lbl = tk.Label(self, text="", font=(FONT, 8),
                                  bg=BG, fg=GREEN)
        self._sel_lbl.pack(pady=(4, 10))
        self._refresh_strip()

        # Rollers
        rw = tk.Frame(self, bg=BG); rw.pack(pady=2)
        tk.Label(rw, text="HOUR", font=(FONT_MONO, 7), bg=BG,
                 fg=TEXT2, width=11).grid(row=0, column=0)
        tk.Label(rw, text="",     bg=BG, width=4).grid(row=0, column=1)
        tk.Label(rw, text="MIN",  font=(FONT_MONO, 7), bg=BG,
                 fg=TEXT2, width=11).grid(row=0, column=2)
        hours   = [f"{h:02d}" for h in range(24)]
        minutes = [f"{m:02d}" for m in range(60)]
        self.hr = DrumRoller(rw, hours,   width=115); self.hr.grid(row=1, column=0, padx=6)
        tk.Label(rw, text=":", font=(FONT, 30, "bold"),
                 bg=BG, fg=CYAN).grid(row=1, column=1)
        self.mn = DrumRoller(rw, minutes, width=115); self.mn.grid(row=1, column=2, padx=6)

        if current:
            try:
                dt = datetime.strptime(current, "%Y-%m-%d %H:%M")
                ds = dt.strftime("%Y-%m-%d")
                self._sel_days = {ds}; self._refresh_strip()
                self.hr.set(dt.strftime("%H")); self.mn.set(dt.strftime("%M"))
            except: pass

        # Pill buttons
        br = tk.Frame(self, bg=BG); br.pack(pady=22)
        PillBtn(br, "Set Time", GREEN,    BG,      GREEN_DIM, self._confirm,
                font_size=10, px=20, py=9).pack(side="left", padx=6)
        PillBtn(br, "Skip",     AMBER,    BG,      "#c47a00", self.destroy,
                font_size=10, px=20, py=9).pack(side="left", padx=6)
        PillBtn(br, "Clear",    "#cc2244", BG,     RED,       self._clear,
                font_size=10, px=20, py=9).pack(side="left", padx=6)

        # Glow line at bottom
        tk.Frame(self, bg=CYAN_DIM, height=1).pack(fill="x", side="bottom")

    def _toggle_day(self, ds):
        if ds in self._sel_days:
            if len(self._sel_days) > 1: self._sel_days.discard(ds)
        else: self._sel_days.add(ds)
        self._refresh_strip()

    def _refresh_strip(self):
        today = datetime.now().date()
        for btn, d in self._dbtns:
            ds       = d.strftime("%Y-%m-%d")
            is_today = (d == today)
            is_sel   = ds in self._sel_days
            btn.config(
                bg     = CYAN    if is_sel else "#0a1a2a" if is_today else GLASS2,
                fg     = BG      if is_sel else CYAN      if is_today else TEXT2,
                relief = "flat",
                font   = (FONT, 7, "bold"),
            )
        count = len(self._sel_days)
        if count == 1:
            ds = next(iter(self._sel_days))
            try:
                d = datetime.strptime(ds, "%Y-%m-%d").date()
                lbl = "Today" if d == datetime.now().date() else d.strftime("%A")
            except: lbl = ds
            self._sel_lbl.config(text=f"✓  {lbl}")
        else:
            self._sel_lbl.config(text=f"✓  {count} days selected — repeated on each")

    def _confirm(self):
        t = f"{self.hr.get()}:{self.mn.get()}"
        for ds in sorted(self._sel_days): self.callback(f"{ds} {t}")
        self.destroy()

    def _clear(self): self.callback(None); self.destroy()


# MAIN APP 
class ToDoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Taskify")
        self.root.geometry("580x860")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.tasks      = []
        self._show_done = False
        self._sel_day   = datetime.now().strftime("%Y-%m-%d")
        self._load(); self._build_ui(); self._render_tasks(); self._tick()

    def _load(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE) as f: self.tasks = json.load(f)
            except: self.tasks = []

    def _save(self):
        with open(SAVE_FILE, "w") as f: json.dump(self.tasks, f, indent=2)

    def _tick(self): self._render_tasks(); self.root.after(30000, self._tick)

    def _build_ui(self):
        # Top glow accent bar
        tk.Frame(self.root, bg=CYAN, height=2).pack(fill="x")

        # Header
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x", padx=30, pady=(22, 0))
        left = tk.Frame(hdr, bg=BG); left.pack(side="left")
        tk.Label(left, text="TASKIFY", font=(FONT, 22, "bold"),
                 bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(left, text="create tasks · stay on track", font=(FONT, 8),
                 bg=BG, fg=CYAN_DIM).pack(anchor="w", pady=(1,0))
        self.cnt = tk.Label(left, text="", font=(FONT, 10),
                             bg=BG, fg=TEXT2)
        self.cnt.pack(anchor="w", pady=(3,0))
        self.clk = tk.Label(hdr, text="", font=(FONT_MONO, 8),
                             bg=BG, fg=TEXT2)
        self.clk.pack(side="right", anchor="ne", pady=(4,0))
        self._upd_clk()

        # Hairline divider with cyan tint
        div = tk.Canvas(self.root, height=1, bg=BG,
                        highlightthickness=0, bd=0)
        div.pack(fill="x", padx=30, pady=(12, 18))
        div.bind("<Configure>", lambda e: (
            div.delete("all"),
            div.create_line(0, 0, e.width, 0, fill=BORDER_LT, width=1)
        ))

        # Entry glowing when focused
        ew = tk.Frame(self.root, bg=GLASS,
                      highlightthickness=1, highlightbackground=BORDER_LT)
        ew.pack(fill="x", padx=30, pady=(0, 6))
        self.entry = tk.Entry(ew, bg=GLASS, fg=TEXT, insertbackground=CYAN,
                              font=(FONT, 12), bd=0,
                              highlightthickness=0, relief="flat")
        self.entry.pack(side="left", fill="x", expand=True, padx=16, pady=14)
        self.entry.bind("<Return>",    lambda e: self._add())
        self.entry.bind("<FocusIn>",   lambda e: ew.config(highlightbackground=CYAN_DIM))
        self.entry.bind("<FocusOut>",  lambda e: ew.config(highlightbackground=BORDER_LT))
        self._ph("Add a new task...")

        # Pill add button
        add_c = tk.Canvas(ew, width=46, height=36, bg=GLASS,
                          highlightthickness=0, bd=0, cursor="hand2")
        add_c.pack(side="right", padx=8, pady=8)
        add_c.bind("<Configure>", lambda e: self._draw_add_btn(add_c, False))
        add_c.bind("<Enter>",     lambda e: self._draw_add_btn(add_c, True))
        add_c.bind("<Leave>",     lambda e: self._draw_add_btn(add_c, False))
        add_c.bind("<ButtonRelease-1>", lambda e: self._add())
        self._add_canvas = add_c

        tk.Label(self.root,
                 text="  ↵ enter to add  ·  time picker opens automatically",
                 font=(FONT, 8), bg=BG, fg=TEXT2).pack(anchor="w", padx=30, pady=(0, 14))

        # Day filter strip
        self._strip_frame = tk.Frame(self.root, bg=BG)
        self._strip_frame.pack(fill="x", padx=30, pady=(0, 16))
        self._build_day_strip()

        # Scrollable task list
        cf = tk.Frame(self.root, bg=BG)
        cf.pack(fill="both", expand=True, padx=30)
        self.canvas = tk.Canvas(cf, bg=BG, bd=0,
                                highlightthickness=0, yscrollincrement=1)
        sb = tk.Scrollbar(cf, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.tf = tk.Frame(self.canvas, bg=BG)
        self.tw = self.canvas.create_window((0,0), window=self.tf, anchor="nw")
        self.tf.bind("<Configure>",
                     lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(self.tw, width=e.width))
        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(-1*(e.delta//120), "units"))

        # Footer
        ft = tk.Frame(self.root, bg=BG)
        ft.pack(fill="x", padx=30, pady=(6, 20))
        clr = tk.Label(ft, text="Clear completed", font=(FONT, 8),
                       bg=BG, fg=TEXT2, cursor="hand2")
        clr.pack(side="right")
        clr.bind("<Enter>",  lambda e: clr.config(fg=RED))
        clr.bind("<Leave>",  lambda e: clr.config(fg=TEXT2))
        clr.bind("<Button-1>", lambda e: self._clr_done())

        # Bottom glow bar
        tk.Frame(self.root, bg=BLUE, height=1).pack(fill="x", side="bottom")

    def _draw_add_btn(self, c, hot):
        c.delete("all")
        w = c.winfo_width() or 46
        h = c.winfo_height() or 36
        fill = CYAN_GLOW if hot else CYAN
        rrect(c, 0, 0, w, h, h//2, fill=fill, outline="")
        c.create_text(w//2, h//2, text="+", fill=BG,
                      font=(FONT, 16, "bold"))

    def _build_day_strip(self):
        for w in self._strip_frame.winfo_children(): w.destroy()
        today  = datetime.now().date()
        monday = today - timedelta(days=today.weekday())
        for i in range(7):
            d        = monday + timedelta(days=i)
            ds       = d.strftime("%Y-%m-%d")
            name     = d.strftime("%A")[:3].upper()
            is_today = (d == today)
            is_sel   = (self._sel_day == ds)
            label    = f"{name}\n★" if is_today else name
            bg   = CYAN   if is_sel else "#0a1a2a" if is_today else GLASS2
            fg   = BG     if is_sel else CYAN      if is_today else TEXT2
            btn = tk.Button(
                self._strip_frame, text=label,
                font=(FONT, 7, "bold"),
                bg=bg, fg=fg, bd=0, padx=0, pady=7,
                cursor="hand2", relief="flat", width=6,
                activebackground=bg, activeforeground=fg,
                command=lambda ds=ds: self._filter_day(ds)
            )
            btn.pack(side="left", padx=2)
        is_all = self._sel_day is None
        allbtn = tk.Button(
            self._strip_frame, text="ALL",
            font=(FONT, 7, "bold"),
            bg=BLUE if is_all else GLASS2,
            fg=TEXT if is_all else TEXT2,
            bd=0, padx=10, pady=7, cursor="hand2", relief="flat",
            activebackground=BLUE, activeforeground=TEXT,
            command=lambda: self._filter_day(None)
        )
        allbtn.pack(side="left", padx=2)

    def _filter_day(self, ds):
        self._sel_day = ds; self._build_day_strip(); self._render_tasks()

    def _upd_clk(self):
        self.clk.config(text=datetime.now().strftime("%a %d %b  %H:%M"))
        self.root.after(1000, self._upd_clk)

    def _ph(self, text):
        self.entry.config(fg=TEXT2); self.entry.insert(0, text)
        def fi(e):
            if self.entry.get() == text:
                self.entry.delete(0,"end"); self.entry.config(fg=TEXT)
        def fo(e):
            if not self.entry.get():
                self.entry.insert(0,text); self.entry.config(fg=TEXT2)
        self.entry.bind("<FocusIn>",fi); self.entry.bind("<FocusOut>",fo)

    def _add(self):
        text = self.entry.get().strip()
        if not text or text == "Add a new task...": return
        self.entry.delete(0,"end")
        self.root.after(80, lambda: self._pick_time_then_add(text))

    def _pick_time_then_add(self, text):
        added = []; skipped = []
        def cb(due_val):
            task_day  = due_val[:10] if due_val else datetime.now().strftime("%Y-%m-%d")
            today_str = datetime.now().strftime("%Y-%m-%d")
            for t in self.tasks:
                if t["text"].lower() != text.lower(): continue
                t_due = t.get("due")
                t_day = t_due[:10] if t_due else t.get("created","")[:10]
                if t_day == task_day:
                    try:
                        d = datetime.strptime(task_day,"%Y-%m-%d").date()
                        skipped.append("Today" if task_day==today_str else d.strftime("%A"))
                    except: skipped.append(task_day)
                    return
            self.tasks.append({"text":text,"done":False,
                               "created":datetime.now().strftime("%Y-%m-%d %H:%M"),
                               "due":due_val})
            try:
                d = datetime.strptime(task_day,"%Y-%m-%d").date()
                added.append("Today" if task_day==today_str else d.strftime("%A"))
            except: added.append(task_day)

        def on_close():
            self._save(); self._render_tasks()
            if skipped:
                messagebox.showwarning("Already exists",
                    f'Skipped on: {", ".join(skipped)}\n' +
                    (f'Added to: {", ".join(added)}' if added else "Nothing added."))

        tp = TimePicker(self.root, cb)
        tp.protocol("WM_DELETE_WINDOW", lambda: (tp.destroy(), on_close()))
        orig = tp._confirm
        def patched(): orig(); on_close()
        tp._confirm = patched
        # PillBtn stores cmd as self._cmd  patch it directly
        for w in tp.winfo_children():
            try:
                for child in w.winfo_children():
                    if isinstance(child, PillBtn) and child._text == "Set Time":
                        child._cmd = patched
            except: pass

    def _undo_all(self):
        for t in self.tasks:
            if t["done"]:
                t["done"] = False
                t.pop("completed_at", None)
        self._save(); self._render_tasks()

    def _set_due(self, idx):
        cur = self.tasks[idx].get("due") or ""
        def cb(v): self.tasks[idx]["due"] = v; self._save(); self._render_tasks()
        TimePicker(self.root, cb, cur)

    def _mark_done(self, idx):
        self.tasks[idx]["done"] = True
        self.tasks[idx]["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._save(); self._render_tasks()

    def _unmark(self, idx):
        self.tasks[idx]["done"] = False
        self.tasks[idx].pop("completed_at", None)
        self._save(); self._render_tasks()

    def _del(self, idx): self.tasks.pop(idx); self._save(); self._render_tasks()
    def _clr_done(self):
        self.tasks = [t for t in self.tasks if not t["done"]]
        self._save(); self._render_tasks()
    def _toggle_done(self): self._show_done = not self._show_done; self._render_tasks()

    def _task_day(self, t):
        due = t.get("due")
        return due[:10] if due else t.get("created","")[:10]

    def _due_disp(self, s):
        if not s: return None, None, False
        try:
            due  = datetime.strptime(s, "%Y-%m-%d %H:%M")
            mins = (due - datetime.now()).total_seconds() / 60
            today_d = datetime.now().date()
            if mins < 0:
                return f"⚠  overdue · {due.strftime('%a %H:%M')}", RED, True
            elif mins < 60:
                return f"⏰  in {int(mins)}m  ({due.strftime('%H:%M')})", AMBER, False
            elif mins < 1440:
                return f"⏰  in {int(mins//60)}h  ({due.strftime('%H:%M')})", AMBER, False
            else:
                diff = int(mins//1440)
                if due.date() == today_d + timedelta(days=1): day = "Tomorrow"
                elif diff <= 6: day = due.strftime("%A")
                else:           day = due.strftime("%a %b %d")
                return f"⏰  {day}  {due.strftime('%H:%M')}", TEXT2, False
        except: return s, TEXT2, False

    def _render_tasks(self):
        for w in self.tf.winfo_children(): w.destroy()
        all_active = [(i,t) for i,t in enumerate(self.tasks) if not t["done"]]
        all_done   = [(i,t) for i,t in enumerate(self.tasks) if     t["done"]]
        active = [(i,t) for i,t in all_active
                  if self._sel_day is None or self._task_day(t) == self._sel_day]
        done   = [(i,t) for i,t in all_done
                  if self._sel_day is None or self._task_day(t) == self._sel_day]

        if self._sel_day:
            try:
                sel_dt  = datetime.strptime(self._sel_day, "%Y-%m-%d").date()
                dname   = "Today" if sel_dt == datetime.now().date() else sel_dt.strftime("%A")
                self.cnt.config(text=f"{len(active)} task{'s' if len(active)!=1 else ''}  ·  {dname}")
            except: self.cnt.config(text=f"{len(active)} tasks")
        else:
            self.cnt.config(text=f"{len(all_active)} active  ·  {len(all_done)} done")

        #  ACTIVE section header 
        if self._sel_day is None and all_done:
            # Show Undo All in the active header row when in All view
            row = tk.Frame(self.tf, bg="#041828",
                           highlightthickness=1, highlightbackground="#062035")
            row.pack(fill="x", pady=(0, 10))
            tk.Label(row, text="  ACTIVE", font=(FONT, 9, "bold"),
                     bg="#041828", fg=CYAN, padx=6, pady=8).pack(side="left")
            tk.Label(row, text=f" {len(active)} ", font=(FONT, 8, "bold"),
                     bg=CYAN, fg=BG, padx=5, pady=1).pack(side="right", padx=10, pady=8)
            undo_lbl = tk.Label(row, text="↩ Undo All", font=(FONT, 8, "bold"),
                                bg="#041828", fg=AMBER, cursor="hand2", padx=8)
            undo_lbl.pack(side="right", pady=8)
            undo_lbl.bind("<Enter>", lambda e: undo_lbl.config(fg=TEXT))
            undo_lbl.bind("<Leave>", lambda e: undo_lbl.config(fg=AMBER))
            undo_lbl.bind("<Button-1>", lambda e: self._undo_all())
        else:
            self._shdr("ACTIVE", len(active), CYAN, "#041828", "#062035")
        if active:
            for ri, t in active: self._acard(ri, t)
        else:
            tk.Label(self.tf, text="  Nothing here — add something above",
                     font=(FONT, 10), bg=BG, fg=TEXT2).pack(anchor="w", padx=10, pady=(6,10))

        # COMPLETED section 
        tk.Frame(self.tf, bg=BG, height=18).pack(fill="x")
        arrow = "▲" if self._show_done else "▼"
        tog = tk.Frame(self.tf, bg="#060e0a",
                       highlightthickness=1, highlightbackground="#0a2518",
                       cursor="hand2")
        tog.pack(fill="x")
        inner = tk.Frame(tog, bg="#060e0a", cursor="hand2")
        inner.pack(side="left")
        for w in [tog, inner]:
            w.bind("<Button-1>", lambda e: self._toggle_done())
        tk.Label(inner, text=f"  ✓  COMPLETED  {arrow}",
                 font=(FONT, 9, "bold"), bg="#060e0a", fg=GREEN,
                 padx=6, pady=9, cursor="hand2").pack(side="left")
        hint = "hide" if self._show_done else f"{len(done)} tasks"
        tk.Label(inner, text=hint, font=(FONT, 7), bg="#060e0a",
                 fg="#1a5a38", cursor="hand2").pack(side="left")
        tk.Label(tog, text=f" {len(done)} ", font=(FONT, 8, "bold"),
                 bg=GREEN, fg=BG, padx=5, pady=2).pack(side="right", padx=10, pady=8)

        def _te(e):
            for w in [tog,inner]+list(tog.winfo_children())+list(inner.winfo_children()):
                try: w.config(bg="#0a1f14")
                except: pass
        def _tl(e):
            for w in [tog,inner]+list(tog.winfo_children())+list(inner.winfo_children()):
                try: w.config(bg="#060e0a")
                except: pass
        for w in [tog, inner]: w.bind("<Enter>",_te); w.bind("<Leave>",_tl)

        if self._show_done:
            tk.Frame(self.tf, bg=BG, height=6).pack(fill="x")
            if done:
                for ri, t in done: self._dcard(ri, t)
            else:
                tk.Label(self.tf, text="  No completed tasks.",
                         font=(FONT, 10), bg=BG, fg=TEXT2).pack(anchor="w", padx=10, pady=4)

    def _shdr(self, title, count, fg, bg, border):
        row = tk.Frame(self.tf, bg=bg,
                       highlightthickness=1, highlightbackground=border)
        row.pack(fill="x", pady=(0, 10))
        tk.Label(row, text=f"  {title}", font=(FONT, 9, "bold"),
                 bg=bg, fg=fg, padx=6, pady=8).pack(side="left")
        tk.Label(row, text=f" {count} ", font=(FONT, 8, "bold"),
                 bg=fg, fg=BG, padx=5, pady=1).pack(side="right", padx=10, pady=8)

    def _day_badge(self, task):
        today = datetime.now().date()
        raw = task.get("due") or task.get("created","")
        try:
            d = datetime.strptime(raw[:10], "%Y-%m-%d").date()
            if d == today:  return "Today",          "#041828"
            elif d < today: return d.strftime("%A"), "#120808"
            else:           return d.strftime("%A"), "#040e1c"
        except: return "", ""

    def _acard(self, ri, task):
        dt, dc, ov = self._due_disp(task.get("due"))

        # Rounded card via Canvas
        card_c = tk.Canvas(self.tf, bg=BG, highlightthickness=0, bd=0, height=72)
        card_c.pack(fill="x", pady=4)
        card_c.bind("<Configure>", lambda e, c=card_c, o=ov: self._draw_card_bg(c, o))

        inner = tk.Frame(card_c, bg=GLASS_HVR if ov else GLASS)
        card_c.create_window(0, 0, window=inner, anchor="nw")

        # Left glow bar (drawn as a thin canvas strip)
        bar = tk.Frame(inner, bg=RED if ov else CYAN, width=3)
        bar.pack(side="left", fill="y")

        con = tk.Frame(inner, bg=GLASS_HVR if ov else GLASS)
        con.pack(side="left", fill="x", expand=True, padx=12, pady=10)

        # Title + day badge
        top = tk.Frame(con, bg=con["bg"]); top.pack(anchor="w", fill="x")
        tk.Label(top, text=task["text"], font=(FONT, 11, "bold"),
                 bg=con["bg"], fg=TEXT, anchor="w").pack(side="left")
        if self._sel_day is None:
            dname, dbg = self._day_badge(task)
            if dname:
                tl = tk.Label(top, text=f"  {dname}  ", font=(FONT, 7),
                              bg=dbg, fg=CYAN_DIM, padx=3, pady=1)
                tl.pack(side="left", padx=(10,0))

        # Meta row
        meta = tk.Frame(con, bg=con["bg"]); meta.pack(anchor="w", pady=(4,0))
        if dt:
            tk.Label(meta, text=dt, font=(FONT, 8, "bold"),
                     bg=con["bg"], fg=dc).pack(side="left", padx=(0,10))
        if task.get("created"):
            try:    cs = datetime.strptime(task["created"],"%Y-%m-%d %H:%M").strftime("added %b %d, %H:%M")
            except: cs = task["created"]
            tk.Label(meta, text=cs, font=(FONT, 7),
                     bg=con["bg"], fg=TEXT2).pack(side="left")

        # Action buttons
        bf = tk.Frame(inner, bg=inner["bg"]); bf.pack(side="right", padx=10, pady=10)

        # Clock icon
        clk = tk.Label(bf, text="⏰", font=(FONT, 10), bg=inner["bg"],
                       fg=AMBER if task.get("due") else DIM, cursor="hand2")
        clk.pack(side="left", padx=(0,8))
        clk.bind("<Button-1>", lambda e, i=ri: self._set_due(i))

        # Done pill
        PillBtn(bf, "Done", GREEN, BG, GREEN_DIM,
                lambda i=ri: self._mark_done(i),
                font_size=8, px=10, py=4).pack(side="left", padx=(0,6))

        # Delete x
        dlbl = tk.Label(bf, text="✕", font=(FONT, 9), bg=inner["bg"],
                        fg=TEXT2, cursor="hand2")
        dlbl.pack(side="left")
        dlbl.bind("<Button-1>",  lambda e, i=ri: self._del(i))
        dlbl.bind("<Enter>", lambda e: dlbl.config(fg=RED))
        dlbl.bind("<Leave>", lambda e: dlbl.config(fg=TEXT2))

        # Hover effect on whole card
        bg_n = GLASS_HVR if ov else GLASS
        bg_h = "#1a2535"
        self._hov_frame(card_c, inner, con, top, meta, bf,
                        extra_labels=[clk, dlbl], norm=bg_n, hov=bg_h)

        # Resize inner to fill canvas
        card_c.bind("<Configure>", lambda e, c=card_c, i=inner, o=ov:
                    (self._draw_card_bg(c, o),
                     i.place(x=0, y=0, width=e.width, height=e.height)))

    def _draw_card_bg(self, c, overdue=False):
        c.delete("cardbg")
        w = c.winfo_width(); h = c.winfo_height()
        if w < 4 or h < 4: return
        border_col = RED if overdue else BORDER_LT
        rrect(c, 0, 0, w,   h,   10, fill=border_col, outline="", tags="cardbg")
        rrect(c, 1, 1, w-1, h-1,  9, fill=GLASS_HVR if overdue else GLASS,
              outline="", tags="cardbg")

    def _dcard(self, ri, task):
        card_c = tk.Canvas(self.tf, bg=BG, highlightthickness=0, bd=0, height=64)
        card_c.pack(fill="x", pady=3)
        inner = tk.Frame(card_c, bg=DONE_GL)
        card_c.create_window(0, 0, window=inner, anchor="nw")
        tk.Frame(inner, bg=GREEN_DIM, width=3).pack(side="left", fill="y")
        con = tk.Frame(inner, bg=DONE_GL)
        con.pack(side="left", fill="x", expand=True, padx=12, pady=9)
        tk.Label(con, text=task["text"], font=(FONT, 11, "overstrike"),
                 bg=DONE_GL, fg=TEXT2, anchor="w").pack(anchor="w")
        meta = tk.Frame(con, bg=DONE_GL); meta.pack(anchor="w", pady=(3,0))
        if task.get("completed_at"):
            try:    cs = "✓ " + datetime.strptime(task["completed_at"],"%Y-%m-%d %H:%M").strftime("%b %d, %H:%M")
            except: cs = "✓ done"
            tk.Label(meta, text=cs, font=(FONT, 7, "bold"),
                     bg=DONE_GL, fg=GREEN_DIM).pack(side="left", padx=(0,8))
        if task.get("due"):
            try:    ds = "due " + datetime.strptime(task["due"],"%Y-%m-%d %H:%M").strftime("%b %d, %H:%M")
            except: ds = ""
            tk.Label(meta, text=ds, font=(FONT, 7),
                     bg=DONE_GL, fg=TEXT2).pack(side="left")
        bf = tk.Frame(inner, bg=DONE_GL); bf.pack(side="right", padx=10, pady=10)
        PillBtn(bf, "Undo", GLASS2, TEXT2, BORDER_LT,
                lambda i=ri: self._unmark(i),
                font_size=8, px=10, py=4).pack(side="left", padx=(0,6))
        dlbl = tk.Label(bf, text="✕", font=(FONT,9), bg=DONE_GL, fg=TEXT2, cursor="hand2")
        dlbl.pack(side="left")
        dlbl.bind("<Button-1>",  lambda e, i=ri: self._del(i))
        dlbl.bind("<Enter>", lambda e: dlbl.config(fg=RED))
        dlbl.bind("<Leave>", lambda e: dlbl.config(fg=TEXT2))
        card_c.bind("<Configure>", lambda e, c=card_c, i=inner:
                    (self._draw_done_bg(c),
                     i.place(x=0, y=0, width=e.width, height=e.height)))

    def _draw_done_bg(self, c):
        c.delete("cardbg")
        w = c.winfo_width(); h = c.winfo_height()
        if w < 4 or h < 4: return
        rrect(c, 0, 0, w,   h,   10, fill="#0a2518", outline="", tags="cardbg")
        rrect(c, 1, 1, w-1, h-1,  9, fill=DONE_GL,  outline="", tags="cardbg")

    def _hov_frame(self, canvas, *frames, extra_labels=None, norm, hov):
        all_w = list(frames) + (extra_labels or [])
        def enter(e):
            for f in frames:
                try: f.config(bg=hov)
                except: pass
                for c in f.winfo_children():
                    try: c.config(bg=hov)
                    except: pass
        def leave(e):
            for f in frames:
                try: f.config(bg=norm)
                except: pass
                for c in f.winfo_children():
                    try: c.config(bg=norm)
                    except: pass
        for w in [canvas] + list(frames):
            w.bind("<Enter>", enter); w.bind("<Leave>", leave)


if __name__ == "__main__":
    root = tk.Tk()
    ToDoApp(root)
    root.mainloop()

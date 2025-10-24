"""
customtkinter Mood Tracker — dashboard Home (weekly chart + calendar + tasks),
Log, Trends, Settings. Dynamic charts, interactive calendar.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timedelta, date
import calendar
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

import storage
import charts as charts  

APP_TITLE = "Haven"
APP_WIDTH, APP_HEIGHT = 1920, 1080
DATA_DIR = Path(__file__).parent / "data"
CSV_PATH = DATA_DIR / "moods.csv"

# --- Accent + neutrals (light, dark)
ACCENT = ("#7C5CFF", "#9b7bff") 
CARD_BG = ("#FFFFFF", "#151B2B")
APP_BG  = ("#F6F8FC", "#0F1422")
TEXT_MUTED = ("#64748b", "#9aa3b2")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(1080, 680)

        # Appearance + base theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=APP_BG)

        # Data
        storage.ensure_data_store(CSV_PATH)
        self.df: pd.DataFrame = storage.load_dataframe(CSV_PATH)

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = Sidebar(self, command=self._navigate)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        # Content stack
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Pages
        self.page_home = HomePage(
            self.container,
            get_df=lambda: self.df,
            get_mode=self._mode,
            on_add_task=self._home_add_task,
            on_toggle_task=self._home_toggle_task,
        )
        self.page_log = LogPage(self.container, on_save=self._save_entry)
        self.page_trends = TrendsPage(self.container, get_df=lambda: self._filtered_df(), get_mode=self._mode)
        self.page_settings = SettingsPage(self.container, on_theme=self._toggle_theme)

        for p in (self.page_home, self.page_log, self.page_trends, self.page_settings):
            p.grid(row=0, column=0, sticky="nsew")


        self.tasks: list[dict] = [
            {"text": "Plan today’s priorities", "done": False},
            {"text": "Take a short walk/breath break", "done": False},
            {"text": "Journal for 5 minutes", "done": False},
        ]
        self._navigate("Home")

    # ---------- Navigation ----------
    def _navigate(self, name: str):
        if name == "Home":
            self.page_home.refresh(self.df, self.tasks)
            self.page_home.tkraise()
        elif name == "Log":
            self.page_log.tkraise()
        elif name == "Trends":
            self.page_trends.refresh_chart()
            self.page_trends.tkraise()
        elif name == "Settings":
            self.page_settings.tkraise()

    # ---------- Data flows ----------
    def _save_entry(self, mood: int, note: str, tags: list[str]):
        if mood < 1 or mood > 5:
            messagebox.showerror("Invalid", "Please choose a mood between 1 and 5.")
            return
        storage.append_entry(CSV_PATH, mood=mood, note=note, tags=tags)
        self.df = storage.load_dataframe(CSV_PATH)
        self.page_log.clear_after_save()
        self._navigate("Home")

    def _filtered_df(self) -> pd.DataFrame:
        if self.df.empty:
            return self.df
        rng = self.page_trends.range_var.get()
        if rng == "All time":
            return self.df
        days = 7 if "7" in rng else 30
        cutoff = datetime.now() - timedelta(days=days)
        return self.df[self.df["timestamp"] >= cutoff]

    # ---------- Tasks model for Home ----------
    def _home_add_task(self, text: str):
        if text.strip():
            self.tasks.insert(0, {"text": text.strip(), "done": False})
            self.page_home.refresh(self.df, self.tasks)

    def _home_toggle_task(self, idx: int, val: bool):
        if 0 <= idx < len(self.tasks):
            self.tasks[idx]["done"] = val
            self.page_home.refresh(self.df, self.tasks)

    # ---------- Theme helpers ----------
    def _toggle_theme(self, mode: str):
        ctk.set_appearance_mode(mode)
        self.configure(fg_color=APP_BG)
        # Re-render charts and UI bits
        self.page_trends.refresh_chart()
        self.page_home.refresh(self.df, self.tasks)

    def _mode(self) -> str:
        return "dark" if ctk.get_appearance_mode().lower() == "dark" else "light"


# ---------- Sidebar ----------
class Sidebar(ctk.CTkFrame):
    def __init__(self, master, command):
        super().__init__(master, width=220, corner_radius=0, fg_color="transparent")
        self.command = command

        title = ctk.CTkLabel(self, text=APP_TITLE, font=ctk.CTkFont(size=22, weight="bold"))
        title.pack(padx=18, pady=(18, 8), anchor="w")

        ctk.CTkLabel(self, text="Navigate", text_color=TEXT_MUTED).pack(padx=18, anchor="w")

        for label in ("Home", "Log", "Trends", "Settings"):
            NavButton(self, text=label, command=lambda n=label: self.command(n)).pack(fill="x", padx=14, pady=6)

        self.pack_propagate(False)


class NavButton(ctk.CTkButton):
    def __init__(self, master, text, command):
        super().__init__(
            master,
            text=text,
            command=command,
            height=44,
            corner_radius=14,
            fg_color=("gray91", "#1D2437"),
            hover_color=("gray85", "#222A41"),
            text_color=("black", "white"),
        )


# ---------- Reusable Card ----------
class Card(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=16, **kwargs)
        self.configure(fg_color=CARD_BG)
        self.pad = ctk.CTkFrame(self, fg_color="transparent")
        self.pad.pack(fill="both", expand=True, padx=16, pady=16)


# ---------- HOME PAGE ----------
class HomePage(ctk.CTkFrame):
    def __init__(self, master, get_df, get_mode, on_add_task, on_toggle_task):
        super().__init__(master, fg_color="transparent")
        self.get_df = get_df
        self.get_mode = get_mode
        self.on_add_task = on_add_task
        self.on_toggle_task = on_toggle_task

        # Calendar state
        today = date.today()
        self.cal_year = today.year
        self.cal_month = today.month
        self.selected_date: date | None = None

        # Grid: 2 columns (main, right)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(2, weight=1)

        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        ctk.CTkLabel(header, text="Hi, there 👋", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", padx=(4, 10))
        self.search = ctk.CTkEntry(header, placeholder_text="Search entries…", width=280)
        self.search.pack(side="left")

        # MAIN COLUMN
        # Weekly Mood Tracker
        self.tracker_card = Card(self)
        self.tracker_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(10, 8))
        title_row = ctk.CTkFrame(self.tracker_card.pad, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(title_row, text="Weekly Mood Tracker", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        self.week_label = ctk.CTkLabel(title_row, text="", text_color=TEXT_MUTED)
        self.week_label.pack(side="right")

        self.week_canvas = None 

        # Recent Entries grid
        self.recent_card = Card(self)
        self.recent_card.grid(row=2, column=0, sticky="nsew", padx=(0, 10), pady=(8, 10))
        head = ctk.CTkFrame(self.recent_card.pad, fg_color="transparent")
        head.pack(fill="x")
        ctk.CTkLabel(head, text="Recent Entries", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        self.recent_grid = ctk.CTkFrame(self.recent_card.pad, fg_color="transparent")
        self.recent_grid.pack(fill="both", expand=True, pady=(6, 0))

        # RIGHT COLUMN
        # Calendar
        self.calendar_card = Card(self)
        self.calendar_card.grid(row=1, column=1, sticky="nsew", pady=(10, 8))
        cal_header = ctk.CTkFrame(self.calendar_card.pad, fg_color="transparent")
        cal_header.pack(fill="x")
        self.month_label = ctk.CTkLabel(cal_header, text="", font=ctk.CTkFont(size=16, weight="bold"))
        self.month_label.pack(side="left")
        ctk.CTkButton(cal_header, text="◀", width=32, command=self._prev_month).pack(side="right")
        ctk.CTkButton(cal_header, text="▶", width=32, command=self._next_month).pack(side="right")
        self.calendar_grid = ctk.CTkFrame(self.calendar_card.pad, fg_color="transparent")
        self.calendar_grid.pack(fill="x", pady=(6, 0))

        # Day entries panel
        self.day_card = Card(self)
        self.day_card.grid(row=2, column=1, sticky="nsew", pady=(8, 10))
        self.day_title = ctk.CTkLabel(self.day_card.pad, text="Entries for —", font=ctk.CTkFont(size=16, weight="bold"))
        self.day_title.pack(anchor="w")
        self.day_list = ctk.CTkScrollableFrame(self.day_card.pad, height=220, fg_color="transparent")
        self.day_list.pack(fill="both", expand=True, pady=(6, 0))

        # Tasks
        self.tasks_card = Card(self)
        self.tasks_card.grid_forget()
        self.progress = None

    # ---- calendar navigation ----
    def _prev_month(self):
        if self.cal_month == 1:
            self.cal_month = 12
            self.cal_year -= 1
        else:
            self.cal_month -= 1
        if self.selected_date and (self.selected_date.year != self.cal_year or self.selected_date.month != self.cal_month):
            self.selected_date = None
        self._build_calendar(self.get_df())

    def _next_month(self):
        if self.cal_month == 12:
            self.cal_month = 1
            self.cal_year += 1
        else:
            self.cal_month += 1
        if self.selected_date and (self.selected_date.year != self.cal_year or self.selected_date.month != self.cal_month):
            self.selected_date = None
        self._build_calendar(self.get_df())

    # ---- calendar builders ----
    def _build_calendar(self, df: pd.DataFrame):

        for w in self.calendar_grid.winfo_children():
            w.destroy()

        self.month_label.configure(text=f"{calendar.month_name[self.cal_month]} {self.cal_year}")


        headers = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.calendar_grid, text=h, text_color=TEXT_MUTED).grid(row=0, column=i, padx=6, pady=4)

        cal = calendar.Calendar(firstweekday=0).monthdatescalendar(self.cal_year, self.cal_month)


        entry_dates = set()
        if df is not None and not df.empty:
            d = df.copy()
            d["date"] = pd.to_datetime(d["timestamp"], errors="coerce").dt.date
            entry_dates = set(d.dropna(subset=["date"])["date"].tolist())


        for r, week in enumerate(cal, start=1):
            for c, day in enumerate(week):
                in_month = (day.month == self.cal_month)
                has_entries = day in entry_dates

                txt_color = ("#94a3b8", "#8a93a3") if not in_month else ("#0f172a", "#E6E9F2")
                btn_fg = (None if not has_entries else ACCENT)

                b = ctk.CTkButton(
                    self.calendar_grid,
                    text=str(day.day),
                    width=40, height=36,
                    corner_radius=10,
                    fg_color=btn_fg if has_entries else ("#e7eef9", "#1E2536"),
                    hover_color=("#dce6fa", "#222b42"),
                    text_color=txt_color,
                    command=lambda d=day: self._on_date_click(d),
                )
                b.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")

        for i in range(7):
            self.calendar_grid.grid_columnconfigure(i, weight=1)

    def _on_date_click(self, d: date):
        self.selected_date = d
        self.day_title.configure(text=f"Entries for {d:%b %d, %Y}")
        for w in self.day_list.winfo_children():
            w.destroy()

        df = self.get_df()
        if df is None or df.empty:
            ctk.CTkLabel(self.day_list, text="No entries.", text_color=TEXT_MUTED).pack(anchor="w", padx=6, pady=4)
            return

        dd = df.copy()
        dd["date"] = pd.to_datetime(dd["timestamp"], errors="coerce").dt.date
        dd = dd[dd["date"] == d].sort_values("timestamp", ascending=False)

        if dd.empty:
            ctk.CTkLabel(self.day_list, text="No entries.", text_color=TEXT_MUTED).pack(anchor="w", padx=6, pady=4)
            return

        for _, row in dd.iterrows():
            ts = pd.to_datetime(row["timestamp"], errors="coerce")
            ttxt = "Unknown" if pd.isna(ts) else ts.strftime("%I:%M %p").lstrip("0")
            mood = int(row.get("mood", 0)) if pd.notna(row.get("mood", None)) else 0
            note = (row.get("note") or "").strip() or "(no note)"
            line = f"[{ttxt}]  Mood {mood} — {note}"
            ctk.CTkLabel(self.day_list, text=line, wraplength=420, justify="left").pack(anchor="w", padx=6, pady=3)


    def refresh(self, df: pd.DataFrame, tasks: list[dict]):
        # Weekly chart
        mode = self.get_mode()
        week_start = (date.today() - timedelta(days=date.today().weekday()))
        week_end = week_start + timedelta(days=6)
        self.week_label.configure(text=f"{week_start:%b %d} – {week_end:%b %d}")
        fig = charts.weekly_mood_bar(df, mode=mode)


        new_canvas = None
        if fig is not None:
            new_canvas = FigureCanvasTkAgg(fig, master=self.tracker_card.pad)
            new_canvas.draw()
            new_canvas.get_tk_widget().pack(fill="both", expand=True, pady=(6, 0))

        old = self.week_canvas
        self.week_canvas = new_canvas
        if old is not None and old.get_tk_widget().winfo_exists():
            self.after(0, old.get_tk_widget().destroy)


        for w in self.recent_grid.winfo_children():
            w.destroy()

        if df is None or df.empty:
            recent = pd.DataFrame()
        else:
            recent = df.copy()
            recent["timestamp"] = pd.to_datetime(recent["timestamp"], errors="coerce")
            recent = recent.dropna(subset=["timestamp"]).sort_values("timestamp", ascending=False).head(4)

        if recent.empty:
            ctk.CTkLabel(self.recent_grid, text="No entries yet.", text_color=TEXT_MUTED).pack(anchor="w")
        else:
            cols = 2
            for i, row in recent.reset_index(drop=True).iterrows():
                card = ctk.CTkFrame(self.recent_grid, corner_radius=12, fg_color=CARD_BG)
                r, c = divmod(i, cols)
                card.grid(row=r, column=c, sticky="nsew", padx=6, pady=6)
                for col in range(cols):
                    self.recent_grid.grid_columnconfigure(col, weight=1)

                ts = pd.to_datetime(row["timestamp"], errors="coerce")
                ts_text = "Unknown time" if pd.isna(ts) else ts.strftime("%a  %I:%M %p").lstrip("0")

                header = ctk.CTkLabel(card, text=ts_text, text_color=TEXT_MUTED)
                header.pack(anchor="w", padx=12, pady=(10, 0))

                note = (row.get("note") or "").strip() or "(no note)"
                body = ctk.CTkLabel(card, text=note, wraplength=360, justify="left")
                body.pack(anchor="w", padx=12, pady=(6, 12))

        self._build_calendar(df)
        if self.selected_date:
            self._on_date_click(self.selected_date)


class LogPage(ctk.CTkFrame):
    def __init__(self, master, on_save):
        super().__init__(master, fg_color="transparent")
        self.on_save = on_save

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkLabel(self, text="Log your mood", font=ctk.CTkFont(size=20, weight="bold"))
        header.grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=(10, 0))

        left = Card(self)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=10)
        ctk.CTkLabel(left.pad, text="How are you feeling?", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(left.pad, text="Drag the slider: 1 (low) → 5 (great).", text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 8))

        self.mood_var = tk.DoubleVar(value=3.0)
        self.mood_int_var = tk.IntVar(value=3)
        self.slider = ctk.CTkSlider(
            left.pad, from_=1, to=5, number_of_steps=4,
            variable=self.mood_var, command=self._on_slider,
            progress_color=ACCENT, button_color=ACCENT
        )
        self.slider.pack(fill="x", pady=10)

        preview = ctk.CTkFrame(left.pad, fg_color="transparent")
        preview.pack(anchor="w", pady=4)
        self.emoji = ctk.CTkLabel(preview, text="😐", font=ctk.CTkFont(size=32))
        self.emoji.pack(side="left")
        self.value_lbl = ctk.CTkLabel(preview, text="3", font=ctk.CTkFont(size=18, weight="bold"))
        self.value_lbl.pack(side="left", padx=8)

        right = Card(self)
        right.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=10)
        ctk.CTkLabel(right.pad, text="Add a note (optional)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.note = ctk.CTkTextbox(right.pad, height=230)
        self.note.pack(fill="both", expand=True, pady=(8, 10))

        tag_bar = ctk.CTkFrame(right.pad, fg_color="transparent")
        tag_bar.pack(anchor="w", pady=(4, 0))
        ctk.CTkLabel(tag_bar, text="Tags:", text_color=TEXT_MUTED).pack(side="left", padx=(0, 8))
        self.tags = ["sleep", "study", "work", "family", "friends", "exercise"]
        self.tag_vars: dict[str, tk.BooleanVar] = {}
        for t in self.tags:
            var = tk.BooleanVar()
            self.tag_vars[t] = var
            cb = ctk.CTkCheckBox(tag_bar, text=t.capitalize(), variable=var, fg_color=ACCENT, border_color=ACCENT)
            cb.pack(side="left", padx=(0, 8))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))
        save_btn = ctk.CTkButton(
            actions, text="Save Entry", command=self._save, height=44, corner_radius=14, fg_color=ACCENT, hover_color=ACCENT
        )
        save_btn.pack(side="left", padx=(0, 10))
        self.status = ctk.CTkLabel(actions, text="")
        self.status.pack(side="left")

    def _on_slider(self, _=None):
        val = int(round(float(self.mood_var.get())))
        self.mood_int_var.set(val)
        emojis = {1: "😞", 2: "🙁", 3: "😐", 4: "🙂", 5: "😄"}
        self.emoji.configure(text=emojis.get(val, "😐"))
        self.value_lbl.configure(text=str(val))

    def _save(self):
        mood = self.mood_int_var.get()
        note = self.note.get("0.0", "end").strip()
        tags = [t for t, v in self.tag_vars.items() if v.get()]
        self.on_save(mood, note, tags)
        self.status.configure(text="Saved ✔")
        self.after(1500, lambda: self.status.configure(text=""))

    def clear_after_save(self):
        self.note.delete("0.0", "end")
        for v in self.tag_vars.values():
            v.set(False)


class TrendsPage(ctk.CTkFrame):
    def __init__(self, master, get_df, get_mode):
        super().__init__(master, fg_color="transparent")
        self.get_df = get_df
        self.get_mode = get_mode

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text="Trends", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", padx=(4, 10))
        self.range_var = tk.StringVar(value="Last 30 days")
        self.range_dd = ctk.CTkOptionMenu(
            top,
            variable=self.range_var,
            values=["Last 7 days", "Last 30 days", "All time"],
            command=lambda _: self.refresh_chart(),
            fg_color=ACCENT,
            button_color=ACCENT,
        )
        self.range_dd.pack(side="left", padx=(0, 10))
        self.stats = ctk.CTkLabel(top, text="", text_color=TEXT_MUTED)
        self.stats.pack(side="left")

        self.card = Card(self)
        self.card.pack(fill="both", expand=True, pady=(10, 0))
        self.canvas_widget = None

    def refresh_chart(self):
        df = self.get_df()
        avg = "— avg: n/a"
        if not df.empty:
            avg_val = df["mood"].mean()
            avg = f"— avg: {avg_val:.2f} from {len(df)} entries"
        self.stats.configure(text=avg)

        mode = self.get_mode()
        fig = charts.mood_line_chart(df, mode=mode)

        new_canvas = None
        if fig is not None:
            new_canvas = FigureCanvasTkAgg(fig, master=self.card.pad)
            new_canvas.draw()
            new_canvas.get_tk_widget().pack(fill="both", expand=True)

        old = self.canvas_widget
        self.canvas_widget = new_canvas
        if old is not None and old.get_tk_widget().winfo_exists():
            self.after(0, old.get_tk_widget().destroy)


class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, on_theme):
        super().__init__(master, fg_color="transparent")
        self.on_theme = on_theme
        card = Card(self)
        card.pack(fill="x", pady=10)
        ctk.CTkLabel(card.pad, text="Appearance", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(card.pad, text="Choose light or dark theme.", text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 6))
        row = ctk.CTkFrame(card.pad, fg_color="transparent")
        row.pack(anchor="w")
        ctk.CTkButton(row, text="Light", command=lambda: self.on_theme("light"),
                      corner_radius=12, height=36, fg_color=ACCENT, hover_color=ACCENT).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="Dark", command=lambda: self.on_theme("dark"),
                      corner_radius=12, height=36, fg_color=ACCENT, hover_color=ACCENT).pack(side="left")


if __name__ == "__main__":
    app = App()
    app.mainloop()

"""
theme.py — ttk theme helpers for a cleaner, modern look with light/dark modes
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk

PALETTES = {
    "dark": {
        "PRIMARY": "#5b8def",
        "BG": "#0f172a",     
        "SURFACE": "#111827",
        "TEXT": "#e5e7eb",   
        "MUTED": "#9ca3af",  
        "CARD": "#0b1220",
        "BORDER": "#1f2937",
    },
    "light": {
        "PRIMARY": "#3b82f6",
        "BG": "#f8fafc",  
        "SURFACE": "#ffffff",
        "TEXT": "#0f172a",
        "MUTED": "#64748b",
        "CARD": "#ffffff",
        "BORDER": "#e5e7eb",
    },
}

def apply_theme(root: tk.Tk, mode: str = "dark") -> None:
    mode = mode if mode in PALETTES else "dark"
    colors = PALETTES[mode]

    style = ttk.Style(root)
    style.theme_use("clam")


    root.configure(bg=colors["BG"])
    style.configure("TFrame", background=colors["BG"])
    style.configure("TLabel", background=colors["BG"], foreground=colors["TEXT"])
    style.configure("TCheckbutton", background=colors["BG"], foreground=colors["TEXT"])
    style.configure("TRadiobutton", background=colors["BG"], foreground=colors["TEXT"])
    style.configure("TButton", padding=10)


    style.configure("TEntry", fieldbackground=colors["SURFACE"], foreground=colors["TEXT"])
    style.configure(
        "TCombobox",
        fieldbackground=colors["SURFACE"],
        background=colors["SURFACE"],
        foreground=colors["TEXT"],
    )
    style.map("TCombobox", fieldbackground=[("readonly", colors["SURFACE"])])

    style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"), foreground=colors["TEXT"])
    style.configure("Subtitle.TLabel", font=("Segoe UI", 11), foreground=colors["MUTED"])
    style.configure("Section.TLabel", font=("Segoe UI", 12, "bold"), foreground=colors["TEXT"])
    style.configure("Hint.TLabel", font=("Segoe UI", 10), foreground=colors["MUTED"])
    style.configure("Status.TLabel", font=("Segoe UI", 10), foreground="#4ade80")

    style.configure("Accent.TButton", background=colors["PRIMARY"], foreground="white")
    style.map("Accent.TButton", background=[("active", _shade(colors["PRIMARY"], -12))])


    style.configure("TScale", background=colors["BG"], troughcolor=colors["SURFACE"], sliderrelief="flat")


    style.configure("TNotebook", background=colors["BG"], borderwidth=0)
    style.configure("TNotebook.Tab", padding=(14, 8))
    style.configure("Card.TFrame", background=colors["CARD"], relief="flat", borderwidth=0)


    root._theme_mode = mode
    restyle_descendants(root)


class Card(ttk.Frame):
    """A simple inset card with internal padding."""
    def __init__(self, master, padding=16, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(style="Card.TFrame")
        self.body = ttk.Frame(self, padding=padding)
        self.body.pack(fill="both", expand=True)


def style_text(text_widget: tk.Text) -> None:
    """Apply current theme colors to a tk.Text widget."""
    mode = getattr(text_widget.winfo_toplevel(), "_theme_mode", "dark")
    colors = PALETTES[mode]
    text_widget.configure(
        bg=colors["CARD"],
        fg=colors["TEXT"],
        insertbackground=colors["TEXT"],
        padx=10, pady=10,
        highlightthickness=1,
        highlightbackground=colors["BORDER"],
        relief="flat", bd=0,
    )

def restyle_descendants(widget: tk.Misc) -> None:
    """Walk the widget tree and restyle any raw Tk widgets (Text, etc.)."""

    if isinstance(widget, tk.Text):
        style_text(widget)

    for child in widget.winfo_children():
        restyle_descendants(child)


def _clamp(n: int) -> int:
    return max(0, min(255, n))

def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb

def _shade(hex_color: str, percent: int) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    r = _clamp(int(r * (100 + percent) / 100))
    g = _clamp(int(g * (100 + percent) / 100))
    b = _clamp(int(b * (100 + percent) / 100))
    return _rgb_to_hex((r, g, b))

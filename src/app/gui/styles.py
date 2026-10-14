from tkinter import ttk

import sv_ttk

COLOR_BG_DARK: str = "#1c1c1c"
COLOR_BG_INPUT: str = "#222222"
COLOR_ACCENT_BLUE: str = "#58a6ff"
COLOR_STATUS_SUCCESS: str = "#3fb950"
COLOR_STATUS_WARNING: str = "#d29922"
COLOR_STATUS_DANGER: str = "#f85149"
COLOR_TEXT_MUTED: str = "#8b949e"
COLOR_TEXT_LIGHT: str = "#eaeaea"


def apply_theme() -> None:
    """Applies the application dark theme and custom widget styles."""
    sv_ttk.set_theme("dark")
    style = ttk.Style()
    style.configure("Red.TButton", foreground=COLOR_STATUS_DANGER)

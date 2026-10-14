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

# Standard button widths (in text character units, not pixels)
BTN_WIDTH_ACTION: int = 14     # Standard dialog/toolbar action buttons
BTN_WIDTH_COMPACT: int = 11    # Compact action buttons (Browse, Add files)
BTN_WIDTH_ICON: int = 3        # Square icon buttons (↗, ↻)
BTN_WIDTH_HEADER: int = 10     # Header buttons (Help, GitHub)
BTN_WIDTH_PRIMARY: int = 22    # Large CTA button (▶ Start Transform)


def apply_theme() -> None:
    """Applies the application dark theme and custom widget styles."""
    sv_ttk.set_theme("dark")
    style = ttk.Style()
    style.configure("Red.TButton", foreground=COLOR_STATUS_DANGER)
    style.configure("Action.TButton", width=BTN_WIDTH_ACTION)
    style.configure("Compact.TButton", width=BTN_WIDTH_COMPACT)
    style.configure("Icon.TButton", width=BTN_WIDTH_ICON)
    style.configure("Header.TButton", width=BTN_WIDTH_HEADER)
    style.configure("Primary.TButton", width=BTN_WIDTH_PRIMARY)

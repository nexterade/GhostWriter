import os
import sys
import base64


# === ANSI CODES ===
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"

    # Midnight palette (ANSI 256-color)
    ACCENT = "\033[38;5;117m"       # cyan #38bdf8
    ACCENT_DIM = "\033[38;5;74m"    # darker cyan
    ACCENT_BOLD = "\033[1;38;5;117m"
    PURPLE = "\033[38;5;141m"       # #a78bfa
    PURPLE_DIM = "\033[38;5;97m"
    GREEN = "\033[38;5;114m"        # #4ade80
    GREEN_DIM = "\033[38;5;71m"
    YELLOW = "\033[38;5;221m"       # #facc15
    RED = "\033[38;5;203m"          # #f87171
    GRAY = "\033[38;5;245m"         # #94a3b8
    GRAY_DIM = "\033[38;5;240m"
    WHITE = "\033[38;5;255m"        # #f8fafc
    BLACK = "\033[38;5;232m"

    BG_ACCENT = "\033[48;5;117m"
    BG_DARK = "\033[48;5;234m"
    BG_SURFACE = "\033[48;5;236m"


# === BRAND CONSTANTS (single source of truth) ===

# Ghost icon — inline SVG, auto pakai var(--accent) di browser
LOGO_SVG_INLINE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'fill="var(--accent, #38bdf8)" aria-hidden="true" class="gw-logo-svg">'
    '<path d="M12 2C7.58 2 4 5.58 4 10v11l2.5-2 2.5 2 2.5-2 2.5 2 2.5-2 2.5 2V10c0-4.42-3.58-8-8-8z'
    'm-3 9a1.25 1.25 0 1 1 0-2.5 1.25 1.25 0 0 1 0 2.5z'
    'm6 0a1.25 1.25 0 1 1 0-2.5 1.25 1.25 0 0 1 0 2.5z"/>'
    '</svg>'
)

# Favicon — standalone, dark rounded bg + accent ghost
FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    '<rect width="24" height="24" rx="5" fill="#0b0f19"/>'
    '<path fill="#38bdf8" d="M12 4C8.13 4 5 7.13 5 11v7.5l2-1.5 2 1.5 2-1.5 2 1.5 2-1.5 2 1.5V11c0-3.87-3.13-7-7-7z'
    'm-2.5 7a1 1 0 1 1 0-2 1 1 0 0 1 0 2z'
    'm5 0a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/>'
    '</svg>'
)

# Pre-encode base64 (dipake di <link rel="icon">)
FAVICON_B64 = base64.b64encode(FAVICON_SVG.encode("utf-8")).decode("ascii")


def get_favicon_link() -> str:
    """Return <link> tag siap inject ke <head>."""
    return (
        '<link rel="icon" type="image/svg+xml" '
        f'href="data:image/svg+xml;base64,{FAVICON_B64}">'
    )


def get_logo_html(size: int = 22, wordmark: bool = True) -> str:
    """
    Return brand HTML: SVG logo + (optional) wordmark.
    size: ukuran SVG dalam px.
    """
    svg = LOGO_SVG_INLINE.replace(
        'class="gw-logo-svg"',
        f'class="gw-logo-svg" width="{size}" height="{size}"'
    )
    if not wordmark:
        return svg
    return (
        '<span class="gw-brand">'
        f'{svg}'
        '<span class="gw-wordmark">GhostWriter</span>'
        '</span>'
    )


# CLI ASCII banner (fallback kalo unicode gak support, atau dipakai di header CLI)
CLI_BANNER = r"""
   __ _  _  _  __  _  _  _    _  _  _  _  _  _
  / _` || || ||  \| || || |  | || || || || || |
 | (_| || || || |\ || || |  | ||_||_||_||_||_|
  \__, ||_||_||_| \_||_||_|  |_|(_)(_)(_)(_)(_)
  |___/  👻  ARCHIVE  📜
"""

CLI_BANNER_COMPACT = "👻 GhostWriter 📜"


def _supports_ansi() -> bool:
    if not sys.stdout.isatty():
        return False
    term = os.environ.get("TERM", "")
    return term not in ("", "dumb")


def _supports_unicode() -> bool:
    encoding = getattr(sys.stdout, "encoding", "") or ""
    return "utf" in encoding.lower()


class Theme:
    def __init__(self):
        self.enabled = _supports_ansi()
        self.unicode = _supports_unicode()

    def color(self, code: str, text: str) -> str:
        if not self.enabled:
            return text
        return f"{code}{text}{C.RESET}"

    # Shortcut methods
    def accent(self, t: str) -> str: return self.color(C.ACCENT, t)
    def accent_dim(self, t: str) -> str: return self.color(C.ACCENT_DIM, t)
    def accent_bold(self, t: str) -> str: return self.color(C.ACCENT_BOLD, t)
    def purple(self, t: str) -> str: return self.color(C.PURPLE, t)
    def purple_dim(self, t: str) -> str: return self.color(C.PURPLE_DIM, t)
    def green(self, t: str) -> str: return self.color(C.GREEN, t)
    def green_dim(self, t: str) -> str: return self.color(C.GREEN_DIM, t)
    def yellow(self, t: str) -> str: return self.color(C.YELLOW, t)
    def red(self, t: str) -> str: return self.color(C.RED, t)
    def gray(self, t: str) -> str: return self.color(C.GRAY, t)
    def gray_dim(self, t: str) -> str: return self.color(C.GRAY_DIM, t)
    def white(self, t: str) -> str: return self.color(C.WHITE, t)
    def bold(self, t: str) -> str: return self.color(C.BOLD, t)
    def dim(self, t: str) -> str: return self.color(C.DIM, t)
    def italic(self, t: str) -> str: return self.color(C.ITALIC, t)
    def underline(self, t: str) -> str: return self.color(C.UNDERLINE, t)

    # Composite
    def bold_accent(self, t: str) -> str:
        if not self.enabled: return t
        return f"{C.BOLD}{C.ACCENT}{t}{C.RESET}"

    def bold_white(self, t: str) -> str:
        if not self.enabled: return t
        return f"{C.BOLD}{C.WHITE}{t}{C.RESET}"

    def status(self, label: str, value: str, color: str = None) -> str:
        """Format: 'label: value' dengan label gray."""
        color = color or C.WHITE
        if not self.enabled:
            return f"{label}: {value}"
        return f"{C.GRAY}{label}{C.RESET}: {color}{value}{C.RESET}"


# Singleton
_theme = Theme()


def get_theme() -> Theme:
    return _theme


# === ICON MAP ===
ICONS = {
    "info": "ℹ",
    "ok": "✓",
    "warn": "⚠",
    "error": "✗",
    "fetch": "↻",
    "download": "↓",
    "upload": "↑",
    "skip": "⏭",
    "shield": "🛡",
    "sparkle": "✦",
    "ghost": "👻",
    "moon": "🌙",
    "db": "🗄",
    "clock": "⏱",
    "file": "📄",
    "folder": "📁",
    "rocket": "🚀",
    "target": "🎯",
    "check": "☑",
    "cross": "☐",
    "arrow": "→",
    "bullet": "•",
    "user": "👤",
    "ai": "🤖",
    "key": "🔑",
    "link": "🔗",
    "trash": "🗑",
    "hammer": "🔨",
    "palette": "🎨",
}
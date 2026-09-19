import sys
import os
import time
import threading
from tools.theme import C, get_theme, ICONS


DEBUG = os.environ.get("GW_DEBUG") == "1"

SPINNER_BRAILLE = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
SPINNER_DOTS = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
SPINNER_ASCII = ["|", "/", "-", "\\"]
SPINNER_ARROW = ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"]


_theme = get_theme()


class LoadingSpinner:
    def __init__(self, initial_text: str = "Loading...", ascii_only: bool = False):
        self.text = initial_text
        self.running = False
        self._thread = None
        self._lock = threading.Lock()
        self._start_time = 0.0
        self._last_width = 0

        if ascii_only or not _theme.unicode:
            self._frames = SPINNER_ASCII
        else:
            self._frames = SPINNER_BRAILLE

        self._use_ansi = _theme.enabled

    def _render(self, frame: str):
        if not self._use_ansi:
            return

        elapsed = time.time() - self._start_time
        if elapsed < 1.0:
            time_str = ""
        elif elapsed < 60:
            time_str = f" {C.DIM}{elapsed:.0f}s{C.RESET}"
        else:
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            time_str = f" {C.DIM}{mins}m{secs:02d}s{C.RESET}"

        with self._lock:
            line = f"  {C.ACCENT}{frame}{C.RESET} {C.WHITE}{self.text}{C.RESET}{time_str}"
            pad = max(0, self._last_width - len(self.text) - 5)
            self._last_width = len(self.text) + 5
            sys.stdout.write(f"\r\033[K{line}{' ' * pad}")
            sys.stdout.flush()

    def _spin(self):
        idx = 0
        while self.running:
            frame = self._frames[idx % len(self._frames)]
            self._render(frame)
            idx += 1
            time.sleep(0.08)

    def start(self):
        if self.running:
            return
        self.running = True
        self._start_time = time.time()

        if not self._use_ansi:
            print(f"  {C.ACCENT}...{C.RESET} {self.text}")
            return

        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def update(self, new_text: str):
        with self._lock:
            self.text = new_text

    def stop(self, final_text: str = None, status: str = "ok"):
        if not self.running:
            if final_text:
                print_status(final_text, status)
            return
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)

        if not self._use_ansi:
            if final_text:
                print_status(final_text, status)
            return

        with self._lock:
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()

        if final_text:
            print_status(final_text, status)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.stop(f"[X] {self.text} (error)", status="error")
        else:
            self.stop()


def _badge(label: str, status: str) -> str:
    if not _theme.enabled:
        return f"[{status.upper()}] {label}"
    color_map = {
        "info": C.ACCENT,
        "ok": C.GREEN,
        "warn": C.YELLOW,
        "error": C.RED,
        "fetch": C.ACCENT,
        "download": C.ACCENT,
        "upload": C.PURPLE,
        "skip": C.GRAY,
        "ghost": C.PURPLE,
    }
    color = color_map.get(status, C.ACCENT)
    icon = ICONS.get(status, "•")
    return f"{color}{icon}{C.RESET} {C.WHITE}{label}{C.RESET}"


def print_status(text: str, status: str = "info"):
    if _theme.enabled:
        sys.stdout.write(f"\r\033[K  {_badge(text, status)}\n")
        sys.stdout.flush()
    else:
        icon = ICONS.get(status, "•")
        print(f"  {icon}  {text}")


def print_success(text: str):
    print_status(text, "ok")


def print_error(text: str):
    print_status(text, "error")


def print_warn(text: str):
    print_status(text, "warn")


def print_info(text: str):
    print_status(text, "info")


def print_section(title: str, icon: str = "sparkle"):
    line = "─" * 50
    icon_char = ICONS.get(icon, "✦")
    if _theme.enabled:
        print(f"\n  {C.ACCENT_DIM}{line}{C.RESET}")
        print(f"  {C.ACCENT}{icon_char}{C.RESET}  {C.BOLD}{C.WHITE}{title}{C.RESET}")
        print(f"  {C.ACCENT_DIM}{line}{C.RESET}")
    else:
        print(f"\n  {'─' * 50}")
        print(f"  {icon_char}  {title}")
        print(f"  {'─' * 50}")


def print_kv(key: str, value: str, color: str = None):
    color = color or C.WHITE
    if _theme.enabled:
        print(f"  {C.GRAY}{key}{C.RESET}: {color}{value}{C.RESET}")
    else:
        print(f"  {key}: {value}")


def print_bullet(text: str, indent: int = 2, color: str = None):
    color = color or C.WHITE
    pad = " " * indent
    if _theme.enabled:
        print(f"{pad}{C.ACCENT}•{C.RESET} {color}{text}{C.RESET}")
    else:
        print(f"{pad}• {text}")


def print_numbered(idx: int, text: str, indent: int = 2):
    pad = " " * indent
    if _theme.enabled:
        print(f"{pad}{C.ACCENT}[{idx:>2}]{C.RESET} {C.WHITE}{text}{C.RESET}")
    else:
        print(f"{pad}[{idx}] {text}")


def print_banner():
    banner = r"""
   ________               __  _       __      _ __            
  / ____/ /_  ____  _____/ /_| |     / /_____(_) /____  _____ 
 / / __/ __ \/ __ \/ ___/ __/ | /| / / ___/ / __/ _ \/ ___/ 
/ /_/ / / / / /_/ (__  ) /_ | |/ |/ / /  / / /_/  __/ /     
\____/_/ /_/\____/____/\__/ |__/|__/_/  /_/\__/\___/_/      
                      👻 AI Chat Mirroring Engine
"""
    if _theme.enabled:
        for i, line in enumerate(banner.split("\n")):
            if i < 7:
                print(f"{C.ACCENT}{line}{C.RESET}")
            else:
                print(f"{C.BOLD}{C.WHITE}{line}{C.RESET}")
    else:
        print(banner)


def print_separator():
    if _theme.enabled:
        print(f"\n  {C.ACCENT_DIM}{'─' * 55}{C.RESET}")
    else:
        print(f"\n  {'─' * 55}")


def progress_bar(current: int, total: int, width: int = 30, label: str = "") -> str:
    if total <= 0:
        return ""

    pct = min(current / total, 1.0)
    filled = int(width * pct)
    empty = width - filled

    if _theme.enabled:
        if filled > 0:
            fill_mid = filled // 2
            bar = (
                C.ACCENT_DIM + "█" * fill_mid
                + C.ACCENT + "█" * (filled - fill_mid)
            )
        else:
            bar = ""
        empty_bar = C.GRAY + C.DIM + "░" * empty + C.RESET
        pct_color = C.GREEN if pct >= 0.75 else (C.YELLOW if pct >= 0.4 else C.ACCENT)
        label_part = f" {C.GRAY}{label}{C.RESET}" if label else ""
        return f"{C.GRAY}[{C.RESET}{bar}{empty_bar}{C.GRAY}]{C.RESET} {pct_color}{current}/{total}{C.RESET} {C.DIM}({pct*100:.0f}%){C.RESET}{label_part}"
    else:
        bar = "█" * filled + "░" * empty
        label_part = f" {label}" if label else ""
        return f"[{bar}] {current}/{total} ({pct*100:.0f}%){label_part}"


def print_prompt(text: str) -> str:
    if _theme.enabled:
        return input(f"{C.ACCENT}→{C.RESET} {C.WHITE}{text}{C.RESET} ")
    return input(f"→ {text} ")
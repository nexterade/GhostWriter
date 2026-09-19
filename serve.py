#!/usr/bin/env python3
"""
GhostWriter — Local HTTP Server

Serve folder `public/` di http://localhost:8000/
Auto-detect Termux & auto-open browser.

Usage:
    python3 serve.py
    python3 serve.py --port 8001
    python3 serve.py --no-open
"""
import os
import sys
import argparse
import http.server
import socketserver
import subprocess
import webbrowser
from pathlib import Path


DEFAULT_PORT = 8000
PUBLIC_DIR = "public"


# === TERMINAL COLORS ===
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ACCENT = "\033[38;5;117m"
    GREEN = "\033[38;5;114m"
    YELLOW = "\033[38;5;221m"
    RED = "\033[38;5;203m"
    GRAY = "\033[38;5;245m"
    WHITE = "\033[38;5;255m"


def _supports_ansi() -> bool:
    if not sys.stdout.isatty():
        return False
    return os.environ.get("TERM", "") not in ("", "dumb")


ANSI = _supports_ansi()


def _c(code: str, text: str) -> str:
    if not ANSI:
        return text
    return f"{code}{text}{C.RESET}"


# === HELPERS ===

def is_termux() -> bool:
    prefix = os.environ.get("PREFIX", "")
    return "com.termux" in prefix


def open_browser(url: str) -> bool:
    """Buka browser — Termux pakai termux-open-url, sisanya webbrowser."""
    try:
        if is_termux():
            subprocess.Popen(
                ["termux-open-url", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        else:
            return webbrowser.open(url)
    except Exception as e:
        print(_c(C.RED, f"  ✗ Gagal buka browser: {e}"))
        return False


def print_banner(port: int, public_path: str):
    print()
    print(_c(C.ACCENT, "━" * 52))
    print(_c(C.BOLD + C.WHITE, "  👻  GhostWriter — Local Server"))
    print(_c(C.ACCENT, "━" * 52))
    print()
    print(f"  {_c(C.GRAY, '📂 Serving:')} {_c(C.WHITE, public_path)}")
    print(f"  {_c(C.GRAY, '🔌 Port:')}    {_c(C.WHITE, str(port))}")
    print(f"  {_c(C.GRAY, '🌐 URL:')}     {_c(C.ACCENT, f'http://localhost:{port}/')}")
    print()
    print(_c(C.ACCENT, "━" * 52))
    print(_c(C.GRAY, "  Server berjalan... (Ctrl+C buat stop)"))
    print(_c(C.ACCENT, "━" * 52))
    print()


def prompt_open_browser(url: str, auto_open: bool) -> None:
    """Tanya user mau buka browser atau engga."""
    if auto_open:
        print(_c(C.ACCENT, "  🌐 Membuka browser..."))
        ok = open_browser(url)
        if ok:
            print(_c(C.GREEN, "  ✓ Browser dibuka"))
        else:
            print(_c(C.YELLOW, "  ⚠ Gagal auto-open. Buka manual:"))
            print(_c(C.WHITE, f"    {url}"))
        print()
        return

    # Prompt
    try:
        if ANSI:
            resp = input(
                f"  {C.ACCENT}→{C.RESET} "
                f"{C.WHITE}Buka browser sekarang?{C.RESET} "
                f"{C.GRAY}[Y/n]{C.RESET}: "
            ).strip().lower()
        else:
            resp = input("  Buka browser sekarang? [Y/n]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        return

    if resp in ("", "y", "yes"):
        print(_c(C.ACCENT, "  🌐 Membuka browser..."))
        ok = open_browser(url)
        if ok:
            print(_c(C.GREEN, "  ✓ Browser dibuka"))
        else:
            print(_c(C.YELLOW, "  ⚠ Gagal auto-open. Buka manual:"))
            print(_c(C.WHITE, f"    {url}"))
    else:
        print(_c(C.GRAY, "  ⏭ Skip buka browser."))
        print(_c(C.WHITE, f"  Buka manual: {url}"))
    print()


# === SERVER ===

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler dengan log yang lebih rapi."""

    def log_message(self, format, *args):
        # Format: 127.0.0.1 - - [time] "GET /path HTTP/1.1" 200 -
        msg = format % args
        # Filter asset statis biar gak spam
        if any(ext in msg for ext in (".js", ".css", ".woff", ".png", ".ico", ".svg")):
            return
        print(_c(C.GRAY, f"  {msg}"))

    def end_headers(self):
        # Disable cache biar selalu fresh pas development
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()


def run_server(port: int, public_path: str, auto_open: bool):
    # Pindah ke folder public/
    os.chdir(public_path)

    # Server
    handler = QuietHandler
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            url = f"http://localhost:{port}/"
            print_banner(port, os.path.abspath(public_path))

            if not auto_open:
                prompt_open_browser(url, auto_open=False)

            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print()
                print(_c(C.YELLOW, "  ⏹ Server dihentikan. Sampai jumpa! 👻"))
                print()
    except OSError as e:
        if "Address already in use" in str(e) or "in use" in str(e).lower():
            print()
            print(_c(C.RED, f"  ✗ Port {port} udah dipake proses lain."))
            print(_c(C.GRAY, "    Coba:"))
            print(_c(C.WHITE, f"      python3 serve.py --port {port + 1}"))
            print(_c(C.GRAY, "    Atau kill proses lama:"))
            print(_c(C.WHITE, f"      lsof -ti:{port} | xargs kill"))
            print()
            sys.exit(1)
        else:
            raise


# === MAIN ===

def main():
    parser = argparse.ArgumentParser(
        prog="serve.py",
        description="Serve GhostWriter output folder di browser."
    )
    parser.add_argument("--port", "-p", type=int, default=DEFAULT_PORT,
                        help=f"Port server (default: {DEFAULT_PORT})")
    parser.add_argument("--no-open", action="store_true",
                        help="Jangan auto-open browser, tanya dulu")
    args = parser.parse_args()

    # Cek folder public/
    public_path = Path(PUBLIC_DIR)
    if not public_path.is_dir():
        print()
        print(_c(C.RED, f"  ✗ Folder '{PUBLIC_DIR}/' gak ada."))
        print(_c(C.GRAY, "    Render dulu lewat:"))
        print(_c(C.WHITE, "      python3 main.py"))
        print()
        sys.exit(1)

    # Cek index.html
    if not (public_path / "index.html").is_file():
        print()
        print(_c(C.YELLOW, f"  ⚠ Folder '{PUBLIC_DIR}/' ada tapi index.html belum kebentuk."))
        print(_c(C.GRAY, "    Coba render atau sync dulu:"))
        print(_c(C.WHITE, "      python3 main.py"))
        print(_c(C.WHITE, "      python3 sync.py"))
        print()
        # Lanjut aja — mungkin user mau serve folder kosong
        input(_c(C.GRAY, "  [Enter] buat lanjut / Ctrl+C buat batal... "))

    # Auto-open logic:
    # Kalo --no-open: tanya dulu
    # Kalo tanpa --no-open: auto-open
    auto_open = not args.no_open

    run_server(args.port, str(public_path), auto_open=auto_open)


if __name__ == "__main__":
    main()

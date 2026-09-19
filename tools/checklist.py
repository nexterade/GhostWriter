import sys
import os
import shutil
import subprocess
import json
from typing import List
from tools.theme import C, get_theme, ICONS


DEBUG = os.environ.get("GW_DEBUG") == "1"


def _debug(msg: str):
    if DEBUG:
        print(f"  [DBG] {msg}")


def _is_termux() -> bool:
    return (
        "com.termux" in os.environ.get("PREFIX", "")
        or os.path.exists("/data/data/com.termux")
        or "TERMUX_VERSION" in os.environ
    )


def _has_termux_api() -> bool:
    try:
        result = subprocess.run(
            ["which", "termux-dialog"],
            capture_output=True, text=True, timeout=3
        )
        return result.returncode == 0
    except Exception:
        return False


def _termux_dialog_text(title: str, hint: str = "") -> str:
    try:
        cmd = ["termux-dialog", "text", "-t", title]
        if hint:
            cmd += ["-i", hint]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return ""
        try:
            data = json.loads(result.stdout)
            return data.get("text", "").strip()
        except json.JSONDecodeError:
            return ""
    except Exception:
        return ""


def _termux_dialog_radio(title: str, options: List[str]) -> str:
    try:
        cmd = ["termux-dialog", "radio", "-t", title, "-v", ",".join(options)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return ""
        try:
            data = json.loads(result.stdout)
            return data.get("text", "").strip()
        except json.JSONDecodeError:
            return ""
    except Exception:
        return ""


def _termux_flow(items: List[dict]) -> List[int]:
    total = len(items)
    modes = [
        f"Pilih semua ({total})",
        "Pilih range (misal 1-5)",
        "Pilih manual (misal 1,3,5)",
        "Batal",
    ]
    mode = _termux_dialog_radio(f"Checklist {total} item — pilih mode", modes)

    if not mode or "Batal" in mode:
        return []

    if "Pilih semua" in mode:
        return list(range(total))

    if "Pilih range" in mode:
        raw = _termux_dialog_text("Range pilih", f"1-{total}, misal: 1-5")
        if not raw:
            return []
        indices = set()
        for part in raw.split(","):
            part = part.strip()
            if "-" in part:
                try:
                    a, b = part.split("-", 1)
                    a, b = int(a), int(b)
                    for i in range(min(a, b), max(a, b) + 1):
                        if 1 <= i <= total:
                            indices.add(i - 1)
                except ValueError:
                    continue
            elif part.isdigit():
                i = int(part)
                if 1 <= i <= total:
                    indices.add(i - 1)
        return sorted(indices)

    if "Pilih manual" in mode:
        raw = _termux_dialog_text("Pilih manual", f"contoh: 1,3,5,7 (1-{total})")
        if not raw:
            return []
        indices = set()
        for part in raw.replace(" ", "").split(","):
            if part.isdigit():
                i = int(part)
                if 1 <= i <= total:
                    indices.add(i - 1)
        return sorted(indices)

    return []


def _get_terminal_width() -> int:
    try:
        return shutil.get_terminal_size((80, 24)).columns
    except Exception:
        return 80


def _clear_lines(n: int):
    for _ in range(n):
        sys.stdout.write("\033[1A\033[2K")
    sys.stdout.flush()


def _read_key() -> str:
    try:
        import termios
        import tty
        import select
        import os as _os
    except ImportError:
        return ""

    fd = sys.stdin.fileno()
    try:
        old = termios.tcgetattr(fd)
    except Exception:
        return ""

    try:
        tty.setraw(fd)
        new = termios.tcgetattr(fd)
        new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
        new[6][termios.VMIN] = 1
        new[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSANOW, new)

        r, _, _ = select.select([fd], [], [], 2.0)
        if not r:
            return ""

        first = _os.read(fd, 1)
        if not first:
            return ""

        ch = first.decode("utf-8", errors="ignore")

        if ch == "\x1b":
            rest = b""
            for _ in range(2):
                r, _, _ = select.select([fd], [], [], 0.1)
                if not r:
                    break
                rest += _os.read(fd, 1)
            full = rest.decode("utf-8", errors="ignore")
            if full == "[A": return "up"
            elif full == "[B": return "down"
            elif full == "[C": return "right"
            elif full == "[D": return "left"
            elif full == "[H": return "home"
            elif full == "[F": return "end"
            return "esc"

        if ch in ("\r", "\n"): return "enter"
        if ch == " ": return "space"
        if ch in ("q", "Q"): return "q"
        if ch in ("a", "A"): return "a"
        if ch in ("n", "N"): return "n"
        if ch in ("i", "I"): return "i"
        if ch == "\x03": raise KeyboardInterrupt
        if ch == "\x04": return "q"
        return ch
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception:
            pass


def _count_render_lines(items, cursor, selected, scroll_offset, max_visible) -> int:
    total = len(items)
    if total > max_visible:
        visible_start = max(0, min(scroll_offset, total - max_visible))
    else:
        visible_start = 0
    visible_end = min(visible_start + max_visible, total)
    return 12 + (visible_end - visible_start)


def _render_list(items, cursor, selected, scroll_offset, max_visible=15):
    t = get_theme()
    total = len(items)
    width = _get_terminal_width()
    sep = "─" * min(width - 4, 60)

    if t.enabled:
        print(f"\n  {C.ACCENT_DIM}{sep}{C.RESET}")
        print(f"  {C.ACCENT}📋{C.RESET}  {C.BOLD}{C.WHITE}Mode Checklist — {total} item{C.RESET}")
        print(f"  {C.ACCENT_DIM}{sep}{C.RESET}")
        print(f"  {C.GRAY}Navigasi:{C.RESET} {C.ACCENT}j/k{C.RESET} {C.GRAY}atau{C.RESET} {C.ACCENT}↑/↓{C.RESET}  {C.GRAY_DIM}│{C.RESET}  {C.ACCENT}Space{C.RESET} {C.GRAY}= centang{C.RESET}  {C.GRAY_DIM}│{C.RESET}  {C.ACCENT}Enter{C.RESET} {C.GRAY}= lanjut{C.RESET}")
        print(f"  {C.ACCENT}a{C.RESET} {C.GRAY}= semua{C.RESET}  {C.GRAY_DIM}│{C.RESET}  {C.ACCENT}n{C.RESET} {C.GRAY}= kosong{C.RESET}  {C.GRAY_DIM}│{C.RESET}  {C.ACCENT}i{C.RESET} {C.GRAY}= invert{C.RESET}  {C.GRAY_DIM}│{C.RESET}  {C.ACCENT}q{C.RESET} {C.GRAY}= batal{C.RESET}")
        print(f"  {C.ACCENT_DIM}{sep}{C.RESET}")
    else:
        print(f"\n  📋 Mode Checklist — {total} item")
        print(f"  {sep}")
        print(f"  Navigasi: j/k atau ↑/↓ | Space = centang | Enter = lanjut")
        print(f"  a = semua | n = kosong | i = invert | q = batal")
        print(f"  {sep}")

    if total > max_visible:
        visible_start = max(0, min(scroll_offset, total - max_visible))
    else:
        visible_start = 0
    visible_end = min(visible_start + max_visible, total)

    if visible_start > 0:
        msg = f"  ... {visible_start} item di atas"
        print(f"  {C.GRAY}{msg}{C.RESET}" if t.enabled else msg)
    else:
        print()

    for i in range(visible_start, visible_end):
        item = items[i]
        marker = "▶" if i == cursor else " "
        checkbox = "☑" if i in selected else "☐"
        title = item.get("title", "Tanpa Judul")
        created = item.get("created_at", "")

        max_title = max(20, width - 30)
        if len(title) > max_title:
            title = title[:max_title - 1] + "…"

        if t.enabled:
            marker_colored = f"{C.ACCENT}{marker}{C.RESET}" if i == cursor else f"{C.GRAY_DIM}{marker}{C.RESET}"
            check_colored = f"{C.GREEN}{checkbox}{C.RESET}" if i in selected else f"{C.GRAY}{checkbox}{C.RESET}"
            num_colored = f"{C.ACCENT}{i + 1:>2}{C.RESET}"
            if i == cursor:
                title_colored = f"{C.BOLD}{C.WHITE}{title}{C.RESET}"
            else:
                title_colored = f"{C.WHITE}{title}{C.RESET}"
            created_colored = f" {C.GRAY}({created}){C.RESET}" if created else ""
            print(f"  {marker_colored} {check_colored} [{num_colored}] {title_colored}{created_colored}")
        else:
            line = f"  {marker} {checkbox} [{i + 1:>2}] {title}"
            if created:
                line += f"  ({created})"
            print(line[:width])

    if visible_end < total:
        msg = f"  ... {total - visible_end} item di bawah"
        print(f"  {C.GRAY}{msg}{C.RESET}" if t.enabled else msg)
    else:
        print()

    if t.enabled:
        print(f"  {C.ACCENT_DIM}{sep}{C.RESET}")
        selected_pct = (len(selected) / total * 100) if total else 0
        sel_color = C.GREEN if len(selected) > 0 else C.GRAY
        print(f"  {C.GRAY}Dipilih:{C.RESET} {sel_color}{len(selected)}/{total}{C.RESET} {C.DIM}({selected_pct:.0f}%){C.RESET}")
        print()
    else:
        print(f"  {sep}")
        print(f"  Dipilih: {len(selected)}/{total}")
        print()


def _can_use_raw_input() -> bool:
    if not sys.stdin.isatty():
        _debug("stdin bukan TTY")
        return False
    try:
        import termios  # noqa
        import tty       # noqa
        import select    # noqa
    except ImportError:
        _debug("termios/tty/select gak available")
        return False
    return True


def _fallback_number_selection(items: List[dict]) -> List[int]:
    t = get_theme()
    print()
    if t.enabled:
        print(f"  {C.YELLOW}⚠{C.RESET}  {C.WHITE}Terminal gak support mode interaktif. Pakai mode angka.{C.RESET}")
        print(f"  {C.GRAY}Format:{C.RESET} {C.ACCENT}'1,3,5'{C.RESET} {C.GRAY}atau{C.RESET} {C.ACCENT}'1-5'{C.RESET} {C.GRAY}atau{C.RESET} {C.ACCENT}'all'{C.RESET} {C.GRAY}(kosong = batal){C.RESET}")
        raw = input(f"  {C.ACCENT}→{C.RESET} {C.WHITE}Pilih{C.RESET}: ").strip().lower()
    else:
        print(f"  ⚠  Terminal gak support mode interaktif. Pakai mode angka.")
        print(f"  Format: '1,3,5' atau '1-5' atau 'all' (kosong = batal)")
        raw = input(f"  → Pilih: ").strip().lower()

    if raw in ("all", "semua", "a", "*"):
        return list(range(len(items)))
    if not raw:
        return []

    indices = set()
    for part in raw.split(","):
        part = part.strip()
        if "-" in part:
            try:
                a, b = part.split("-", 1)
                a, b = int(a), int(b)
                for i in range(min(a, b), max(a, b) + 1):
                    if 1 <= i <= len(items):
                        indices.add(i - 1)
            except ValueError:
                continue
        elif part.isdigit():
            i = int(part)
            if 1 <= i <= len(items):
                indices.add(i - 1)

    return sorted(indices)


def interactive_checklist(items: List[dict]) -> List[int]:
    if not items:
        return []

    if _is_termux() and _has_termux_api():
        _debug("Termux detected + termux-api available — pake dialog")
        result = _termux_flow(items)
        return result

    if not _can_use_raw_input():
        return _fallback_number_selection(items)

    cursor = 0
    selected = set()
    scroll_offset = 0
    max_visible = 15
    total = len(items)
    first_render_lines = 0

    while True:
        if first_render_lines > 0:
            _clear_lines(first_render_lines)
        first_render_lines = _count_render_lines(items, cursor, selected, scroll_offset, max_visible)
        _render_list(items, cursor, selected, scroll_offset, max_visible)

        key = _read_key()

        if key == "up" or key == "k":
            cursor = max(0, cursor - 1)
        elif key == "down" or key == "j":
            cursor = min(total - 1, cursor + 1)
        elif key == "space":
            if cursor in selected:
                selected.discard(cursor)
            else:
                selected.add(cursor)
            if cursor < total - 1:
                cursor += 1
        elif key == "a":
            selected = set(range(total))
        elif key == "n":
            selected = set()
        elif key == "i":
            selected = set(range(total)) - selected
        elif key == "enter":
            return sorted(selected)
        elif key == "q" or key == "esc":
            print("  [~] Checklist dibatalkan.")
            return []
        elif key == "":
            _debug("Key read timeout — fallback ke mode angka")
            return _fallback_number_selection(items)

        if cursor < scroll_offset:
            scroll_offset = cursor
        elif cursor >= scroll_offset + max_visible:
            scroll_offset = cursor - max_visible + 1
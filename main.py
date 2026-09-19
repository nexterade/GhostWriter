import sys
import os
import time
import glob
import json
import re
import argparse
import traceback
from parsers.json_parser import JSONChatParser
from parsers.md_parser import MarkdownChatParser
from parsers.docx_parser import DocxChatParser
from exporter import HTMLExporter
from tools.deepseek_backup import DeepSeekLiveBackup, _session_delay, AuthExpiredError
from tools.checklist import interactive_checklist
from tools.loading import (
    print_banner, print_section, print_status, print_success,
    print_error, print_warn, print_info, print_kv, print_bullet,
    print_numbered, print_separator, progress_bar, print_prompt,
    LoadingSpinner
)
from tools.theme import C, get_theme


TOKEN_CACHE_FILE = ".deepseek_token"
PUBLIC_DIR = "public"
HISTORY_SUBDIR = "history"
BACKUP_DIR = "backups"
AUTHOR = "@nexterade"


# ============================================================
# UTILITIES
# ============================================================

def load_cached_token() -> str:
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return ""
    return ""


def save_cached_token(token: str):
    try:
        with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(token.strip())
        try:
            os.chmod(TOKEN_CACHE_FILE, 0o600)
        except OSError:
            pass
    except Exception as e:
        print_error(f"Gagal menyimpan cache token: {e}")


def invalidate_cached_token():
    try:
        if os.path.exists(TOKEN_CACHE_FILE):
            os.remove(TOKEN_CACHE_FILE)
    except OSError:
        pass


def scan_local_dump_files():
    """Scan file .json/.md/.docx di root, skip folder backups/."""
    extensions = ["*.json", "*.md", "*.docx"]
    found = []
    for ext in extensions:
        found.extend(glob.glob(ext))
    return sorted(found)


def _format_size(size_bytes: int) -> str:
    """Format size jadi human-readable (B / KB / MB / GB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _get_menu_context() -> dict:
    """Kumpulin context info buat footer menu."""
    ctx = {
        "files_count": 0,
        "files_size": 0,
        "convo_count": 0,
        "has_legacy_dist": False,
    }

    try:
        files = scan_local_dump_files()
        ctx["files_count"] = len(files)
        for f in files:
            try:
                ctx["files_size"] += os.path.getsize(f)
            except OSError:
                pass
    except Exception:
        pass

    try:
        history_dir = os.path.join(PUBLIC_DIR, HISTORY_SUBDIR)
        if os.path.isdir(history_dir):
            for entry in os.listdir(history_dir):
                entry_path = os.path.join(history_dir, entry)
                if os.path.isdir(entry_path):
                    if os.path.isfile(os.path.join(entry_path, "index.html")):
                        ctx["convo_count"] += 1
    except Exception:
        pass

    ctx["has_legacy_dist"] = os.path.isdir("dist")

    return ctx


def _format_clock() -> str:
    """Return waktu lokal format HH:MM."""
    return time.strftime("%H:%M", time.localtime())


def _generate_convo_id(inserted_at, fallback_offset: int = 0) -> str:
    """Generate ID unik untuk convo."""
    if inserted_at is not None:
        try:
            ts = int(float(inserted_at))
            if ts > 0:
                return str(ts)
        except (ValueError, TypeError):
            pass
    return str(int(time.time()) + fallback_offset)


def _format_epoch(raw) -> str:
    if raw is None or raw == "":
        return "—"
    if isinstance(raw, (int, float)):
        try:
            return time.strftime("%Y-%m-%d %H:%M", time.gmtime(raw))
        except (OSError, ValueError, OverflowError):
            return "—"
    return str(raw)[:16].replace("T", " ")


def _parse_selection(raw: str, total: int) -> list:
    raw = raw.strip().lower()
    if raw in ("all", "semua", "a", "*"):
        return list(range(total))
    if raw == "":
        return [0]

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

    return sorted(indices) if indices else [0]


def _print_session_list(sessions, limit=None):
    """Print session list dengan title dalam quote biar gak bingung."""
    view = sessions[:limit] if limit else sessions
    for idx, s in enumerate(view, 1):
        ins = s.get("inserted_at")
        ins_str = _format_epoch(ins)
        title = s.get("title") or "Tanpa Judul"
        # FIX: kasih quote biar jelas ini judul chat, bukan status
        print_numbered(idx, f'💬 "{title}"  ·  {ins_str}')


def _is_cancel(text: str) -> bool:
    return text.strip().lower() in ("0", "q", "quit", "cancel", "batal", "exit")


def _prompt(prompt_text: str, default: str = "") -> str:
    t = get_theme()
    if default == "":
        hint = f" {C.GRAY}[0=batal]{C.RESET}"
    else:
        hint = f" {C.GRAY}[default: {default}, 0=batal]{C.RESET}"

    if t.enabled:
        raw = input(f"{C.ACCENT}->{C.RESET} {C.WHITE}{prompt_text}{C.RESET}{hint}: ").strip()
    else:
        raw = input(f"{prompt_text}{hint}: ").strip()

    if _is_cancel(raw):
        return "__CANCEL__"
    return raw if raw else default


def _prompt_yes_no(prompt_text: str, default: str = "y") -> bool:
    """Prompt Y/n, return bool."""
    t = get_theme()
    hint = f" {C.GRAY}[default: {default}]{C.RESET}"
    if t.enabled:
        raw = input(f"{C.ACCENT}->{C.RESET} {C.WHITE}{prompt_text}{C.RESET}{hint}: ").strip().lower()
    else:
        raw = input(f"{prompt_text}[default: {default}]: ").strip().lower()
    if raw == "":
        raw = default
    return raw in ("y", "yes", "ya")


def _clear_screen():
    """Clear terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def get_parser_for_file(file_path: str):
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext == ".json":
        return JSONChatParser(file_path)
    elif ext == ".md":
        return MarkdownChatParser(file_path)
    elif ext == ".docx":
        return DocxChatParser(file_path)
    else:
        raise ValueError(f"Ekstensi {ext} belum didukung.")


# ============================================================
# PR-40: INTEGRITY CHECK
# ============================================================

def _validate_chat_data(chat_data: dict, convo_label: str = "") -> tuple:
    """PR-40: Validasi chat_data setelah parse."""
    errors = []
    warnings = []
    label = f"'{convo_label}'" if convo_label else "convo"

    if not isinstance(chat_data, dict):
        errors.append(f"{label}: hasil parse bukan dict (got {type(chat_data).__name__})")
        return False, errors, warnings

    title = (chat_data.get("title") or "").strip()
    if not title:
        warnings.append(f"{label}: title kosong, bakal pake default 'Tanpa Judul'")

    messages = chat_data.get("messages")
    if not isinstance(messages, list):
        errors.append(f"{label}: 'messages' bukan list (got {type(messages).__name__})")
        return False, errors, warnings

    if len(messages) == 0:
        errors.append(f"{label}: 0 pesan — file mungkin korup atau schema beda")
        return False, errors, warnings

    invalid_msgs = 0
    empty_content = 0
    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            invalid_msgs += 1
            continue
        role = msg.get("role")
        if role not in ("user", "assistant", "system"):
            invalid_msgs += 1
        content = msg.get("content")
        if not content or not str(content).strip():
            empty_content += 1

    if invalid_msgs > 0:
        warnings.append(f"{label}: {invalid_msgs} pesan dengan format tidak standar")

    if empty_content > 0:
        # FIX: penjelasan kenapa ada pesan kosong
        warnings.append(
            f"{label}: {empty_content} pesan tanpa teks (kemungkinan cuma lampiran gambar)"
        )

    if empty_content > len(messages) / 2:
        errors.append(f"{label}: >50% pesan kosong ({empty_content}/{len(messages)}) — parse kemungkinan gagal")
        return False, errors, warnings

    return True, errors, warnings


def _check_attachments_in_html(html_path: str) -> tuple:
    """PR-40: Cek attachment base64 di HTML."""
    if not os.path.isfile(html_path):
        return 0, 0

    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return 0, 0

    total = len(re.findall(r'class="attachment-box', content))
    missing = len(re.findall(r'class="attachment-box missing', content))

    return total, missing


# ============================================================
# LIVE BACKUP
# ============================================================

def handle_live_deepseek_backup() -> bool:
    print_section("Live Backup DeepSeek", icon="rocket")
    print_info("Ketik '0' di prompt mana aja buat batal & balik ke menu")

    # FIX: kasih overview alur sebelum mulai
    if get_theme().enabled:
        print()
        print(f"  {C.GRAY}Alur:{C.RESET}")
        print(f"  {C.ACCENT_DIM}1.{C.RESET} {C.GRAY}Verifikasi token{C.RESET}")
        print(f"  {C.ACCENT_DIM}2.{C.RESET} {C.GRAY}Ambil daftar obrolan dari akun DeepSeek{C.RESET}")
        print(f"  {C.ACCENT_DIM}3.{C.RESET} {C.GRAY}Pilih obrolan yang mau di-backup{C.RESET}")
        print(f"  {C.ACCENT_DIM}4.{C.RESET} {C.GRAY}Download + simpan ke {C.WHITE}backups/{C.RESET}")

    token = load_cached_token()
    fetcher = None

    if token:
        spinner = LoadingSpinner("Verifikasi token cache...")
        spinner.start()
        fetcher = DeepSeekLiveBackup(token, download_dir="attachments")
        is_valid = fetcher.test_connection()
        if is_valid:
            spinner.stop("Token valid", status="ok")
        else:
            spinner.stop("Token kedaluwarsa", status="warn")
            invalidate_cached_token()
            token = ""
            fetcher = None

    if not token:
        print_section("Cara Ambil Token", icon="key")
        print_numbered(1, "Buka DevTools (F12) di browser")
        print_numbered(2, "Tab 'Application' → Local Storage")
        print_numbered(3, "Cari key 'userToken', salin value-nya")
        print()
        print_info("Login dulu di chat.deepseek.com, baru buka DevTools")

        token_input = _prompt("Paste token")
        if token_input == "__CANCEL__" or not token_input:
            print_warn("Dibatalkan.")
            return False
        token = token_input

        spinner = LoadingSpinner("Verifikasi koneksi...")
        spinner.start()
        fetcher = DeepSeekLiveBackup(token, download_dir="attachments")
        is_valid = fetcher.test_connection()
        if not is_valid:
            spinner.stop("Token tidak valid", status="error")
            print()
            print_info("Pastiin token bener & belum expired. Coba ambil ulang dari DevTools.")
            return False
        spinner.stop("Login sukses, token disimpan (chmod 600)", status="ok")
        save_cached_token(token)

    try:
        return _run_live_backup_flow(fetcher)
    except AuthExpiredError:
        print()
        print_error("Token expired di tengah proses — silakan login ulang.")
        invalidate_cached_token()
        print_info("Token cache udah dihapus. Balik ke menu, pilih [2] lagi buat login.")
        return False


def _run_live_backup_flow(fetcher: DeepSeekLiveBackup) -> bool:
    print_section("Mode Backup", icon="db")
    print_bullet("i  = Incremental — cuma backup obrolan yang ada update (rekomendasi)")
    print_bullet("f  = Full — backup ulang semua obrolan (lebih lambat)")
    print()
    mode_input = _prompt("[i]ncremental (default) / [f]ull", default="i")
    if mode_input == "__CANCEL__":
        print_warn("Dibatalkan.")
        return False

    force_full = mode_input.lower() == "f"
    if force_full:
        print_info("Mode FULL — semua obrolan bakal di-backup ulang")
        fetcher.incremental = False
        fetcher.force_full = True
    else:
        print_info("Mode INCREMENTAL — obrolan tanpa update bakal di-skip")

    sessions = fetcher.fetch_session_list()
    if not sessions:
        print_error("Tidak ada obrolan ditemukan di akun lu.")
        return False

    total_sessions = len(sessions)
    print_section(f"Ditemukan {total_sessions} Obrolan", icon="folder")
    _print_session_list(sessions, limit=30)
    if total_sessions > 30:
        print_info(f"... dan {total_sessions - 30} lainnya")

    print_section("Pilih Obrolan", icon="target")
    print_bullet("1         → backup obrolan #1")
    print_bullet("1,3,5     → backup #1, #3, #5")
    print_bullet("1-5       → backup #1 sampe #5")
    print_bullet("all       → backup SEMUA (rekomendasi)")
    print_bullet("c         → mode checklist interaktif")
    print()

    # FIX: adaptive default — kalo cuma ≤10, default "all"
    default_sel = "all" if total_sessions <= 10 else "1"
    if default_sel == "all":
        print_info(f"Total: {total_sessions} obrolan — default 'all' (backup semua)")
    else:
        print_info(f"Total: {total_sessions} obrolan — default '1' (biar gak kelamaan)")

    raw = _prompt("Pilih obrolan", default=default_sel)

    if raw == "__CANCEL__":
        print_warn("Dibatalkan.")
        return False

    if raw.lower() in ("c", "check", "checklist"):
        selected = interactive_checklist(sessions)
        if not selected:
            print_warn("Gak ada yang dipilih. Balik ke menu.")
            return False
        print_success(f"{len(selected)} obrolan dipilih via checklist:")
        for idx in selected:
            title = sessions[idx].get("title", "Tanpa Judul")
            print_bullet(f'[{idx + 1}] 💬 "{title}"', indent=6)
    else:
        selected = _parse_selection(raw, total_sessions)

    if not selected:
        print_error("Tidak ada obrolan valid yang dipilih.")
        return False

    total_sel = len(selected)
    print_section(f"Menyedot {total_sel} Obrolan", icon="download")
    if total_sel > 1:
        print_info("Progress bakal di-update per obrolan")
    print()

    convo_results = []
    failed = []
    skipped = []
    debug_mode = os.environ.get("GW_DEBUG") == "1"

    for pos, idx in enumerate(selected, 1):
        s = sessions[idx]

        title = s.get("title") or "Tanpa Judul"
        print_section(f'[{pos}/{total_sel}] 💬 "{title}"', icon="ghost")

        session_label = f"— {pos}/{total_sel}"

        try:
            data = fetcher.backup_session(s, debug=debug_mode, session_label=session_label)
        except AuthExpiredError:
            raise

        if data:
            convo_results.append(data)
        elif fetcher.incremental and not force_full:
            skipped.append(s.get("id"))
        else:
            failed.append(s.get("id"))

        if pos < total_sel:
            _session_delay("Pindah ke obrolan berikutnya")

    if not convo_results:
        if skipped:
            print_warn(f"Semua obrolan gak ada update. Skip: {len(skipped)} obrolan.")
        else:
            print_error("Semua obrolan gagal disedot.")
        return False

    os.makedirs(BACKUP_DIR, exist_ok=True)
    if len(convo_results) > 1:
        bulk_name = os.path.join(BACKUP_DIR, "backup_bulk.json")
    else:
        slug = re.sub(r"[^a-z0-9]+", "-", convo_results[0].get("title", "chat").lower()).strip("-")[:40] or "chat"
        bulk_name = os.path.join(BACKUP_DIR, f"backup_{slug}.json")

    with open(bulk_name, "w", encoding="utf-8") as f:
        json.dump(convo_results, f, indent=2, ensure_ascii=False)

    print_section("Hasil Backup", icon="check")
    print_success(f"{len(convo_results)} obrolan tersimpan ke: {bulk_name}")
    if skipped:
        print_warn(f"Skip: {len(skipped)} obrolan (gak ada update)")
    if failed:
        print_error(f"Gagal: {len(failed)} obrolan")

    manifest = fetcher.write_pending_manifest()
    if manifest:
        pending_count = len(set(a["file_name"] for a in fetcher.pending_attachments))
        print()
        print_warn(f"📎 {pending_count} file lampiran perlu taruh manual")
        print_info("DeepSeek blokir download otomatis buat file.")
        print()
        print_bullet(f"Buka: {C.WHITE}attachments/PENDING.md{C.RESET}" if get_theme().enabled else "Buka: attachments/PENDING.md")
        print_bullet("Ikutin langkah-langkahnya (~5 menit)")
        print_bullet("Re-render buat apply lampiran")

    print()
    if _prompt_yes_no("Render ke HTML sekarang?", default="y"):
        _do_render(bulk_name, auto_render_all=True)
    else:
        print_info("Skip render. Balik ke menu.")
    return True

# ============================================================
# RENDER (LOCAL)
# ============================================================

def _do_render(file_path: str, selected_index: int = None, auto_render_all: bool = False):
    """Render convo dari file."""
    try:
        parser = get_parser_for_file(file_path)
    except ValueError as e:
        print_error(str(e))
        return

    if not parser.validate():
        print_error("Validasi file gagal — file korup atau format gak dikenali.")
        return

    convo_list = parser.list_conversations()
    if not convo_list:
        print_error("Tidak ada percakapan di file ini.")
        return

    empty_titles = sum(1 for c in convo_list if not (c.get("title") or "").strip())
    if empty_titles == len(convo_list):
        print_warn(f"Semua {len(convo_list)} obrolan gak punya title. Bakal pake default.")

    if auto_render_all or (selected_index is None and len(convo_list) > 1):
        if len(convo_list) > 1 and not auto_render_all:
            print_section(f"{len(convo_list)} Obrolan dalam File", icon="folder")
            for c in convo_list:
                print_numbered(c["index"] + 1, f'💬 "{c["title"]}"  ·  {c["created_at"] or "No date"}')

            print()
            if _prompt_yes_no(f"Render semua {len(convo_list)} obrolan ke HTML?", default="y"):
                indices_to_render = list(range(len(convo_list)))
            else:
                idx_input = _prompt(f"Pilih [1-{len(convo_list)}]", default="1")
                if idx_input == "__CANCEL__":
                    print_warn("Dibatalkan.")
                    return
                if idx_input.lower() in ("all", "semua", "a"):
                    indices_to_render = list(range(len(convo_list)))
                else:
                    selected = _parse_selection(idx_input, len(convo_list))
                    indices_to_render = selected if selected else [0]
        else:
            indices_to_render = list(range(len(convo_list)))
    elif selected_index is not None:
        indices_to_render = [selected_index]
    else:
        indices_to_render = [0]

    total = len(indices_to_render)
    print_section(f"Render {total} Obrolan", icon="hammer")
    print()

    rendered = []
    failed = []
    skipped_integrity = []

    for pos, idx in enumerate(indices_to_render, 1):
        try:
            convo = convo_list[idx]
        except IndexError:
            continue

        inserted_at = convo.get("inserted_at") or convo.get("created_at_ts")
        convo_id = _generate_convo_id(inserted_at, fallback_offset=pos - 1)

        spinner = LoadingSpinner(f"[{pos}/{total}] Parsing '{convo['title']}'...")
        spinner.start()
        try:
            chat_data = parser.parse(convo_index=idx)
        except Exception as e:
            spinner.stop(f"Gagal parse: {e}", status="error")
            failed.append(convo.get("title", f"#{idx}"))
            continue
        spinner.stop(f"Parsed: '{chat_data.get('title')}' - {len(chat_data.get('messages', []))} pesan")

        is_valid, errors, warnings = _validate_chat_data(
            chat_data, convo_label=chat_data.get("title") or convo.get("title", f"#{idx}")
        )

        for w in warnings:
            # FIX: ganti icon warn jadi info buat pesan kosong
            if "tanpa teks" in w:
                t = get_theme()
                if t.enabled:
                    print(f"  {C.ACCENT}ℹ{C.RESET}  {C.GRAY}{w}{C.RESET}")
                else:
                    print(f"  ℹ  {w}")
            else:
                print_warn(f"  {w}")

        if not is_valid:
            print_error(f"  Integrity check GAGAL — skip render:")
            for err in errors:
                print_error(f"    - {err}")
            skipped_integrity.append(chat_data.get("title") or convo.get("title", f"#{idx}"))
            continue

        output_path = os.path.join(PUBLIC_DIR, HISTORY_SUBDIR, convo_id, "index.html")

        spinner = LoadingSpinner("Inject HTML template...")
        spinner.start()
        try:
            exporter = HTMLExporter(template_dir="templates", template_name="viewer.html")
            final_path = exporter.export(
                chat_data,
                output_path,
                convo_count=len(convo_list),
                convo_id=convo_id,
            )
        except Exception as e:
            spinner.stop(f"Gagal render: {e}", status="error")
            failed.append(chat_data.get("title", f"#{idx}"))
            continue
        spinner.stop("Render selesai")

        att_total, att_missing = _check_attachments_in_html(final_path)
        if att_total > 0 and att_missing > 0:
            print_warn(f"  📎 {att_missing}/{att_total} lampiran gak ke-resolve (baca attachments/PENDING.md)")

        rendered.append({
            "id": convo_id,
            "title": chat_data.get("title", "Tanpa Judul"),
            "messages": len(chat_data.get("messages", [])),
            "path": final_path,
        })
        print()

    print_section("Render Selesai", icon="check")
    if rendered:
        print_success(f"{len(rendered)} obrolan berhasil di-render")
    if skipped_integrity:
        print_warn(f"{len(skipped_integrity)} obrolan di-skip (integrity check gagal): {', '.join(skipped_integrity)}")
    if failed:
        print_error(f"{len(failed)} gagal: {', '.join(failed)}")

    if not rendered:
        return

    print()
    print_info("Daftar obrolan:")
    for r in rendered:
        print_bullet(f'💬 "{r["title"]}"  ({r["messages"]} pesan)  →  {r["id"]}', indent=6)

    print()
    _print_post_render_hint()


def _print_post_render_hint():
    """Hint setelah render selesai - next step konkret."""
    t = get_theme()
    if t.enabled:
        print(f"  {C.ACCENT_DIM}{'─' * 56}{C.RESET}")
        print(f"  {C.GREEN}✅{C.RESET}  {C.WHITE}Render selesai! Hasilnya bisa dibuka di browser.{C.RESET}")
        print()
        print(f"  {C.WHITE}Cara buka:{C.RESET}")
        print(f"  {C.ACCENT_DIM}1.{C.RESET} {C.GRAY}Buka terminal baru (atau Ctrl+C di sini){C.RESET}")
        print(f"  {C.ACCENT_DIM}2.{C.RESET} {C.GRAY}Jalanin: {C.ACCENT}python3 serve.py{C.RESET}")
        print(f"  {C.ACCENT_DIM}3.{C.RESET} {C.GRAY}Browser kebuka otomatis{C.RESET}")
        print()
        print(f"  {C.GRAY}Baca panduan lengkap: menu {C.ACCENT}[3] Tutorial{C.RESET}")
        print(f"  {C.ACCENT_DIM}{'─' * 56}{C.RESET}")
    else:
        print("  " + "─" * 56)
        print("  ✅  Render selesai! Hasilnya bisa dibuka di browser.")
        print()
        print("  Cara buka:")
        print("  1. Buka terminal baru (atau Ctrl+C di sini)")
        print("  2. Jalanin: python3 serve.py")
        print("  3. Browser kebuka otomatis")
        print()
        print("  Baca panduan lengkap: menu [3] Tutorial")
        print("  " + "─" * 56)


def handle_local_render() -> bool:
    files = scan_local_dump_files()
    if not files:
        print_warn("Gak ada file .json / .md / .docx di folder ini.")
        print()
        print_info("Taruh file backup chat lu di folder ini dulu.")
        print_info("Atau kasih path manual kalo file-nya di tempat lain.")
        print()
        file_path = _prompt("Path file manual")
        if file_path == "__CANCEL__" or not file_path:
            print_warn("Dibatalkan.")
            return False
    else:
        print_section(f"Ditemukan {len(files)} File Siap Render", icon="folder")
        for idx, f in enumerate(files, 1):
            size_kb = os.path.getsize(f) / 1024
            print_numbered(idx, f"{f}  ({size_kb:.1f} KB)")
        print_numbered(len(files) + 1, "Input path manual")

        pilih = _prompt(f"Pilih file [1-{len(files) + 1}]", default="1")
        if pilih == "__CANCEL__":
            print_warn("Dibatalkan.")
            return False
        if not pilih:
            file_path = files[0]
        elif pilih.isdigit() and 1 <= int(pilih) <= len(files):
            file_path = files[int(pilih) - 1]
        else:
            file_path = _prompt("Path file manual")
            if file_path == "__CANCEL__" or not file_path:
                print_warn("Dibatalkan.")
                return False

    if not os.path.exists(file_path):
        print_error(f"File tidak ditemukan: {file_path}")
        return False

    _do_render(file_path)
    return True


# ============================================================
# TUTORIAL & PANDUAN (Menu [3]) — UPGRADED
# ============================================================

def handle_tutorial():
    """Tampilkan tutorial lengkap — versi upgrade user-friendly."""
    _clear_screen()
    t = get_theme()

    def _header(title: str):
        if t.enabled:
            print(f"{C.ACCENT_DIM}{'─' * 58}{C.RESET}")
            print(f"  {C.BOLD}{C.WHITE}{title}{C.RESET}")
            print(f"{C.ACCENT_DIM}{'─' * 58}{C.RESET}")
        else:
            print("─" * 58)
            print(f"  {title}")
            print("─" * 58)

    def _section(title: str, icon: str = "✦"):
        print()
        if t.enabled:
            print(f"{C.ACCENT}{'─' * 58}{C.RESET}")
            print(f"  {C.BOLD}{C.WHITE}{icon}  {title}{C.RESET}")
            print(f"{C.ACCENT}{'─' * 58}{C.RESET}")
        else:
            print("─" * 58)
            print(f"  {icon}  {title}")
            print("─" * 58)

    def _line(text: str, indent: int = 2):
        print(" " * indent + text)

    def _cmd(text: str, indent: int = 6):
        if t.enabled:
            print(" " * indent + f"{C.GREEN}{text}{C.RESET}")
        else:
            print(" " * indent + text)

    def _hint(text: str, indent: int = 2):
        if t.enabled:
            print(" " * indent + f"{C.YELLOW}{text}{C.RESET}")
        else:
            print(" " * indent + text)

    def _info(text: str, indent: int = 2):
        if t.enabled:
            print(" " * indent + f"{C.ACCENT}ℹ{C.RESET}  {C.GRAY}{text}{C.RESET}")
        else:
            print(" " * indent + f"ℹ  {text}")

    # ============================================================
    # HEADER
    # ============================================================
    _header("📖  TUTORIAL & PANDUAN — GhostWriter")
    print()
    _line("Selamat datang di GhostWriter! 👻")
    _line("Panduan ini bakal ngebantu lu dari nol sampe bisa buka viewer.")
    print()
    if t.enabled:
        print(f"  {C.GRAY}💡 Baru pake? Baca {C.WHITE}QUICK START{C.RESET} {C.GRAY}di bawah.{C.RESET}")
        print(f"  {C.GRAY}💡 Udah jalan, cuma butuh fitur? Skip ke {C.WHITE}TIPS & TRIK{C.RESET}{C.GRAY}.{C.RESET}")

    # ============================================================
    # SECTION 1 — QUICK START (BARU)
    # ============================================================
    _section("QUICK START", icon="⚡")

    print()
    _line("3 langkah — kurang dari 30 detik:")
    print()
    if t.enabled:
        print(f"  {C.ACCENT_DIM}1.{C.RESET} {C.WHITE}Render file backup lu{C.RESET}")
        print(f"     {C.GRAY}Dari menu utama, pilih {C.ACCENT}[1]{C.RESET}")
    else:
        print("  1. Render file backup lu")
        print("     Dari menu utama, pilih [1]")
    print()
    if t.enabled:
        print(f"  {C.ACCENT_DIM}2.{C.RESET} {C.WHITE}Jalanin server lokal{C.RESET}")
        _cmd("python3 serve.py")
    else:
        print("  2. Jalanin server lokal")
        print("     python3 serve.py")
    print()
    if t.enabled:
        print(f"  {C.ACCENT_DIM}3.{C.RESET} {C.WHITE}Buka di browser{C.RESET}")
        _cmd("http://localhost:8000/")
    else:
        print("  3. Buka di browser")
        print("     http://localhost:8000/")
    print()
    _hint("💡 serve.py bakal nanya \"buka browser sekarang?\" — ketik Y.")
    _info("Kalo error, lompat ke TROUBLESHOOTING di bawah.")

    # ============================================================
    # SECTION 2 — CARA BUKA DI BROWSER
    # ============================================================
    _section("CARA BUKA DI BROWSER", icon="🌐")

    print()
    _line("Kenapa butuh server?")
    _line("Viewer GhostWriter fetch index.json & asset lewat HTTP.", indent=4)
    _line("Kalo buka langsung file HTML (file://), bakal error.", indent=4)
    print()
    _line("Step detail:")
    print()
    _cmd("python3 serve.py", indent=4)
    print()
    _line("Terus buka browser ke salah satu:", indent=4)
    _cmd("• Chrome / Firefox / Edge", indent=6)
    _cmd("• http://localhost:8000/", indent=6)
    print()
    _info("Ganti port: python3 serve.py --port 8080")

    # ============================================================
    # SECTION 3 — KEYBOARD SHORTCUTS
    # ============================================================
    _section("KEYBOARD SHORTCUTS", icon="⌨️")

    print()
    if t.enabled:
        shortcuts = [
            ("?", "Buka panel keyboard shortcuts"),
            ("/", "Fokus ke search box"),
            ("j / k", "Navigate pesan berikutnya / sebelumnya"),
            ("Home", "Scroll ke paling atas"),
            ("End", "Scroll ke paling bawah"),
            ("Esc", "Tutup sidebar / right rail / modal"),
        ]
        for key, desc in shortcuts:
            print(f"  {C.ACCENT}{key:<10}{C.RESET} {C.WHITE}{desc}{C.RESET}")
    else:
        shortcuts = [
            ("?", "Buka panel keyboard shortcuts"),
            ("/", "Fokus ke search box"),
            ("j / k", "Navigate pesan berikutnya / sebelumnya"),
            ("Home", "Scroll ke paling atas"),
            ("End", "Scroll ke paling bawah"),
            ("Esc", "Tutup sidebar / right rail / modal"),
        ]
        for key, desc in shortcuts:
            print(f"  {key:<10} {desc}")
    print()
    _info("Tekan ? di viewer buat liat semua shortcut")

    # ============================================================
    # SECTION 4 — TROUBLESHOOTING (DI-GROUP)
    # ============================================================
    _section("TROUBLESHOOTING", icon="❓")

    # --- Group 1: Error Umum ---
    print()
    if t.enabled:
        print(f"  {C.RED}🔴 Error Umum{C.RESET}")
        print(f"  {C.ACCENT_DIM}{'─' * 54}{C.RESET}")
    else:
        print("  🔴 Error Umum")
        print("  " + "─" * 54)

    print()
    _hint("Q: Error \"fetch index.json failed\"?")
    _line("A: Pastiin lu akses via http://localhost:8000/,", indent=4)
    _line("   bukan file://path/to/file.html", indent=4)
    print()
    _hint("Q: Port 8000 udah dipake?")
    _line("A: Ganti port: python3 serve.py --port 8080", indent=4)
    _line("   Atau kill proses lama: lsof -ti:8000 | xargs kill", indent=4)
    print()
    _hint("Q: Token expired terus-terusan?")
    _line("A: GhostWriter auto-invalidate token cache.", indent=4)
    _line("   Login ulang pake token baru dari DevTools.", indent=4)

    # --- Group 2: Fitur Gak Jalan ---
    print()
    if t.enabled:
        print(f"  {C.YELLOW}🟡 Fitur Gak Jalan{C.RESET}")
        print(f"  {C.ACCENT_DIM}{'─' * 54}{C.RESET}")
    else:
        print("  🟡 Fitur Gak Jalan")
        print("  " + "─" * 54)

    print()
    _hint("Q: Convo gak muncul di landing page?")
    _line("A: Jalanin sync: python3 sync.py", indent=4)
    print()
    _hint("Q: Lampiran gak ke-render?")
    _line("A: Buka attachments/PENDING.md — ikutin langkahnya.", indent=4)
    _line("   DeepSeek blokir download otomatis buat file.", indent=4)
    print()
    _hint("Q: Viewer blank / putih doang?")
    _line("A: Cek Console (F12) — biasanya CORS atau JS error.", indent=4)
    _line("   Pastiin akses via http://localhost:8000/", indent=4)

    # ============================================================
    # SECTION 5 — TIPS & TRIK (BARU)
    # ============================================================
    _section("TIPS & TRIK", icon="💡")

    print()
    if t.enabled:
        tips = [
            ("Render 1 obrolan doang",
             'python3 main.py backup.json --chat-index 0'),
            ("Render semua obrolan di file",
             'python3 main.py backup.json --all'),
            ("Ganti port server",
             'python3 serve.py --port 8080'),
            ("Sync index tanpa render ulang",
             'python3 sync.py'),
            ("Debug mode (kalo ada error)",
             'GW_DEBUG=1 python3 main.py'),
            ("Ganti delay backup (anti-suspend)",
             'GW_DELAY_MIN=2 GW_DELAY_MAX=4 python3 main.py'),
        ]
        for i, (desc, cmd) in enumerate(tips, 1):
            print(f"  {C.ACCENT_DIM}{i}.{C.RESET} {C.WHITE}{desc}{C.RESET}")
            print(f"     {C.GREEN}{cmd}{C.RESET}")
            print()
    else:
        tips = [
            ("Render 1 obrolan doang",
             'python3 main.py backup.json --chat-index 0'),
            ("Render semua obrolan di file",
             'python3 main.py backup.json --all'),
            ("Ganti port server",
             'python3 serve.py --port 8080'),
            ("Sync index tanpa render ulang",
             'python3 sync.py'),
            ("Debug mode (kalo ada error)",
             'GW_DEBUG=1 python3 main.py'),
            ("Ganti delay backup (anti-suspend)",
             'GW_DELAY_MIN=2 GW_DELAY_MAX=4 python3 main.py'),
        ]
        for i, (desc, cmd) in enumerate(tips, 1):
            print(f"  {i}. {desc}")
            print(f"     {cmd}")
            print()

    # ============================================================
    # FOOTER
    # ============================================================
    print()
    if t.enabled:
        print(f"{C.ACCENT_DIM}{'─' * 58}{C.RESET}")
        print(f"  {C.GRAY}Butuh bantuan lain?{C.RESET}")
        print(f"  {C.GRAY}• Menu utama: {C.WHITE}[Enter]{C.RESET} {C.GRAY}balik{C.RESET}")
        print(f"  {C.GRAY}• Baca ulang: {C.WHITE}[3]{C.RESET} {C.GRAY}dari menu utama{C.RESET}")
        print(f"  {C.GRAY}• Report bug: {C.ACCENT}github.com/nexterade/GhostWriter{C.RESET}")
        print(f"{C.ACCENT_DIM}{'─' * 58}{C.RESET}")
    else:
        print("─" * 58)
        print("  Butuh bantuan lain?")
        print("  • Menu utama: [Enter] balik")
        print("  • Baca ulang: [3] dari menu utama")
        print("  • Report bug: github.com/nexterade/GhostWriter")
        print("─" * 58)

    print()
    input(f"  {C.GRAY if t.enabled else ''}[Enter] buat balik ke menu...{C.RESET if t.enabled else ''}")


# ============================================================
# MENU UTAMA — User-Friendly (Nomor + Context)
# ============================================================

def print_main_menu():
    """
    Menu utama GhostWriter — design Soft & Friendly.

    Layout:
        Header: emoji + title + garis horizontal
        Items : [N] ▸ label — hint
        Footer: context line (file, convo, jam)
        Prompt: siap di bawah

    FIX v2.4.0: Tambah nomor [N] di setiap item biar match sama input.
    """
    t = get_theme()
    ctx = _get_menu_context()

    bullet = "▸" if t.unicode else ">"
    sep = "─"

    if t.enabled:
        print()
        print(f"  {C.BOLD}{C.WHITE}👻  GhostWriter — Menu Utama{C.RESET}")
        print(f"  {C.ACCENT_DIM}{sep * 55}{C.RESET}")
        print()
        print(f"  {C.ACCENT}[1]{C.RESET} {C.ACCENT}{bullet}{C.RESET}  {C.WHITE}Render backup lokal{C.RESET}")
        print(f"       {C.GRAY}Baca .json / .md / .docx offline{C.RESET}")
        print()
        print(f"  {C.ACCENT}[2]{C.RESET} {C.ACCENT}{bullet}{C.RESET}  {C.WHITE}Sedot live dari DeepSeek{C.RESET}")
        print(f"       {C.GRAY}Tarik obrolan dari akun DeepSeek lu{C.RESET}")
        print()
        print(f"  {C.ACCENT}[3]{C.RESET} {C.ACCENT}{bullet}{C.RESET}  {C.WHITE}Tutorial & Panduan{C.RESET}")
        print(f"       {C.GRAY}Panduan lengkap + troubleshooting{C.RESET}")
        print()
        print(f"  {C.GRAY}[0]{C.RESET} {C.GRAY}{bullet}{C.RESET}  {C.GRAY}Keluar{C.RESET}")
        print()

        # === FOOTER CONTEXT ===
        print(f"  {C.ACCENT_DIM}{sep * 55}{C.RESET}")
        ctx_parts = []
        if ctx["files_count"] > 0:
            ctx_parts.append(
                f"{C.GRAY}📁{C.RESET} {C.WHITE}{ctx['files_count']}{C.RESET} {C.GRAY}file siap render{C.RESET}"
            )
            ctx_parts.append(
                f"{C.GRAY}💾{C.RESET} {C.WHITE}{_format_size(ctx['files_size'])}{C.RESET}"
            )
        if ctx["convo_count"] > 0:
            ctx_parts.append(
                f"{C.GRAY}📚{C.RESET} {C.WHITE}{ctx['convo_count']}{C.RESET} {C.GRAY}obrolan dirender{C.RESET}"
            )
        ctx_parts.append(
            f"{C.GRAY}🕐{C.RESET} {C.WHITE}{_format_clock()}{C.RESET}"
        )

        print("  " + f"  {C.GRAY_DIM}·{C.RESET}  ".join(ctx_parts))

        if ctx["has_legacy_dist"]:
            print(f"  {C.YELLOW}⚠{C.RESET}  {C.GRAY}Folder {C.WHITE}dist/{C.RESET} {C.GRAY}legacy — hapus manual: {C.ACCENT}rm -rf dist/{C.RESET}")

        if ctx["files_count"] == 0:
            print(f"  {C.YELLOW}💡{C.RESET}  {C.GRAY}Taruh {C.WHITE}.json / .md / .docx{C.RESET} {C.GRAY}di folder ini buat mulai.{C.RESET}")

        print(f"  {C.ACCENT_DIM}{sep * 55}{C.RESET}")
    else:
        print()
        print("  👻  GhostWriter — Menu Utama")
        print("  " + sep * 55)
        print()
        print(f"  [1] {bullet}  Render backup lokal")
        print(f"       Baca .json / .md / .docx offline")
        print()
        print(f"  [2] {bullet}  Sedot live dari DeepSeek")
        print(f"       Tarik obrolan dari akun DeepSeek lu")
        print()
        print(f"  [3] {bullet}  Tutorial & Panduan")
        print(f"       Panduan lengkap + troubleshooting")
        print()
        print(f"  [0] {bullet}  Keluar")
        print()
        print("  " + sep * 55)

        ctx_parts = []
        if ctx["files_count"] > 0:
            ctx_parts.append(f"📁 {ctx['files_count']} file siap render")
            ctx_parts.append(f"💾 {_format_size(ctx['files_size'])}")
        if ctx["convo_count"] > 0:
            ctx_parts.append(f"📚 {ctx['convo_count']} obrolan dirender")
        ctx_parts.append(f"🕐 {_format_clock()}")
        print("  " + "  ·  ".join(ctx_parts))

        if ctx["has_legacy_dist"]:
            print("  ⚠  Folder dist/ legacy — hapus manual: rm -rf dist/")
        if ctx["files_count"] == 0:
            print("  💡 Taruh .json / .md / .docx di folder ini buat mulai.")
        print("  " + sep * 55)


def _wait_enter():
    t = get_theme()
    if t.enabled:
        input(f"\n  {C.GRAY}[Enter] buat balik ke menu...{C.RESET}")
    else:
        input("\n  [Enter] buat balik ke menu...")


# ============================================================
# FIX #3: WRAPPER — Try/Except per Handler
# ============================================================

def _safe_run(handler_fn, handler_name: str, **kwargs) -> bool:
    """FIX #3: Jalankan handler dengan try/except comprehensive."""
    try:
        result = handler_fn(**kwargs)
        return bool(result) if result is not None else True

    except AuthExpiredError:
        print()
        print_error(f"{handler_name} gagal: token expired.")
        invalidate_cached_token()
        print_info("Token cache udah dihapus. Login ulang di menu [2].")
        return False

    except KeyboardInterrupt:
        print()
        print_warn(f"{handler_name} di-cancel (Ctrl+C).")
        return False

    except Exception as e:
        print()
        print_error(f"{handler_name} error: {type(e).__name__}: {e}")

        if os.environ.get("GW_DEBUG") == "1":
            print()
            print_warn("Debug mode: full traceback")
            traceback.print_exc()

        print()
        print_info("Error udah di-handle. Balik ke menu utama.")
        return False


def run_wizard():
    print_banner()
    print_status(f"Wizard Mode GhostWriter — by {AUTHOR}", status="ghost")
    print_info("Ketik '0' di prompt manapun buat batal")

    while True:
        print_main_menu()
        # FIX: default = "0" (keluar) — safe default
        pilihan = _prompt("Pilih menu [0-3]", default="0")

        if pilihan == "__CANCEL__" or pilihan in ("0", "q", "quit", "exit", "keluar"):
            print_status("Sampai jumpa, bre. Data lu aman di lokal.", status="ghost")
            break

        if pilihan == "1":
            _safe_run(handle_local_render, "Render lokal")
            _wait_enter()
        elif pilihan == "2":
            _safe_run(handle_live_deepseek_backup, "Live Backup")
            _wait_enter()
        elif pilihan == "3":
            _safe_run(handle_tutorial, "Tutorial")
        else:
            print_warn(f"Pilihan '{pilihan}' gak valid. Pilih [0-3].")


# ============================================================
# CLI MODE
# ============================================================

def main():
    if len(sys.argv) == 1:
        try:
            run_wizard()
        except KeyboardInterrupt:
            print()
            print_status("Ctrl+C - keluar.", status="warn")
            sys.exit(0)
        return

    parser = argparse.ArgumentParser(
        prog="GhostWriter",
        description="GhostWriter 👻📜 - Konversi arsip obrolan AI jadi web interaktif."
    )
    parser.add_argument("input_file", help="File backup (.json, .md, .docx)")
    parser.add_argument("--chat-index", type=int, default=None, help="Indeks obrolan (0-based, default: render semua)")
    parser.add_argument("--all", action="store_true", help="Render semua convo dalam file")

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print_error(f"File tidak ditemukan: {args.input_file}")
        sys.exit(1)

    if args.all:
        _do_render(args.input_file, auto_render_all=True)
    else:
        _do_render(args.input_file, selected_index=args.chat_index)


if __name__ == "__main__":
    main()
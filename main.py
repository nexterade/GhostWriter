import sys
import os
import time
import glob
import json
import re
import argparse
from parsers.json_parser import JSONChatParser
from parsers.md_parser import MarkdownChatParser
from parsers.docx_parser import DocxChatParser
from exporter import HTMLExporter
from tools.deepseek_backup import DeepSeekLiveBackup, _session_delay
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


def _generate_convo_id(inserted_at, fallback_offset: int = 0) -> str:
    """
    Generate ID unik untuk convo.
    Prioritas: inserted_at (Unix epoch) -> fallback time.time() + offset.
    """
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
    view = sessions[:limit] if limit else sessions
    for idx, s in enumerate(view, 1):
        ins = s.get("inserted_at")
        ins_str = _format_epoch(ins)
        title = s.get("title") or "Tanpa Judul"
        print_numbered(idx, f"{title}  ({ins_str})")


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
    """
    PR-40: Validasi chat_data setelah parse.

    Return: (is_valid: bool, errors: list, warnings: list)
    """
    errors = []
    warnings = []
    label = f"'{convo_label}'" if convo_label else "convo"

    if not isinstance(chat_data, dict):
        errors.append(f"{label}: hasil parse bukan dict (got {type(chat_data).__name__})")
        return False, errors, warnings

    # 1. Title gak boleh kosong
    title = (chat_data.get("title") or "").strip()
    if not title:
        warnings.append(f"{label}: title kosong, bakal pake default 'Tanpa Judul'")

    # 2. Messages harus list
    messages = chat_data.get("messages")
    if not isinstance(messages, list):
        errors.append(f"{label}: 'messages' bukan list (got {type(messages).__name__})")
        return False, errors, warnings

    # 3. Messages gak boleh kosong
    if len(messages) == 0:
        errors.append(f"{label}: 0 pesan — file mungkin korup atau schema beda")
        return False, errors, warnings

    # 4. Tiap message harus punya role & content valid
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
        warnings.append(
            f"{label}: {invalid_msgs} pesan dengan role invalid (bukan user/assistant/system)"
        )

    if empty_content > 0:
        warnings.append(
            f"{label}: {empty_content} pesan dengan content kosong"
        )

    # Kalo > 50% message kosong, anggap error (kemungkinan parse gagal)
    if empty_content > len(messages) / 2:
        errors.append(
            f"{label}: >50% pesan kosong ({empty_content}/{len(messages)}) — parse kemungkinan gagal"
        )
        return False, errors, warnings

    return True, errors, warnings


def _check_attachments_in_html(html_path: str) -> tuple:
    """
    PR-40: Cek attachment base64 di HTML — apakah file fisiknya ada.

    Return: (total, missing) — jumlah attachment total & yang ilang.
    """
    if not os.path.isfile(html_path):
        return 0, 0

    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return 0, 0

    # Cari attachment-box yang class-nya "missing" (kalo ada)
    # Attachment yang gak punya file fisik biasanya ditandai class "missing"
    # di template, atau gak ada <img> di dalamnya
    total = len(re.findall(r'class="attachment-box', content))
    missing = len(re.findall(r'class="attachment-box missing', content))

    return total, missing


# ============================================================
# LIVE BACKUP
# ============================================================

def handle_live_deepseek_backup() -> bool:
    print_section("Live Backup DeepSeek", icon="rocket")
    print_info("Ketik '0' di prompt mana aja buat batal & balik ke menu")

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

    if not token:
        print_section("Cara Ambil Token", icon="key")
        print_numbered(1, "Buka DevTools (F12) -> Application -> Local Storage")
        print_numbered(2, "Cari key 'userToken', salin value-nya")

        token_input = _prompt("User Token DeepSeek")
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
            return False
        spinner.stop("Login sukses, token disimpan (chmod 600)", status="ok")
        save_cached_token(token)

    print_section("Mode Backup", icon="db")
    mode_input = _prompt("[i]ncremental (default) / [f]ull", default="i")
    if mode_input == "__CANCEL__":
        print_warn("Dibatalkan.")
        return False

    force_full = mode_input.lower() == "f"
    if force_full:
        print_info("Mode FULL - semua sesi di-backup ulang")
        fetcher.incremental = False
        fetcher.force_full = True
    else:
        print_info("Mode INCREMENTAL - sesi tanpa update bakal di-skip")

    sessions = fetcher.fetch_session_list()
    if not sessions:
        print_error("Tidak ada obrolan ditemukan.")
        return False

    print_section(f"Ditemukan {len(sessions)} Obrolan", icon="folder")
    _print_session_list(sessions, limit=30)
    if len(sessions) > 30:
        print_info(f"... dan {len(sessions) - 30} lainnya")

    print_section("Pilih Sesi", icon="target")
    print_bullet("'1' | '1,3,5' | '1-5' - pilih manual")
    print_bullet("'all' - pilih semua")
    print_bullet("'c' / 'check' - mode checklist interaktif")
    raw = _prompt("Mau backup yang mana?", default="1")

    if raw == "__CANCEL__":
        print_warn("Dibatalkan.")
        return False

    if raw.lower() in ("c", "check", "checklist"):
        selected = interactive_checklist(sessions)
        if not selected:
            print_warn("Gak ada yang dipilih. Balik ke menu.")
            return False
        print_success(f"{len(selected)} sesi dipilih via checklist:")
        for idx in selected:
            print_bullet(f"[{idx + 1}] {sessions[idx].get('title', 'Tanpa Judul')}", indent=6)
    else:
        selected = _parse_selection(raw, len(sessions))

    if not selected:
        print_error("Tidak ada sesi valid yang dipilih.")
        return False

    total_sel = len(selected)
    print_section(f"Menyedot {total_sel} Sesi", icon="download")
    if total_sel > 1:
        print_info("Progress bakal di-update per sesi")
    print()

    convo_results = []
    failed = []
    skipped = []
    debug_mode = os.environ.get("GW_DEBUG") == "1"

    for pos, idx in enumerate(selected, 1):
        s = sessions[idx]

        title = s.get("title") or "Tanpa Judul"
        print_section(f"[{pos}/{total_sel}] {title}", icon="ghost")

        session_label = f"- Sesi {pos}/{total_sel}"
        data = fetcher.backup_session(s, debug=debug_mode, session_label=session_label)
        if data:
            convo_results.append(data)
        elif fetcher.incremental and not force_full:
            skipped.append(s.get("id"))
        else:
            failed.append(s.get("id"))

        if pos < total_sel:
            _session_delay("Pindah ke sesi berikutnya")

    if not convo_results:
        if skipped:
            print_warn(f"Semua sesi gak ada update. Skip: {len(skipped)} sesi.")
        else:
            print_error("Semua sesi gagal disedot.")
        return False

    # Simpan dump JSON ke backups/ (BUKAN di root)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if len(convo_results) > 1:
        bulk_name = os.path.join(BACKUP_DIR, "backup_bulk.json")
    else:
        slug = re.sub(r"[^a-z0-9]+", "-", convo_results[0].get("title", "chat").lower()).strip("-")[:40] or "chat"
        bulk_name = os.path.join(BACKUP_DIR, f"backup_{slug}.json")

    with open(bulk_name, "w", encoding="utf-8") as f:
        json.dump(convo_results, f, indent=2, ensure_ascii=False)

    print_section("Hasil Backup", icon="check")
    print_success(f"{len(convo_results)} sesi tersimpan ke: {bulk_name}")
    if skipped:
        print_warn(f"Skip: {len(skipped)} sesi (gak ada update)")
    if failed:
        print_error(f"Gagal: {len(failed)} sesi -> {failed}")

    manifest = fetcher.write_pending_manifest()
    if manifest:
        pending_count = len(set(a["file_name"] for a in fetcher.pending_attachments))
        print_warn(f"{pending_count} attachment pending - lihat: {manifest}")

    # Tanya render (sekali aja)
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
    """
    Render convo dari file.

    Args:
        file_path: path file .json/.md/.docx
        selected_index: index convo (kalo cuma mau 1)
        auto_render_all: render semua convo tanpa tanya (buat bulk)
    """
    try:
        parser = get_parser_for_file(file_path)
    except ValueError as e:
        print_error(str(e))
        return

    # === PR-40: Validate parser ===
    if not parser.validate():
        print_error("Validasi file gagal — file korup atau format gak dikenali.")
        return

    convo_list = parser.list_conversations()
    if not convo_list:
        print_error("Tidak ada percakapan di file ini.")
        return

    # === PR-40: Validate convo list ===
    empty_titles = sum(1 for c in convo_list if not (c.get("title") or "").strip())
    if empty_titles == len(convo_list):
        print_warn(f"Semua {len(convo_list)} convo gak punya title. Bakal pake default.")

    # Tentukan convo yang mau di-render
    if auto_render_all or (selected_index is None and len(convo_list) > 1):
        if len(convo_list) > 1 and not auto_render_all:
            print_section(f"{len(convo_list)} Sesi dalam File", icon="folder")
            for c in convo_list:
                print_numbered(c["index"] + 1, f"{c['title']}  ({c['created_at'] or 'No date'})")

            print()
            if _prompt_yes_no(f"Render semua {len(convo_list)} sesi ke HTML?", default="y"):
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
    print_section(f"Render {total} Sesi", icon="hammer")
    print()

    rendered = []
    failed = []
    skipped_integrity = []

    for pos, idx in enumerate(indices_to_render, 1):
        try:
            convo = convo_list[idx]
        except IndexError:
            continue

        # Generate ID unik
        inserted_at = convo.get("inserted_at") or convo.get("created_at_ts")
        convo_id = _generate_convo_id(inserted_at, fallback_offset=pos - 1)

        # Parse
        spinner = LoadingSpinner(f"[{pos}/{total}] Parsing '{convo['title']}'...")
        spinner.start()
        try:
            chat_data = parser.parse(convo_index=idx)
        except Exception as e:
            spinner.stop(f"Gagal parse: {e}", status="error")
            failed.append(convo.get("title", f"#{idx}"))
            continue
        spinner.stop(f"Parsed: '{chat_data.get('title')}' - {len(chat_data.get('messages', []))} pesan")

        # === PR-40: Integrity check ===
        is_valid, errors, warnings = _validate_chat_data(
            chat_data, convo_label=chat_data.get("title") or convo.get("title", f"#{idx}")
        )

        for w in warnings:
            print_warn(f"  {w}")

        if not is_valid:
            print_error(f"  Integrity check GAGAL — skip render:")
            for err in errors:
                print_error(f"    - {err}")
            skipped_integrity.append(chat_data.get("title") or convo.get("title", f"#{idx}"))
            continue

        # Output path: public/history/<id>/index.html
        output_path = os.path.join(PUBLIC_DIR, HISTORY_SUBDIR, convo_id, "index.html")

        # Render
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

        # === PR-40: Check attachment di HTML ===
        att_total, att_missing = _check_attachments_in_html(final_path)
        if att_total > 0 and att_missing > 0:
            print_warn(f"  {att_missing}/{att_total} attachment ilang (liat attachments/PENDING.md)")

        rendered.append({
            "id": convo_id,
            "title": chat_data.get("title", "Tanpa Judul"),
            "messages": len(chat_data.get("messages", [])),
            "path": final_path,
        })
        print()

    # Summary
    print_section("Render Selesai", icon="check")
    if rendered:
        print_success(f"{len(rendered)} convo berhasil di-render")
    if skipped_integrity:
        print_warn(f"{len(skipped_integrity)} convo di-skip (integrity check gagal): {', '.join(skipped_integrity)}")
    if failed:
        print_error(f"{len(failed)} gagal: {', '.join(failed)}")

    if not rendered:
        return

    print()
    print_info("Daftar convo:")
    for r in rendered:
        print_bullet(f"{r['title']}  ({r['messages']} pesan)  ->  {r['id']}", indent=6)

    # Hint ke tutorial
    print()
    _print_post_render_hint()


def _print_post_render_hint():
    """Hint setelah render selesai - arahin user ke menu [3]."""
    t = get_theme()
    if t.enabled:
        print(f"  {C.ACCENT}={('=' * 50)}={C.RESET}")
        print(f"  {C.YELLOW}💡{C.RESET} {C.WHITE}Belum tau cara buka di browser?{C.RESET}")
        print(f"     {C.GRAY}-> Balik ke menu, pilih {C.ACCENT}[3] Tutorial & Panduan{C.RESET}")
        print(f"  {C.ACCENT}={('=' * 50)}={C.RESET}")
    else:
        print("  ==================================================")
        print("  💡 Belum tau cara buka di browser?")
        print("     -> Balik ke menu, pilih [3] Tutorial & Panduan")
        print("  ==================================================")


def handle_local_render() -> bool:
    files = scan_local_dump_files()
    if not files:
        print_warn("Gak ada file .json/.md/.docx di root.")
        file_path = _prompt("Path file backup manual")
        if file_path == "__CANCEL__" or not file_path:
            print_warn("Dibatalkan.")
            return False
    else:
        print_section(f"Ditemukan {len(files)} File", icon="folder")
        for idx, f in enumerate(files, 1):
            size_kb = os.path.getsize(f) / 1024
            print_numbered(idx, f"{f}  ({size_kb:.1f} KB)")
        print_numbered(len(files) + 1, "Input path manual")

        pilih = _prompt(f"Pilih [1-{len(files) + 1}]", default="1")
        if pilih == "__CANCEL__":
            print_warn("Dibatalkan.")
            return False
        if not pilih:
            file_path = files[0]
        elif pilih.isdigit() and 1 <= int(pilih) <= len(files):
            file_path = files[int(pilih) - 1]
        else:
            file_path = _prompt("Path file backup manual")
            if file_path == "__CANCEL__" or not file_path:
                print_warn("Dibatalkan.")
                return False

    if not os.path.exists(file_path):
        print_error(f"File tidak ditemukan: {file_path}")
        return False

    _do_render(file_path)
    return True


# ============================================================
# TUTORIAL (Menu [3])
# ============================================================

def handle_tutorial():
    """Tampilkan tutorial lengkap."""
    _clear_screen()
    t = get_theme()

    def _header(title: str):
        if t.enabled:
            print(f"{C.ACCENT}{'=' * 56}{C.RESET}")
            print(f"  {C.BOLD}{C.WHITE}{title}{C.RESET}")
            print(f"{C.ACCENT}{'=' * 56}{C.RESET}")
        else:
            print("=" * 56)
            print(f"  {title}")
            print("=" * 56)

    def _section(title: str):
        print()
        if t.enabled:
            print(f"{C.ACCENT}{'=' * 56}{C.RESET}")
            print(f"  {C.ACCENT}{title}{C.RESET}")
            print(f"{C.ACCENT}{'=' * 56}{C.RESET}")
        else:
            print("=" * 56)
            print(f"  {title}")
            print("=" * 56)

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

    _header("📖  TUTORIAL & PANDUAN - GhostWriter")
    print()
    _line("Selamat datang di GhostWriter! 👻")
    _line("Panduan ini bakal ngebantu lu buka hasil render di browser.")
    print()

    # === CARA BUKA DI BROWSER ===
    _section("🌐 CARA BUKA DI BROWSER")

    print()
    _line("Langkah 1 - Jalanin server lokal")
    print()
    _cmd("python3 serve.py")
    print()
    _line("Kenapa harus server? Karena viewer GhostWriter fetch", indent=4)
    _line("index.json & asset vendor via HTTP. Kalo buka langsung", indent=4)
    _line("file HTML (file://), bakal error.", indent=4)

    print()
    _line("Langkah 2 - Buka browser")
    print()
    _line("Setelah server jalan, buka salah satu:", indent=4)
    print()
    _cmd("• Chrome / Firefox / Edge", indent=6)
    _cmd("• Ketik di address bar: http://localhost:8000/", indent=6)
    print()
    _hint("💡 Tips: serve.py bakal nanya otomatis")
    _hint("   \"buka browser sekarang?\" - tinggal ketik Y.")

    # === STRUKTUR OUTPUT ===
    _section("📂 STRUKTUR OUTPUT")

    print()
    _cmd("public/")
    _cmd("├── index.html              <- Landing page", indent=4)
    _cmd("├── index.json              <- Metadata convo", indent=4)
    _cmd("├── vendor/                 <- Asset offline", indent=4)
    _cmd("└── history/", indent=4)
    _cmd("    ├── 1789718334/         <- Convo 1", indent=4)
    _cmd("    │   └── index.html", indent=4)
    _cmd("    ├── 1789718335/         <- Convo 2", indent=4)
    _cmd("    │   └── index.html", indent=4)
    _cmd("    └── ...", indent=4)
    print()
    _line("🌐 URL:", indent=2)
    _cmd("Landing: http://localhost:8000/", indent=6)
    _cmd("Viewer:  http://localhost:8000/history/1789718334/", indent=6)

    # === KEYBOARD SHORTCUTS ===
    _section("⌨️  KEYBOARD SHORTCUTS (di viewer)")

    print()
    _cmd("/          Fokus ke search", indent=6)
    _cmd("j / k      Navigate pesan next / prev", indent=6)
    _cmd("Home       Scroll ke atas", indent=6)
    _cmd("End        Scroll ke bawah", indent=6)
    _cmd("Esc        Tutup sidebar / right rail", indent=6)

    # === TROUBLESHOOTING ===
    _section("❓ TROUBLESHOOTING")

    print()
    _hint("Q: Error \"fetch index.json failed\"?")
    _line("A: Pastiin lu akses via http://localhost:8000/,", indent=4)
    _line("   bukan file://path/to/file.html.", indent=4)
    print()
    _hint("Q: Port 8000 udah dipake?")
    _line("A: Ganti port: python3 serve.py --port 8001", indent=4)
    _line("   Atau kill proses: lsof -ti:8000 | xargs kill", indent=4)
    print()
    _hint("Q: Convo gak muncul di landing?")
    _line("A: Jalanin sync: python3 sync.py", indent=4)

    print()
    if t.enabled:
        print(f"{C.ACCENT}{'=' * 56}{C.RESET}")
    else:
        print("=" * 56)
    print()
    input(f"  {C.GRAY if t.enabled else ''}[Enter] buat balik ke menu...{C.RESET if t.enabled else ''}")


# ============================================================
# MENU
# ============================================================

def print_main_menu():
    t = get_theme()
    if t.enabled:
        print(f"\n  {C.ACCENT}╭{'─' * 46}╮{C.RESET}")
        print(f"  {C.ACCENT}│{C.RESET}  {C.BOLD}{C.WHITE}👻  GhostWriter - Menu Utama{C.RESET}{' ' * 16}{C.ACCENT}│{C.RESET}")
        print(f"  {C.ACCENT}├{'─' * 46}┤{C.RESET}")
        print(f"  {C.ACCENT}│{C.RESET}  {C.ACCENT}[1]{C.RESET}  {C.WHITE}Render backup lokal (.json/.md/.docx){C.RESET}{C.ACCENT}│{C.RESET}")
        print(f"  {C.ACCENT}│{C.RESET}  {C.ACCENT}[2]{C.RESET}  {C.WHITE}Sedot live dari DeepSeek{C.RESET}{' ' * 22}{C.ACCENT}│{C.RESET}")
        print(f"  {C.ACCENT}│{C.RESET}  {C.ACCENT}[3]{C.RESET}  {C.WHITE}📖 Tutorial & Panduan{C.RESET}{' ' * 24}{C.ACCENT}│{C.RESET}")
        print(f"  {C.ACCENT}│{C.RESET}  {C.GRAY}[0]{C.RESET}  {C.WHITE}Keluar{C.RESET}{' ' * 38}{C.ACCENT}│{C.RESET}")
        print(f"  {C.ACCENT}╰{'─' * 46}╯{C.RESET}")
    else:
        print("\n  ┌────────────────────────────────────────────┐")
        print("  │  👻 GhostWriter - Menu Utama                │")
        print("  ├────────────────────────────────────────────┤")
        print("  │  [1] Render backup lokal (.json/.md/.docx)  │")
        print("  │  [2] Sedot live dari DeepSeek               │")
        print("  │  [3] 📖 Tutorial & Panduan                  │")
        print("  │  [0] Keluar                                 │")
        print("  └────────────────────────────────────────────┘")


def _check_legacy_dist():
    """Warning kalo ada folder dist/ lama."""
    if os.path.isdir("dist"):
        t = get_theme()
        msg_warn = "Folder `dist/` terdeteksi (struktur lama)."
        msg_hint = "Hapus manual: rm -rf dist/"
        if t.enabled:
            print()
            print(f"  {C.YELLOW}⚠ {msg_warn}{C.RESET}")
            print(f"  {C.GRAY}  {msg_hint}{C.RESET}")
        else:
            print(f"  ⚠ {msg_warn}")
            print(f"    {msg_hint}")


def _wait_enter():
    t = get_theme()
    if t.enabled:
        input(f"\n  {C.GRAY}[Enter] buat balik ke menu...{C.RESET}")
    else:
        input("\n  [Enter] buat balik ke menu...")


def run_wizard():
    print_banner()
    print_status(f"Wizard Mode GhostWriter - by {AUTHOR}", status="ghost")
    print_info("Ketik '0' di prompt manapun buat batal")

    _check_legacy_dist()

    while True:
        print_main_menu()
        pilihan = _prompt("Pilih [1-3, 0=keluar]", default="1")

        if pilihan == "__CANCEL__" or pilihan in ("0", "q", "quit", "exit", "keluar"):
            print_status("Sampai jumpa, bre. Data lu aman di lokal.", status="ghost")
            break

        if pilihan in ("", "1"):
            handle_local_render()
            _wait_enter()
        elif pilihan == "2":
            handle_live_deepseek_backup()
            _wait_enter()
        elif pilihan == "3":
            handle_tutorial()
        else:
            print_warn("Pilihan gak valid.")


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
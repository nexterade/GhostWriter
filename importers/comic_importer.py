"""
GhostWriter — Comic Importer (ZIP)

Extract gambar dari file ZIP (manga, webtoon, comic strip, dsb),
generate reader HTML dengan format yang sama kayak PDF ebook.

Karakteristik:
    - Keep format asli (.jpg, .png, .webp, .gif, .bmp, .avif)
    - Natural sort (1, 2, 10, bukan 1, 10, 2)
    - Skip __MACOSX, ._*, .DS_Store, Thumbs.db
    - Flatten nested folder jadi 1 urutan

Dependencies:
    - zipfile (built-in)
    - Pillow (buat validate image — opsional)

Usage (dari main.py):
    from importers.comic_importer import handle_comic_import
    handle_comic_import()
"""

import os
import re
import glob
import time
import shutil
import zipfile

from tools.loading import (
    print_section, print_info, print_success, print_error, print_warn,
    print_numbered, print_bullet, LoadingSpinner,
)
from tools.theme import get_theme, C
from importers._reader_common import (
    slugify, ensure_dir, format_size, get_folder_size,
    render_reader_html, build_payload,
)


# ============================================================
# CONFIG
# ============================================================

INPUT_DIR = "inputs"
PUBLIC_DIR = "public"
COMICS_SUBDIR = "comics"
TEMPLATE_PATH = os.path.join("templates", "reader.html")

PAGE_PREFIX = "page_"
PAGE_DIGITS = 3

SUPPORTED_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".avif")
SKIP_PREFIXES = ("__MACOSX/", "._")
SKIP_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}

MAX_SINGLE_FILE_MB = 100
MAX_TOTAL_SIZE_MB = 2000


# ============================================================
# HELPERS
# ============================================================

def _get_input_dir() -> str:
    """Pakai inputs/ kalau ada, fallback ke root."""
    if os.path.isdir(INPUT_DIR):
        return INPUT_DIR
    return "."


def scan_zip_files() -> list:
    """Scan file .zip di input dir, sorted by name."""
    input_dir = _get_input_dir()
    pattern = os.path.join(input_dir, "*.zip")
    return sorted(glob.glob(pattern), key=lambda p: os.path.basename(p).lower())


def _is_image(name: str) -> bool:
    """Cek apakah file ZIP entry adalah image yang didukung."""
    lower = name.lower()

    # Skip Mac metadata
    if lower.startswith("__macosx/"):
        return False

    # Skip AppleDouble (._filename)
    basename = os.path.basename(name)
    if basename.startswith("._"):
        return False

    # Skip OS junk
    if basename in SKIP_NAMES:
        return False

    # Skip directory entry (endswith /)
    if name.endswith("/"):
        return False

    return lower.endswith(SUPPORTED_EXTS)


def _natural_sort_key(path: str):
    """
    Natural sort: 'page2.jpg' < 'page10.jpg'.
    Split path jadi chunk angka & non-angka.
    """
    basename = os.path.basename(path).lower()
    return [
        int(chunk) if chunk.isdigit() else chunk
        for chunk in re.split(r"(\d+)", basename)
    ]


def _unique_folder_name(base_slug: str, parent_dir: str) -> str:
    """Kalau folder <slug> udah ada, tambah suffix -2, -3, dst."""
    candidate = base_slug
    counter = 2
    while os.path.isdir(os.path.join(parent_dir, candidate)):
        candidate = f"{base_slug}-{counter}"
        counter += 1
        if counter > 999:
            candidate = f"{base_slug}-{int(time.time())}"
            break
    return candidate


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f} detik"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes} menit {secs} detik"


def _safe_ext(name: str) -> str:
    """Ambil extension dari nama file (lowercase, with dot)."""
    ext = os.path.splitext(name)[1].lower()
    return ext if ext in SUPPORTED_EXTS else ".jpg"


# ============================================================
# ZIP INSPECTION
# ============================================================

def _inspect_zip(zip_path: str) -> dict:
    """
    Baca struktur ZIP tanpa extract.
    Return: {
        "total_entries": int,
        "image_entries": list[str],
        "total_size": int,
        "warnings": list[str],
    }
    """
    result = {
        "total_entries": 0,
        "image_entries": [],
        "total_size": 0,
        "warnings": [],
    }

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            infos = zf.infolist()
            result["total_entries"] = len(infos)

            for info in infos:
                if info.is_dir():
                    continue
                result["total_size"] += info.file_size
                if _is_image(info.filename):
                    result["image_entries"].append(info.filename)

            if len(result["image_entries"]) == 0:
                result["warnings"].append("ZIP gak punya image yang didukung")
                return result

            # Sort natural
            result["image_entries"].sort(key=_natural_sort_key)

            # Warning kalau ada file >MAX_SINGLE_FILE_MB
            for info in infos:
                if info.file_size > MAX_SINGLE_FILE_MB * 1024 * 1024:
                    result["warnings"].append(
                        f"File gede: {info.filename} ({format_size(info.file_size)})"
                    )
                    break

            # Warning total size
            if result["total_size"] > MAX_TOTAL_SIZE_MB * 1024 * 1024:
                result["warnings"].append(
                    f"Total size >{MAX_TOTAL_SIZE_MB}MB. Proses bisa lama."
                )

    except zipfile.BadZipFile:
        result["warnings"].append("File bukan ZIP valid / korup")
    except OSError as e:
        result["warnings"].append(f"Gagal baca ZIP: {e}")

    return result


# ============================================================
# FILE PICKER
# ============================================================

def _pick_zip_file() -> str:
    """
    Prompt user buat pilih ZIP.
    Return: path ZIP atau "" kalau cancel.
    """
    zip_files = scan_zip_files()
    input_dir = _get_input_dir()

    if not zip_files:
        print_warn(f"Gak ada file .zip di folder '{input_dir}'.")
        print()
        print_info("Taruh ZIP di folder itu, atau kasih path manual.")

        from main import _prompt
        manual = _prompt("Path ZIP manual")
        if manual == "__CANCEL__" or not manual:
            return ""
        if not os.path.isfile(manual):
            print_error(f"File gak ditemukan: {manual}")
            return ""
        if not manual.lower().endswith(".zip"):
            print_error("File bukan ZIP.")
            return ""
        return manual

    print_section(f"Ditemukan {len(zip_files)} ZIP", icon="folder")
    for idx, f in enumerate(zip_files, 1):
        size = os.path.getsize(f)
        print_numbered(idx, f"{os.path.basename(f)}  ({format_size(size)})")

    print()
    print_bullet("[nomor]  → pilih dari daftar")
    print_bullet("path     → input path manual")
    print()

    from main import _prompt
    pilih = _prompt(f"Pilih ZIP [1-{len(zip_files)}]", default="1")
    if pilih == "__CANCEL__":
        return ""

    if pilih.isdigit():
        idx = int(pilih) - 1
        if 0 <= idx < len(zip_files):
            return zip_files[idx]
        print_warn(f"Nomor {pilih} di luar range. Coba path manual.")
        pilih = _prompt("Path ZIP manual")
        if pilih == "__CANCEL__" or not pilih:
            return ""
        if not os.path.isfile(pilih):
            print_error(f"File gak ditemukan: {pilih}")
            return ""
        return pilih

    if os.path.isfile(pilih):
        return pilih

    print_error(f"Input gak valid: {pilih}")
    return ""


# ============================================================
# MAIN HANDLER
# ============================================================

def handle_comic_import() -> bool:
    """
    Flow import comic ZIP.

    Returns:
        True kalau sukses extract minimal 1 image
        False kalau cancel / gagal total
    """
    print_section("Import Comic ZIP", icon="book")
    print_info("Extract gambar, natural sort, generate reader HTML")
    print()

    # === STEP 1: Pilih file ===
    zip_path = _pick_zip_file()
    if not zip_path:
        print_warn("Dibatalkan.")
        return False

    # === STEP 2: Inspect ZIP ===
    print()
    spinner = LoadingSpinner("Baca struktur ZIP...")
    spinner.start()

    info = _inspect_zip(zip_path)

    if not info["image_entries"]:
        spinner.stop("Gak ada image valid", status="error")
        for w in info["warnings"]:
            print_warn(w)
        return False

    num_images = len(info["image_entries"])
    spinner.stop(f"ZIP valid: {num_images} gambar")

    # === STEP 3: Konfirmasi ===
    fallback_title = os.path.splitext(os.path.basename(zip_path))[0]
    title = fallback_title

    print()
    print_section("Info Comic", icon="info")
    print_bullet(f"Judul  : {title}", indent=4)
    print_bullet(f"Gambar : {num_images}", indent=4)
    print_bullet(f"Size   : {format_size(os.path.getsize(zip_path))}", indent=4)
    print_bullet(f"Uncompressed: {format_size(info['total_size'])}", indent=4)

    if info["warnings"]:
        print()
        for w in info["warnings"]:
            print_warn(w)

    print()

    from main import _prompt_yes_no
    if not _prompt_yes_no("Lanjut extract?", default="y"):
        print_warn("Dibatalkan.")
        return False

    # === STEP 4: Siapin folder output ===
    slug_base = slugify(title, max_len=50)
    comics_dir = os.path.join(PUBLIC_DIR, COMICS_SUBDIR)
    if not ensure_dir(comics_dir):
        return False

    # === FIX: hapus folder lama kalau slug-nya sama ===
    slug = slug_base
    existing_dir = os.path.join(comics_dir, slug)

    if os.path.isdir(existing_dir):
        print_info(f"Folder '{slug}' udah ada — hapus & extract ulang")
        try:
            shutil.rmtree(existing_dir)
        except OSError as e:
            print_warn(f"Gagal hapus folder lama: {e}")
            slug = _unique_folder_name(slug_base, comics_dir)

    out_dir = os.path.join(comics_dir, slug)
    images_dir = os.path.join(out_dir, "images")
    out_html = os.path.join(out_dir, "index.html")

    if not ensure_dir(images_dir):
        return False

    if slug != slug_base:
        print_info(f"Folder '{slug_base}' gagal dihapus, pakai '{slug}'")

    # === STEP 5: Extract images ===
    print()
    print_section(f"Extract {num_images} Gambar", icon="hammer")
    print()

    start_time = time.time()
    sections = []
    extracted_count = 0
    failed_entries = []

    try:
        spinner = LoadingSpinner("Extract ZIP...")
        spinner.start()

        with zipfile.ZipFile(zip_path, "r") as zf:
            for i, entry_name in enumerate(info["image_entries"], 1):
                ext = _safe_ext(entry_name)
                filename = f"{PAGE_PREFIX}{i:0{PAGE_DIGITS}d}{ext}"
                filepath = os.path.join(images_dir, filename)

                try:
                    with zf.open(entry_name) as src, open(filepath, "wb") as dst:
                        shutil.copyfileobj(src, dst)

                    file_size = os.path.getsize(filepath)
                    if file_size == 0:
                        os.remove(filepath)
                        failed_entries.append((entry_name, "file kosong"))
                        continue

                    sections.append({
                        "page": i,
                        "type": "image",
                        "src": f"images/{filename}",
                    })
                    extracted_count += 1

                except Exception as e:
                    failed_entries.append((entry_name, str(e)))

        spinner.stop(f"Tersimpan: {extracted_count} gambar")

    except zipfile.BadZipFile:
        print_error("ZIP korup / gak bisa dibaca.")
        try:
            shutil.rmtree(out_dir)
        except OSError:
            pass
        return False
    except Exception as e:
        print_error(f"Gagal extract: {e}")
        try:
            shutil.rmtree(out_dir)
        except OSError:
            pass
        return False

    if extracted_count == 0:
        print_error("Gak ada gambar yang berhasil di-extract.")
        try:
            shutil.rmtree(out_dir)
        except OSError:
            pass
        return False

    if failed_entries:
        print_warn(f"{len(failed_entries)} entry gagal:")
        for name, err in failed_entries[:3]:
            print_bullet(f"{name}: {err}", indent=6)
        if len(failed_entries) > 3:
            print_bullet(f"... dan {len(failed_entries) - 3} lagi", indent=6)

    # === STEP 6: Renumber sections (kalau ada yang gagal) ===
    if len(sections) != num_images:
        for new_idx, sec in enumerate(sections, 1):
            sec["page"] = new_idx

    # === STEP 7: Generate HTML ===
    print()
    spinner = LoadingSpinner("Generate HTML...")
    spinner.start()

    payload = build_payload(
        title=title,
        author="Comic Source",
        sections=sections,
    )

    try:
        render_reader_html(
            template_path=TEMPLATE_PATH,
            output_path=out_html,
            payload=payload,
            type_="comic",
        )
    except Exception as e:
        spinner.stop(f"Gagal generate HTML: {e}", status="error")
        print_info(f"Folder output tetep ada di: {out_dir}")
        return False

    spinner.stop("HTML siap")

    # === STEP 8: Report ===
    duration = time.time() - start_time
    folder_size = get_folder_size(out_dir)

    print()
    print_section("Import Selesai", icon="check")
    print_success(f"Comic '{title}' berhasil di-import!")
    print()
    print_bullet(f"Gambar   : {extracted_count}", indent=4)
    print_bullet(f"Durasi   : {_format_duration(duration)}", indent=4)
    print_bullet(f"Size     : {format_size(folder_size)}", indent=4)
    print_bullet(f"Lokasi   : {out_dir}", indent=4)

    print()
    _print_access_hint(slug)

    return True


# ============================================================
# ACCESS HINT
# ============================================================

def _print_access_hint(slug: str):
    """Print cara akses comic di browser."""
    t = get_theme()
    url = f"http://localhost:8000/comics/{slug}/index.html"

    if t.enabled:
        print(f"  {C.ACCENT_DIM}{'─' * 56}{C.RESET}")
        print(f"  {C.GREEN}✅{C.RESET}  {C.WHITE}Cara buka:{C.RESET}")
        print()
        print(f"  {C.ACCENT_DIM}1.{C.RESET} {C.GRAY}Jalanin server (kalau belum): {C.ACCENT}python3 serve.py{C.RESET}")
        print(f"  {C.ACCENT_DIM}2.{C.RESET} {C.GRAY}Buka: {C.WHITE}{url}{C.RESET}")
        print()
        print(f"  {C.GRAY}Atau akses via landing page kalau udah di-sync.{C.RESET}")
        print(f"  {C.ACCENT_DIM}{'─' * 56}{C.RESET}")
    else:
        print("  " + "─" * 56)
        print("  ✅  Cara buka:")
        print()
        print("  1. Jalanin server (kalau belum): python3 serve.py")
        print(f"  2. Buka: {url}")
        print()
        print("  Atau akses via landing page kalau udah di-sync.")
        print("  " + "─" * 56)
"""
GhostWriter — PDF Importer (Image Mode)

Convert PDF (ebook, scan, apapun) jadi reader HTML dengan setiap halaman
di-render sebagai gambar JPEG.

Dependencies:
    - pypdf        : baca metadata & count halaman
    - pdf2image    : render PDF -> PIL images (butuh Poppler)
    - Pillow       : save image ke disk

Usage (dari main.py):
    from importers.pdf_importer import handle_pdf_import
    handle_pdf_import()
"""

import os
import re
import glob
import time
import shutil

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
READERS_SUBDIR = "readers"
TEMPLATE_PATH = os.path.join("templates", "reader.html")

DEFAULT_DPI = 150
JPEG_QUALITY = 85
PAGE_PREFIX = "page_"
PAGE_DIGITS = 3


# ============================================================
# HELPERS
# ============================================================

def _get_input_dir() -> str:
    """Pakai inputs/ kalau ada, fallback ke root."""
    if os.path.isdir(INPUT_DIR):
        return INPUT_DIR
    return "."


def scan_pdf_files() -> list:
    """Scan file .pdf di input dir, sorted by name."""
    input_dir = _get_input_dir()
    pattern = os.path.join(input_dir, "*.pdf")
    return sorted(glob.glob(pattern), key=lambda p: os.path.basename(p).lower())


def _check_poppler() -> bool:
    """Cek apakah Poppler (pdftoppm) tersedia di PATH."""
    return shutil.which("pdftoppm") is not None


def _read_pdf_metadata(pdf_path: str) -> dict:
    """
    Baca metadata PDF via pypdf.
    Return: {"title": str, "author": str, "pages": int}
    """
    result = {"title": "", "author": "", "pages": 0}

    try:
        from pypdf import PdfReader
    except ImportError:
        return result

    try:
        reader = PdfReader(pdf_path)
        result["pages"] = len(reader.pages)

        meta = reader.metadata
        if meta:
            title = getattr(meta, "title", None) or meta.get("/Title", "")
            author = getattr(meta, "author", None) or meta.get("/Author", "")
            if title:
                result["title"] = str(title).strip()
            if author:
                result["author"] = str(author).strip()
    except Exception:
        pass

    return result


def _unique_folder_name(base_slug: str, parent_dir: str) -> str:
    """
    Kalau folder <slug> udah ada, tambah suffix -2, -3, dst.
    """
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


# ============================================================
# FILE PICKER
# ============================================================

def _pick_pdf_file() -> str:
    """
    Prompt user buat pilih PDF.
    Return: path PDF atau "" kalau cancel.
    """
    pdf_files = scan_pdf_files()
    input_dir = _get_input_dir()

    if not pdf_files:
        print_warn(f"Gak ada file .pdf di folder '{input_dir}'.")
        print()
        print_info("Taruh PDF di folder itu, atau kasih path manual.")

        from main import _prompt
        manual = _prompt("Path PDF manual")
        if manual == "__CANCEL__" or not manual:
            return ""
        if not os.path.isfile(manual):
            print_error(f"File gak ditemukan: {manual}")
            return ""
        if not manual.lower().endswith(".pdf"):
            print_error("File bukan PDF.")
            return ""
        return manual

    print_section(f"Ditemukan {len(pdf_files)} PDF", icon="folder")
    for idx, f in enumerate(pdf_files, 1):
        size = os.path.getsize(f)
        print_numbered(idx, f"{os.path.basename(f)}  ({format_size(size)})")

    print()
    print_bullet("[nomor]  → pilih dari daftar")
    print_bullet("path     → input path manual")
    print()

    from main import _prompt
    pilih = _prompt(f"Pilih PDF [1-{len(pdf_files)}]", default="1")
    if pilih == "__CANCEL__":
        return ""

    if pilih.isdigit():
        idx = int(pilih) - 1
        if 0 <= idx < len(pdf_files):
            return pdf_files[idx]
        print_warn(f"Nomor {pilih} di luar range. Coba path manual.")
        pilih = _prompt("Path PDF manual")
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

def handle_pdf_import() -> bool:
    """
    Flow import PDF ebook (image mode).

    Returns:
        True kalau sukses render minimal 1 halaman
        False kalau cancel / gagal total
    """
    print_section("Import Ebook PDF", icon="book")
    print_info("Setiap halaman bakal di-render jadi gambar JPEG")
    print()

    # === STEP 1: Cek dependencies ===
    try:
        from pypdf import PdfReader  # noqa: F401
    except ImportError:
        print_error("pypdf belum keinstall.")
        print_info("Jalanin: pip install pypdf pdf2image Pillow")
        return False

    try:
        from pdf2image import convert_from_path  # noqa: F401
    except ImportError:
        print_error("pdf2image belum keinstall.")
        print_info("Jalanin: pip install pdf2image Pillow")
        return False

    if not _check_poppler():
        print_error("Poppler (pdftoppm) gak ketemu di PATH.")
        print_info("Install dulu:")
        print_bullet("Termux  : pkg install poppler", indent=6)
        print_bullet("Ubuntu  : sudo apt install poppler-utils", indent=6)
        print_bullet("macOS   : brew install poppler", indent=6)
        return False

    # === STEP 2: Pilih file ===
    pdf_path = _pick_pdf_file()
    if not pdf_path:
        print_warn("Dibatalkan.")
        return False

    # === STEP 3: Baca metadata ===
    print()
    spinner = LoadingSpinner("Analisis PDF...")
    spinner.start()

    meta = _read_pdf_metadata(pdf_path)
    num_pages = meta["pages"]

    if num_pages <= 0:
        spinner.stop("PDF gak punya halaman", status="error")
        return False

    fallback_title = os.path.splitext(os.path.basename(pdf_path))[0]
    title = meta["title"] or fallback_title
    author = meta["author"]

    spinner.stop(f"PDF valid: {num_pages} halaman", status="ok")

    # === STEP 4: Konfirmasi ===
    print()
    print_section("Info Ebook", icon="info")
    print_bullet(f"Judul  : {title}", indent=4)
    if author:
        print_bullet(f"Author : {author}", indent=4)
    print_bullet(f"Halaman: {num_pages}", indent=4)
    print_bullet(f"Size   : {format_size(os.path.getsize(pdf_path))}", indent=4)
    print_bullet(f"DPI    : {DEFAULT_DPI}", indent=4)

    if num_pages > 100:
        print()
        print_warn(f"PDF ini gede ({num_pages} halaman). Proses bisa makan 5-15 menit.")
        print_info("Tergantung device & DPI. Sabar ya.")

    print()

    from main import _prompt_yes_no
    if not _prompt_yes_no("Lanjut render?", default="y"):
        print_warn("Dibatalkan.")
        return False

    # === STEP 5: Siapin folder output ===
    slug_base = slugify(title, max_len=50)
    readers_dir = os.path.join(PUBLIC_DIR, READERS_SUBDIR)
    if not ensure_dir(readers_dir):
        return False

    # === FIX: hapus folder lama kalau slug-nya sama ===
    slug = slug_base
    existing_dir = os.path.join(readers_dir, slug)

    if os.path.isdir(existing_dir):
        print_info(f"Folder '{slug}' udah ada — hapus & render ulang")
        try:
            shutil.rmtree(existing_dir)
        except OSError as e:
            print_warn(f"Gagal hapus folder lama: {e}")
            slug = _unique_folder_name(slug_base, readers_dir)

    out_dir = os.path.join(readers_dir, slug)
    images_dir = os.path.join(out_dir, "images")
    out_html = os.path.join(out_dir, "index.html")

    if not ensure_dir(images_dir):
        return False

    if slug != slug_base:
        print_info(f"Folder '{slug_base}' gagal dihapus, pakai '{slug}'")

    # === STEP 6: Render PDF -> images ===
    print()
    print_section(f"Render {num_pages} Halaman", icon="hammer")
    print()

    start_time = time.time()
    sections = []
    rendered_count = 0
    failed_pages = []

    try:
        spinner = LoadingSpinner(f"Render halaman 1/{num_pages}...")
        spinner.start()

        images = convert_from_path(
            pdf_path,
            dpi=DEFAULT_DPI,
            fmt="jpeg",
            thread_count=2,
            output_folder=None,
        )

        spinner.stop(f"Render selesai: {len(images)} halaman")

        # === STEP 7: Save images ===
        print()
        spinner = LoadingSpinner("Menyimpan gambar...")
        spinner.start()

        for i, img in enumerate(images, 1):
            filename = f"{PAGE_PREFIX}{i:0{PAGE_DIGITS}d}.jpg"
            filepath = os.path.join(images_dir, filename)

            try:
                img.save(filepath, "JPEG", quality=JPEG_QUALITY, optimize=True)
                rendered_count += 1
                sections.append({
                    "page": i,
                    "type": "image",
                    "src": f"images/{filename}",
                })
            except Exception as e:
                failed_pages.append((i, str(e)))

        spinner.stop(f"Tersimpan: {rendered_count} halaman")

    except Exception as e:
        print_error(f"Gagal render PDF: {e}")
        print_info("Bersihin folder output...")
        try:
            shutil.rmtree(out_dir)
        except OSError:
            pass
        return False

    if rendered_count == 0:
        print_error("Gak ada halaman yang berhasil di-render.")
        try:
            shutil.rmtree(out_dir)
        except OSError:
            pass
        return False

    if failed_pages:
        print_warn(f"{len(failed_pages)} halaman gagal:")
        for pg, err in failed_pages[:3]:
            print_bullet(f"Hal {pg}: {err}", indent=6)
        if len(failed_pages) > 3:
            print_bullet(f"... dan {len(failed_pages) - 3} lagi", indent=6)

    # === STEP 8: Generate HTML ===
    print()
    spinner = LoadingSpinner("Generate HTML...")
    spinner.start()

    payload = build_payload(
        title=title,
        author=author,
        sections=sections,
    )

    try:
        render_reader_html(
            template_path=TEMPLATE_PATH,
            output_path=out_html,
            payload=payload,
            type_="ebook",
        )
    except Exception as e:
        spinner.stop(f"Gagal generate HTML: {e}", status="error")
        print_info(f"Folder output tetep ada di: {out_dir}")
        return False

    spinner.stop("HTML siap")

    # === STEP 9: Report ===
    duration = time.time() - start_time
    folder_size = get_folder_size(out_dir)

    print()
    print_section("Import Selesai", icon="check")
    print_success(f"Ebook '{title}' berhasil di-import!")
    print()
    print_bullet(f"Halaman  : {rendered_count}", indent=4)
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
    """Print cara akses ebook di browser."""
    t = get_theme()
    url = f"http://localhost:8000/readers/{slug}/index.html"

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
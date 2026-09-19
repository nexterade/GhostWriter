"""
GhostWriter — Reader Common Helpers

Shared utilities untuk PDF & Comic importer:
- Slug generation (folder name)
- HTML rendering dari templates/reader.html
- Escaping JSON untuk injeksi ke <script>
- Konstanta LOGO_SVG & FAVICON_LINK (samain dengan index.html)
"""

import os
import re
import json
import time

from tools.loading import print_error, print_warn


# ============================================================
# CONSTANTS — SAMAIN DENGAN index.html & viewer.html
# ============================================================

LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'fill="var(--accent, #38bdf8)" aria-hidden="true" '
    'class="gw-logo-svg" width="26" height="26">'
    '<path d="M12 2C7.58 2 4 5.58 4 10v11l2.5-2 2.5 2 2.5-2 2.5 2 '
    '2.5-2 2.5 2V10c0-4.42-3.58-8-8-8zm-3 9a1.25 1.25 0 1 1 0-2.5 '
    '1.25 1.25 0 0 1 0 2.5zm6 0a1.25 1.25 0 1 1 0-2.5 1.25 1.25 '
    '0 0 1 0 2.5z"/></svg>'
)

FAVICON_LINK = (
    '<link rel="icon" type="image/svg+xml" '
    'href="data:image/svg+xml;base64,'
    'PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9'
    'IjAgMCAyNCAyNCI+PHJlY3Qgd2lkdGg9IjI0IiBoZWlnaHQ9IjI0IiByeD0iNSIg'
    'ZmlsbD0iIzBiMGYxOSIvPjxwYXRoIGZpbGw9IiMzOGJkZjgiIGQ9Ik0xMiA0Qzgu'
    'MTMgNCA1IDcuMTMgNSAxMXY3LjVsMi0xLjUgMiAxLjUgMi0xLjUgMiAxLjUgMi0x'
    'LjUgMiAxLjVWMTFjMC0zLjg3LTMuMTMtNy03LTd6bS0yLjUgN2ExIDEgMCAxIDEg'
    'MC0yIDEgMSAwIDAgMSAwIDJ6bTUgMGExIDEgMCAxIDEgMC0yIDEgMSAwIDAgMSAw'
    'IDJ6Ii8+PC9zdmc+'
    '">'
)


# ============================================================
# UTILITIES
# ============================================================

def slugify(text: str, max_len: int = 50) -> str:
    """
    Convert title jadi slug aman buat nama folder.
    Contoh: "Fisika Kuantum — Bab 1" -> "fisika-kuantum-bab-1"
    """
    if not text:
        return f"untitled_{int(time.time())}"

    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s\-]+", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")

    if not text:
        return f"untitled_{int(time.time())}"

    return text[:max_len].rstrip("-")


def ensure_dir(path: str) -> bool:
    """Bikin folder kalau belum ada. Return True kalau sukses."""
    if not path:
        return False
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError as e:
        print_error(f"Gagal bikin folder '{path}': {e}")
        return False


def format_size(size_bytes: int) -> str:
    """Human-readable size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_folder_size(folder_path: str) -> int:
    """Total size folder recursive."""
    total = 0
    try:
        for dirpath, _, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
    except OSError:
        pass
    return total


# ============================================================
# JSON INJECTION
# ============================================================

def _safe_json_for_script(data: dict) -> str:
    """
    Serialize dict ke JSON string yang aman buat disuntik ke <script>.
    Handle `</script>` di dalam string dengan escape `</` -> `<\\/`.
    """
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return raw.replace("</", "<\\/")


# ============================================================
# HTML RENDERING
# ============================================================

def _build_subtitle(type_: str, pages: int, author: str = "") -> str:
    """Bikin subtitle konsisten buat header & sidebar."""
    type_label = "Ebook" if type_ == "ebook" else "Comic"
    base = f"{type_label} · {pages} halaman"
    if author and author.strip():
        return f"{base} · {author.strip()}"
    return base


def render_reader_html(
    template_path: str,
    output_path: str,
    payload: dict,
    type_: str = "ebook",
) -> str:
    """
    Render templates/reader.html dengan payload.

    Args:
        template_path: path ke templates/reader.html
        output_path:   path output index.html
        payload:       dict {title, author, pages, sections}
        type_:         "ebook" atau "comic"

    Returns:
        output_path kalau sukses, raise Exception kalau gagal.
    """
    if not os.path.isfile(template_path):
        raise FileNotFoundError(f"Template gak ada: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    title = payload.get("title") or "Tanpa Judul"
    author = payload.get("author") or ""
    pages = int(payload.get("pages") or len(payload.get("sections") or []))

    type_class = "ebook" if type_ == "ebook" else "comic"
    type_label = "EBOOK" if type_ == "ebook" else "COMIC"
    subtitle = _build_subtitle(type_, pages, author)

    json_str = _safe_json_for_script(payload)

    replacements = {
        "{{ TITLE }}":        _escape_html(title),
        "{{ SUBTITLE }}":     _escape_html(subtitle),
        "{{ TYPE_CLASS }}":   type_class,
        "{{ TYPE_LABEL }}":   type_label,
        "{{ TOTAL_PAGES }}":  str(pages),
        "{{ LOGO_SVG }}":     LOGO_SVG,
        "{{ FAVICON_LINK }}": FAVICON_LINK,
        "{{ READER_JSON }}":  json_str,
    }

    for key, val in replacements.items():
        html = html.replace(key, val)

    out_dir = os.path.dirname(output_path)
    if out_dir and not ensure_dir(out_dir):
        raise OSError(f"Gagal bikin folder output: {out_dir}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


def _escape_html(text: str) -> str:
    """Escape minimal buat konteks HTML (bukan atribut)."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ============================================================
# PAYLOAD BUILDER
# ============================================================

def build_payload(title: str, author: str, sections: list) -> dict:
    """
    Bikin payload standar buat reader.html.

    Args:
        title:    judul ebook/comic
        author:   author (boleh kosong)
        sections: list of {page, type, src/content}

    Returns:
        dict payload siap render
    """
    return {
        "title": title or "Tanpa Judul",
        "author": author or "",
        "pages": len(sections),
        "sections": sections,
    }
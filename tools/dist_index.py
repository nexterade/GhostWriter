import os
import re
import json
import glob
import time
from datetime import datetime
from typing import List, Dict, Any

from tools.theme import (
    LOGO_SVG_INLINE,
    get_favicon_link,
)


PUBLIC_DIR = "public"
HISTORY_SUBDIR = "history"
READERS_SUBDIR = "readers"
COMICS_SUBDIR = "comics"
INDEX_JSON = "index.json"
INDEX_HTML = "index.html"
MAX_INDEX_ITEMS = 500

TYPE_CHAT = "chat"
TYPE_EBOOK = "ebook"
TYPE_COMIC = "comic"

TYPE_LABELS = {
    TYPE_CHAT: {"emoji": "💬", "label": "Chat"},
    TYPE_EBOOK: {"emoji": "📖", "label": "Ebook"},
    TYPE_COMIC: {"emoji": "🎨", "label": "Comic"},
}


# === EXTRACTORS ===

def _extract_title(html_path: str, fallback: str) -> str:
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            head = f.read(4000)
        m = re.search(r"<title>([^<]+)</title>", head, re.IGNORECASE)
        if m:
            title = m.group(1).strip()
            if title:
                return title
    except Exception:
        pass
    return fallback


def _extract_msg_count(html_path: str) -> int:
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        return len(re.findall(r'class="message-row', content))
    except Exception:
        return 0


def _extract_created_at(html_path: str) -> str:
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            head = f.read(6000)
        m = re.search(r'id="header-subtitle"[^>]*>([^<]+)<', head)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return ""


def _extract_first_created(html_path: str) -> str:
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read(200_000)
        m = re.search(r'class="meta-time">([^<]+)<', content)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return ""


def _extract_pages(html_path: str) -> int:
    """Extract total halaman dari reader.html (id='stat-pages')."""
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        m = re.search(r'id="stat-pages"[^>]*>(\d+)<', content)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return 0


def _extract_reader_subtitle(html_path: str) -> str:
    """Extract subtitle dari reader.html (buat meta info)."""
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            head = f.read(8000)
        m = re.search(r'class="header-subtitle"[^>]*>([^<]+)<', head)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return ""


# === TITLE NORMALIZATION (PR-30 FIXED) ===

_TS_SUFFIX_PATTERNS = [
    re.compile(r"\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s*$"),
    re.compile(r"\s+\d{4}-\d{2}-\d{2}\s*$"),
    re.compile(r"_\d{4}-\d{2}-\d{2}\s*$"),
]

_PAREN_NUM_PATTERN = re.compile(r"\s*\(\d+\)\s*$")


def _normalize_title(title: str) -> str:
    t = title.strip()
    for pat in _TS_SUFFIX_PATTERNS:
        t = pat.sub("", t)
    return t.strip().lower()


def _normalize_title_strip_paren(title: str) -> str:
    t = _normalize_title(title)
    t = _PAREN_NUM_PATTERN.sub("", t)
    return t.strip().lower()


def _dedup_by_title(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Dedup khusus chat (by normalized title)."""
    seen: Dict[str, Dict[str, Any]] = {}
    for it in items:
        key = _normalize_title(it.get("title", ""))
        if not key:
            key = it["id"].lower()
        if key not in seen:
            seen[key] = it
        else:
            if it.get("mtime", 0) > seen[key].get("mtime", 0):
                seen[key] = it
    return list(seen.values())


def _dedup_by_title_aggressive(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Dict[str, Dict[str, Any]] = {}
    for it in items:
        key = _normalize_title_strip_paren(it.get("title", ""))
        if not key:
            key = it["id"].lower()
        if key not in seen:
            seen[key] = it
        else:
            if it.get("mtime", 0) > seen[key].get("mtime", 0):
                seen[key] = it
    return list(seen.values())


def _convo_sort_key(it: Dict[str, Any]) -> tuple:
    convo_id = it.get("id", "")
    try:
        numeric_id = int(convo_id)
    except (ValueError, TypeError):
        numeric_id = 0
    return (numeric_id, it.get("mtime", 0))


# === SCAN — CHAT ===

def scan_dist() -> List[Dict[str, Any]]:
    """Scan public/history/*/index.html — tiap subfolder = 1 convo."""
    results = []
    history_dir = os.path.join(PUBLIC_DIR, HISTORY_SUBDIR)

    if not os.path.isdir(history_dir):
        return results

    for folder_path in sorted(glob.glob(os.path.join(history_dir, "*"))):
        if not os.path.isdir(folder_path):
            continue

        convo_id = os.path.basename(folder_path)
        index_path = os.path.join(folder_path, "index.html")
        if not os.path.isfile(index_path):
            continue

        try:
            size_kb = os.path.getsize(index_path) / 1024
            mtime = os.path.getmtime(index_path)
        except OSError:
            continue

        fallback_title = convo_id
        title = _extract_title(index_path, fallback_title)
        msg_count = _extract_msg_count(index_path)
        created_at = _extract_created_at(index_path)
        first_created = _extract_first_created(index_path)

        results.append({
            "id": convo_id,
            "folder": f"{HISTORY_SUBDIR}/{convo_id}",
            "title": title,
            "type": TYPE_CHAT,
            "size_kb": round(size_kb, 1),
            "msg_count": msg_count,
            "pages": 0,
            "created_at": created_at,
            "first_created": first_created,
            "mtime": mtime,
        })

    results.sort(key=_convo_sort_key, reverse=True)
    results = _dedup_by_title(results)

    if len(results) > MAX_INDEX_ITEMS:
        results = _dedup_by_title_aggressive(results)

    if len(results) > MAX_INDEX_ITEMS:
        results = results[:MAX_INDEX_ITEMS]

    return results


# === SCAN — READERS (EBOOK) ===

def scan_readers() -> List[Dict[str, Any]]:
    """Scan public/readers/*/index.html — tiap subfolder = 1 ebook."""
    results = []
    readers_dir = os.path.join(PUBLIC_DIR, READERS_SUBDIR)

    if not os.path.isdir(readers_dir):
        return results

    for folder_path in sorted(glob.glob(os.path.join(readers_dir, "*"))):
        if not os.path.isdir(folder_path):
            continue

        slug = os.path.basename(folder_path)
        index_path = os.path.join(folder_path, "index.html")
        if not os.path.isfile(index_path):
            continue

        try:
            size_kb = _get_folder_size(folder_path) / 1024
            mtime = os.path.getmtime(index_path)
        except OSError:
            continue

        fallback_title = slug.replace("-", " ").replace("_", " ").title()
        title = _extract_title(index_path, fallback_title)
        pages = _extract_pages(index_path)
        created_at = _extract_reader_subtitle(index_path)

        results.append({
            "id": slug,
            "folder": f"{READERS_SUBDIR}/{slug}",
            "title": title,
            "type": TYPE_EBOOK,
            "size_kb": round(size_kb, 1),
            "msg_count": 0,
            "pages": pages,
            "created_at": created_at,
            "first_created": "",
            "mtime": mtime,
        })

    results.sort(key=lambda x: x.get("mtime", 0), reverse=True)
    return results


# === SCAN — COMICS ===

def scan_comics() -> List[Dict[str, Any]]:
    """Scan public/comics/*/index.html — tiap subfolder = 1 comic."""
    results = []
    comics_dir = os.path.join(PUBLIC_DIR, COMICS_SUBDIR)

    if not os.path.isdir(comics_dir):
        return results

    for folder_path in sorted(glob.glob(os.path.join(comics_dir, "*"))):
        if not os.path.isdir(folder_path):
            continue

        slug = os.path.basename(folder_path)
        index_path = os.path.join(folder_path, "index.html")
        if not os.path.isfile(index_path):
            continue

        try:
            size_kb = _get_folder_size(folder_path) / 1024
            mtime = os.path.getmtime(index_path)
        except OSError:
            continue

        fallback_title = slug.replace("-", " ").replace("_", " ").title()
        title = _extract_title(index_path, fallback_title)
        pages = _extract_pages(index_path)
        created_at = _extract_reader_subtitle(index_path)

        results.append({
            "id": slug,
            "folder": f"{COMICS_SUBDIR}/{slug}",
            "title": title,
            "type": TYPE_COMIC,
            "size_kb": round(size_kb, 1),
            "msg_count": 0,
            "pages": pages,
            "created_at": created_at,
            "first_created": "",
            "mtime": mtime,
        })

    results.sort(key=lambda x: x.get("mtime", 0), reverse=True)
    return results


# === SCAN — ALL ===

def scan_all() -> List[Dict[str, Any]]:
    """Gabungan semua tipe."""
    all_items = scan_dist() + scan_readers() + scan_comics()
    all_items.sort(key=lambda x: x.get("mtime", 0), reverse=True)
    return all_items


def _get_folder_size(folder_path: str) -> int:
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


# === DATE GROUPING ===

DATE_GROUP_ORDER = [
    "Hari Ini",
    "Kemarin",
    "7 Hari Terakhir",
    "30 Hari Terakhir",
    "Lebih Lama",
]


def _date_group_key(mtime: float) -> str:
    now = datetime.now()
    dt = datetime.fromtimestamp(mtime)
    today = now.date()
    target = dt.date()
    diff = (today - target).days
    if diff <= 0:
        return "Hari Ini"
    if diff == 1:
        return "Kemarin"
    if diff <= 7:
        return "7 Hari Terakhir"
    if diff <= 30:
        return "30 Hari Terakhir"
    return "Lebih Lama"


def _group_items_by_date(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = {k: [] for k in DATE_GROUP_ORDER}
    for it in items:
        g = _date_group_key(it.get("mtime", 0))
        groups.setdefault(g, []).append(it)
    return groups


# === FORMATTING ===

def _format_date(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# === ITEM RENDERING ===

def _build_meta_html(it: Dict[str, Any]) -> str:
    """Meta display beda per tipe."""
    t = it.get("type", TYPE_CHAT)
    size_kb = it.get("size_kb", 0)
    created = it.get("created_at") or _format_date(it.get("mtime", 0))
    first_created = it.get("first_created") or ""

    if t == TYPE_CHAT:
        msg_count = it.get("msg_count", 0)
        meta_parts = [
            f'<span>💬 {msg_count} pesan</span>',
            f'<span>📄 {size_kb:.1f} KB</span>',
            f'<span>🕐 {_esc(created)}</span>',
        ]
        if first_created and first_created != created:
            meta_parts.append(f'<span title="First created">🌱 {_esc(first_created)}</span>')
        return "\n        ".join(meta_parts)

    elif t == TYPE_EBOOK:
        pages = it.get("pages", 0)
        return (
            f'<span>📖 {pages} halaman</span>\n        '
            f'<span>📄 {size_kb:.1f} KB</span>\n        '
            f'<span>🕐 {_esc(created)}</span>'
        )

    elif t == TYPE_COMIC:
        pages = it.get("pages", 0)
        return (
            f'<span>🎨 {pages} halaman</span>\n        '
            f'<span>📄 {size_kb:.1f} KB</span>\n        '
            f'<span>🕐 {_esc(created)}</span>'
        )

    return f'<span>📄 {size_kb:.1f} KB</span>'


def _render_item(it: Dict[str, Any]) -> str:
    """Render 1 item (chat / ebook / comic)."""
    t = it.get("type", TYPE_CHAT)
    item_id = it["id"]
    folder = it["folder"]

    if t == TYPE_CHAT:
        href = f"{folder}/"
    else:
        href = f"{folder}/index.html"

    title = _esc(it["title"])
    badge = TYPE_LABELS.get(t, {}).get("emoji", "📄")
    search_blob = f"{it['title']} {it.get('created_at', '')}".lower()
    meta_html = _build_meta_html(it)

    return (
        f'<a class="conv-item" href="{href}"'
        f' data-type="{t}"'
        f' data-search="{_esc(search_blob)}"'
        f' data-msg="{it.get("msg_count", 0)}"'
        f' data-pages="{it.get("pages", 0)}"'
        f' data-size="{it.get("size_kb", 0)}"'
        f' data-mtime="{it.get("mtime", 0)}"'
        f' data-title="{_esc(search_blob)}">'
        f'\n  <div class="conv-main">'
        f'\n    <div class="conv-title"><span class="type-badge-inline">{badge}</span> {title}</div>'
        f'\n    <div class="conv-meta">\n        {meta_html}\n    </div>'
        f'\n  </div>'
        f'\n  <div class="conv-arrow">→</div>'
        f'\n</a>'
    )


def _render_groups(items: List[Dict[str, Any]]) -> str:
    if not items:
        return (
            '<div class="empty">'
            '<div class="empty-icon">👻</div>'
            '<div class="empty-title">Belum ada konten</div>'
            '<div class="empty-sub">Render chat, import PDF, atau import comic dulu.</div>'
            '</div>'
        )

    groups = _group_items_by_date(items)
    sections = []
    for group_name in DATE_GROUP_ORDER:
        group_items = groups.get(group_name, [])
        if not group_items:
            continue
        rows = "\n".join(_render_item(it) for it in group_items)
        sections.append(
            f'<section class="date-group" data-group="{_esc(group_name)}">'
            f'\n  <h2 class="date-label">{_esc(group_name)} '
            f'<span class="date-count">{len(group_items)}</span></h2>'
            f'\n  <div class="conv-list-inner">\n{rows}\n  </div>'
            f'\n</section>'
        )
    return "\n".join(sections)


# === INDEX JSON ===

def write_index_json() -> str:
    items = scan_all()
    path = os.path.join(PUBLIC_DIR, INDEX_JSON)
    os.makedirs(PUBLIC_DIR, exist_ok=True)

    count_by_type = {
        TYPE_CHAT: 0,
        TYPE_EBOOK: 0,
        TYPE_COMIC: 0,
    }
    for it in items:
        t = it.get("type", TYPE_CHAT)
        count_by_type[t] = count_by_type.get(t, 0) + 1

    payload = {
        "count": len(items),
        "count_by_type": count_by_type,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "items": items,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


# === INDEX HTML ===

def write_index_html() -> str:
    items = scan_all()
    path = os.path.join(PUBLIC_DIR, INDEX_HTML)
    os.makedirs(PUBLIC_DIR, exist_ok=True)

    items_html = _render_groups(items)

    total_count = len(items)
    chat_count = sum(1 for it in items if it.get("type") == TYPE_CHAT)
    ebook_count = sum(1 for it in items if it.get("type") == TYPE_EBOOK)
    comic_count = sum(1 for it in items if it.get("type") == TYPE_COMIC)

    generated = time.strftime("%Y-%m-%d %H:%M:%S")
    favicon_link = get_favicon_link()

    html = f"""<!DOCTYPE html>
<html lang="id" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GhostWriter Archive</title>
{favicon_link}
<style>
:root {{
  --bg-primary: #0b0f19;
  --bg-secondary: #0f172a;
  --bg-surface: #1e293b;
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --border-color: #1e293b;
  --border-subtle: #334155;
  --accent: #38bdf8;
  --accent-glow: rgba(56, 189, 248, 0.15);
  --badge-bg: #1e293b;
  --purple: #a78bfa;
  --purple-glow: rgba(167, 139, 250, 0.15);
}}
html[data-theme="light"] {{
  --bg-primary: #f8fafc;
  --bg-secondary: #ffffff;
  --bg-surface: #f1f5f9;
  --text-main: #0f172a;
  --text-muted: #64748b;
  --border-color: #e2e8f0;
  --border-subtle: #cbd5e1;
  --accent: #0284c7;
  --accent-glow: rgba(2, 132, 199, 0.12);
  --badge-bg: #f1f5f9;
  --purple: #7c3aed;
  --purple-glow: rgba(124, 58, 237, 0.12);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
body {{ background: var(--bg-primary); color: var(--text-main); min-height: 100vh; padding: 32px 16px; transition: background 0.3s ease, color 0.3s ease; }}
.container {{ max-width: 900px; margin: 0 auto; }}
.gw-brand {{ display: inline-flex; align-items: center; gap: 0.55rem; text-decoration: none; color: var(--text-main); user-select: none; }}
.gw-logo-svg {{ flex-shrink: 0; display: block; }}
.gw-wordmark {{ font-size: 1.25rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1; }}
.header {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
.title-group {{ display: flex; flex-direction: column; gap: 6px; min-width: 0; }}
.subtitle {{ font-size: 0.78rem; color: var(--text-muted); }}
.theme-btn {{ background: var(--bg-surface); border: 1px solid var(--border-subtle); color: var(--text-muted); width: 38px; height: 38px; border-radius: 10px; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; }}
.theme-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
.controls {{ display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }}
.search-wrapper {{ position: relative; flex: 1; min-width: 220px; display: flex; align-items: center; }}
.search-icon {{ position: absolute; left: 14px; color: var(--text-muted); pointer-events: none; }}
.search-input {{ width: 100%; background: var(--bg-secondary); border: 1px solid var(--border-subtle); color: var(--text-main); padding: 11px 14px 11px 38px; border-radius: 9999px; outline: none; }}
.search-input:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }}
.sort-wrapper {{ position: relative; display: flex; align-items: center; background: var(--bg-secondary); border: 1px solid var(--border-subtle); border-radius: 9999px; padding: 0 4px 0 14px; }}
.sort-wrapper:hover {{ border-color: var(--accent); }}
.sort-wrapper::after {{ content: "▼"; font-size: 0.6rem; color: var(--text-muted); padding-right: 10px; pointer-events: none; }}
.sort-select {{ appearance: none; background: transparent; border: none; color: var(--text-main); padding: 11px 6px 11px 0; font-size: 0.85rem; font-weight: 500; cursor: pointer; outline: none; min-width: 150px; }}
.sort-select option {{ background: var(--bg-secondary); color: var(--text-main); }}

.tabs {{
  display: flex;
  gap: 6px;
  margin-bottom: 22px;
  flex-wrap: wrap;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 4px;
}}
.tab-btn {{
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-muted);
  padding: 8px 14px;
  border-radius: 9999px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  font-family: inherit;
  transition: all 0.18s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}}
.tab-btn:hover {{
  background: var(--bg-surface);
  color: var(--text-main);
}}
.tab-btn.active {{
  background: var(--accent-glow);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}}
.tab-count {{
  font-size: 0.7rem;
  background: var(--bg-surface);
  color: var(--text-muted);
  padding: 1px 7px;
  border-radius: 9999px;
  font-weight: 600;
}}
.tab-btn.active .tab-count {{
  background: var(--accent);
  color: var(--bg-primary);
}}

.stats {{ display: flex; gap: 16px; font-size: 0.78rem; color: var(--text-muted); margin-bottom: 18px; padding: 0 4px; }}
.stats strong {{ color: var(--accent); font-weight: 700; }}
.date-group {{ margin-bottom: 26px; }}
.date-label {{ font-size: 0.7rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 10px; padding: 0 4px; display: flex; align-items: center; gap: 8px; }}
.date-count {{ display: inline-flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 600; color: var(--accent); background: var(--accent-glow); padding: 1px 7px; border-radius: 9999px; letter-spacing: 0; }}
.conv-list-inner {{ display: flex; flex-direction: column; gap: 8px; }}
.conv-item {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 14px; padding: 14px 18px; text-decoration: none; color: inherit; transition: all 0.18s ease; cursor: pointer; }}
.conv-item:hover {{ border-color: var(--accent); background: var(--bg-surface); transform: translateX(2px); }}
.conv-main {{ display: flex; flex-direction: column; gap: 6px; min-width: 0; flex: 1; }}
.conv-title {{ font-size: 0.98rem; font-weight: 600; color: var(--text-main); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center; gap: 6px; }}
.type-badge-inline {{ flex-shrink: 0; font-size: 1.05em; }}
.conv-meta {{ display: flex; gap: 14px; font-size: 0.72rem; color: var(--text-muted); flex-wrap: wrap; }}
.conv-arrow {{ font-size: 1.2rem; color: var(--text-muted); flex-shrink: 0; transition: all 0.18s ease; }}
.conv-item:hover .conv-arrow {{ color: var(--accent); transform: translateX(4px); }}
.empty {{ text-align: center; padding: 64px 20px; background: var(--bg-secondary); border: 1px dashed var(--border-subtle); border-radius: 16px; }}
.empty-icon {{ font-size: 3rem; margin-bottom: 14px; opacity: 0.7; }}
.empty-title {{ font-size: 1.05rem; font-weight: 600; color: var(--text-main); margin-bottom: 6px; }}
.empty-sub {{ font-size: 0.85rem; color: var(--text-muted); }}
.empty code {{ background: var(--bg-surface); padding: 2px 8px; border-radius: 5px; font-family: ui-monospace, monospace; color: var(--accent); font-size: 0.82rem; }}
footer {{ margin-top: 40px; text-align: center; font-size: 0.72rem; color: var(--text-muted); display: flex; align-items: center; justify-content: center; gap: 6px; flex-wrap: wrap; }}
footer .dot {{ opacity: 0.4; }}
footer a {{ color: var(--accent); text-decoration: none; }}
footer a:hover {{ text-decoration: underline; }}
@media (max-width: 500px) {{
  body {{ padding: 20px 12px; }}
  .gw-wordmark {{ font-size: 1.1rem; }}
  .sort-wrapper {{ flex: 1; }}
  .sort-select {{ min-width: 0; flex: 1; }}
  .conv-item {{ padding: 12px 14px; border-radius: 12px; }}
  .conv-title {{ font-size: 0.92rem; }}
  .tab-btn {{ padding: 7px 11px; font-size: 0.8rem; }}
}}
@media print {{
  body {{ background: #fff !important; color: #000 !important; padding: 0; }}
  .theme-btn, .controls, .tabs {{ display: none !important; }}
  .conv-item {{ border: 1px solid #ccc !important; page-break-inside: avoid; }}
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="title-group">
      <a class="gw-brand" href="index.html">
        {LOGO_SVG_INLINE.replace('class="gw-logo-svg"', 'class="gw-logo-svg" width="26" height="26"')}
        <span class="gw-wordmark">GhostWriter</span>
      </a>
      <div class="subtitle">Generated: {generated}</div>
    </div>
    <button class="theme-btn" id="theme-toggle" title="Toggle tema">🌙</button>
  </div>

  <div class="controls">
    <div class="search-wrapper">
      <span class="search-icon">🔍</span>
      <input type="text" class="search-input" id="search-input" placeholder="Cari semua konten... ( / )">
    </div>
    <div class="sort-wrapper">
      <select class="sort-select" id="sort-select">
        <option value="mtime">Terbaru</option>
        <option value="title">Judul (A-Z)</option>
        <option value="msg">Pesan Terbanyak</option>
        <option value="pages">Halaman Terbanyak</option>
        <option value="size">Ukuran Terbesar</option>
      </select>
    </div>
  </div>

  <div class="tabs" id="tabs">
    <button class="tab-btn active" data-type="all">
      <span>📚</span> Semua <span class="tab-count">{total_count}</span>
    </button>
    <button class="tab-btn" data-type="chat">
      <span>💬</span> Chat <span class="tab-count">{chat_count}</span>
    </button>
    <button class="tab-btn" data-type="ebook">
      <span>📖</span> Ebook <span class="tab-count">{ebook_count}</span>
    </button>
    <button class="tab-btn" data-type="comic">
      <span>🎨</span> Comic <span class="tab-count">{comic_count}</span>
    </button>
  </div>

  <div class="stats">
    <span>📚 <strong id="stat-visible">{total_count}</strong> dari <strong id="stat-total">{total_count}</strong> konten</span>
  </div>

  <div id="conv-list-root">
    {items_html}
  </div>

  <footer>
    <span>GhostWriter</span>
    <span class="dot">·</span>
    <span>by <a href="https://github.com/nexterade" target="_blank" rel="noopener">@nexterade</a></span>
  </footer>
</div>

<script>
  const savedTheme = localStorage.getItem("gw-theme");
  if (savedTheme === "light") {{
    document.documentElement.setAttribute("data-theme", "light");
    document.getElementById("theme-toggle").textContent = "☀️";
  }}
  document.getElementById("theme-toggle")?.addEventListener("click", () => {{
    const cur = document.documentElement.getAttribute("data-theme");
    const next = cur === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    document.getElementById("theme-toggle").textContent = next === "light" ? "☀️" : "🌙";
    localStorage.setItem("gw-theme", next);
  }});

  const root = document.getElementById("conv-list-root");
  const allSections = Array.from(root.querySelectorAll(".date-group"));
  const allItems = Array.from(root.querySelectorAll(".conv-item"));
  const tabs = Array.from(document.querySelectorAll(".tab-btn"));

  const STORAGE_KEY_TAB = "gw-active-tab";
  let activeType = localStorage.getItem(STORAGE_KEY_TAB) || "chat";
  if (!["all", "chat", "ebook", "comic"].includes(activeType)) activeType = "chat";

  function applyActiveTab() {{
    tabs.forEach(t => {{
      t.classList.toggle("active", t.getAttribute("data-type") === activeType);
    }});
  }}

  function applyFilterAndSort() {{
    const q = document.getElementById("search-input").value.trim().toLowerCase();
    const sortBy = document.getElementById("sort-select").value;
    const isSearching = q.length > 0;
    let visibleCount = 0;

    allItems.forEach(el => {{
      const itemType = el.getAttribute("data-type") || "chat";
      const matchType = activeType === "all" || itemType === activeType;
      const matchSearch = !q || (el.getAttribute("data-search") || "").includes(q);
      const match = matchType && matchSearch;
      el.style.display = match ? "" : "none";
      if (match) visibleCount++;
    }});

    if (!isSearching) {{
      allSections.forEach(sec => {{
        const items = Array.from(sec.querySelectorAll(".conv-item"));
        const visibleInSection = items.filter(el => el.style.display !== "none");
        sec.style.display = visibleInSection.length > 0 ? "" : "none";

        const inner = sec.querySelector(".conv-list-inner");
        const sorted = sortItems(items, sortBy);
        sorted.forEach(el => inner.appendChild(el));

        const countEl = sec.querySelector(".date-count");
        if (countEl) countEl.textContent = visibleInSection.length;
      }});
      const order = ["Hari Ini", "Kemarin", "7 Hari Terakhir", "30 Hari Terakhir", "Lebih Lama"];
      const sectionMap = {{}};
      allSections.forEach(s => {{ sectionMap[s.dataset.group] = s; }});
      order.forEach(name => {{ if (sectionMap[name]) root.appendChild(sectionMap[name]); }});
    }} else {{
      allSections.forEach(sec => sec.style.display = "none");
      let flat = document.getElementById("flat-results");
      if (!flat) {{
        flat = document.createElement("div");
        flat.id = "flat-results";
        flat.className = "conv-list-inner";
        root.appendChild(flat);
      }}
      flat.style.display = "";
      const matching = allItems.filter(el => el.style.display !== "none");
      const sorted = sortItems(matching, sortBy);
      flat.innerHTML = "";
      sorted.forEach(el => flat.appendChild(el));
    }}

    document.getElementById("stat-visible").textContent = visibleCount;
  }}

  function sortItems(items, sortBy) {{
    const arr = items.slice();
    if (sortBy === "title") arr.sort((a, b) => a.getAttribute("data-title").localeCompare(b.getAttribute("data-title")));
    else if (sortBy === "msg") arr.sort((a, b) => parseInt(b.getAttribute("data-msg")) - parseInt(a.getAttribute("data-msg")));
    else if (sortBy === "pages") arr.sort((a, b) => parseInt(b.getAttribute("data-pages")) - parseInt(a.getAttribute("data-pages")));
    else if (sortBy === "size") arr.sort((a, b) => parseFloat(b.getAttribute("data-size")) - parseFloat(a.getAttribute("data-size")));
    else arr.sort((a, b) => parseFloat(b.getAttribute("data-mtime")) - parseFloat(a.getAttribute("data-mtime")));
    return arr;
  }}

  tabs.forEach(tab => {{
    tab.addEventListener("click", () => {{
      activeType = tab.getAttribute("data-type");
      localStorage.setItem(STORAGE_KEY_TAB, activeType);
      applyActiveTab();
      applyFilterAndSort();
    }});
  }});

  document.getElementById("search-input")?.addEventListener("input", applyFilterAndSort);
  document.getElementById("sort-select")?.addEventListener("change", applyFilterAndSort);

  document.addEventListener("keydown", (e) => {{
    if (e.key === "/" && document.activeElement.tagName !== "INPUT") {{
      e.preventDefault();
      document.getElementById("search-input").focus();
    }}
  }});

  applyActiveTab();
  applyFilterAndSort();
</script>
</body>
</html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def write_all() -> tuple:
    """Return (json_path, html_path)."""
    return write_index_json(), write_index_html()
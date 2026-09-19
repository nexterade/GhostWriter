import os
import re
import shutil
import json
import time
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader

from tools.theme import (
    get_favicon_link,
    LOGO_SVG_INLINE,
)


# === PR-39: Auto-Backup Config ===
MAX_BACKUPS_PER_CONVO = 3  # Simpen maksimal 3 versi lama per convo


def _extract_title_from_html(html_path: str) -> str:
    """Baca <title> dari HTML existing."""
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            head = f.read(4000)
        m = re.search(r"<title>([^<]+)</title>", head, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return ""


def _backup_existing_file(target_path: str) -> str:
    """
    PR-39: Backup file yang ada sebelum ditimpa.

    Return: path backup (kalo berhasil), atau "" (kalo gak ada file / gagal).
    """
    if not os.path.isfile(target_path):
        return ""

    try:
        # Format timestamp: YYYYMMDD-HHMMSS
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        base_dir = os.path.dirname(target_path)
        base_name = os.path.basename(target_path)  # index.html

        # Nama backup: index-20260919-103045.html.bak
        name_no_ext, ext = os.path.splitext(base_name)
        backup_name = f"{name_no_ext}-{timestamp}{ext}.bak"
        backup_path = os.path.join(base_dir, backup_name)

        shutil.copy2(target_path, backup_path)
        return backup_path
    except OSError:
        return ""


def _prune_old_backups(target_dir: str, max_keep: int = MAX_BACKUPS_PER_CONVO):
    """
    PR-39: Hapus backup lama, simpen maksimal `max_keep` versi terbaru.

    Backup file pattern: index-YYYYMMDD-HHMMSS.html.bak
    """
    if not os.path.isdir(target_dir):
        return

    try:
        entries = os.listdir(target_dir)
    except OSError:
        return

    # Filter backup files, sort by mtime (paling lama duluan)
    backups = []
    for name in entries:
        if not name.endswith(".html.bak"):
            continue
        full_path = os.path.join(target_dir, name)
        try:
            mtime = os.path.getmtime(full_path)
            backups.append((mtime, full_path))
        except OSError:
            continue

    backups.sort(key=lambda x: x[0])  # asc — paling lama di depan

    # Kalo lebih dari max_keep, hapus yang paling lama
    if len(backups) > max_keep:
        for _, old_path in backups[: len(backups) - max_keep]:
            try:
                os.remove(old_path)
            except OSError:
                pass


class HTMLExporter:
    """Class untuk mengekspor data percakapan standar ke file HTML mandiri."""

    def __init__(self, template_dir: str = "templates", template_name: str = "viewer.html"):
        self.template_dir = template_dir
        self.template_name = template_name
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True
        )

    def _ensure_vendor(self, output_dir: str):
        """
        Copy vendor assets ke public/vendor/ (shared, bukan per-convo).

        Struktur:
            public/
            ├── vendor/                    <- taruh di sini
            └── history/
                └── <id>/
                    └── index.html         <- viewer (2-level up ke vendor)
        """
        src = "vendor"
        if not os.path.isdir(src):
            return

        abs_out = os.path.abspath(output_dir)
        abs_public = os.path.abspath("public")

        # Kalo output di dalam public/ -> taruh vendor di public/vendor/
        if abs_out.startswith(abs_public + os.sep) and abs_out != abs_public:
            target_parent = abs_public
        else:
            # Fallback: taruh di folder output
            target_parent = abs_out

        dst = os.path.join(target_parent, "vendor")

        if os.path.abspath(src) == os.path.abspath(dst):
            return

        # BUG #2 FIX: Cek isi folder, bukan cuma eksistensi folder.
        # Kalo folder ada tapi kosong -> hapus dulu, baru copy ulang.
        if os.path.isdir(dst):
            try:
                if os.listdir(dst):
                    return  # udah ada isinya, skip
            except OSError:
                pass
            try:
                shutil.rmtree(dst)
            except OSError as e:
                print(f"[!] Gagal hapus vendor kosong: {e}")
                return

        try:
            shutil.copytree(src, dst)
        except OSError as e:
            print(f"[!] Gagal copy vendor: {e}")

    def export(
        self,
        data: Dict[str, Any],
        output_path: str,
        convo_count: int = 1,
        convo_id: str = "",
    ) -> str:
        title = data.get("title", "GhostWriter Archive")

        out_dir = os.path.dirname(output_path) or "."
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        self._ensure_vendor(out_dir)

        # === PR-39: Auto-backup sebelum overwrite ===
        backup_path = _backup_existing_file(output_path)
        if backup_path:
            try:
                from tools.loading import print_info
                print_info(f"Backup: {os.path.basename(backup_path)}")
            except Exception:
                pass

        # === PR-39: Prune backup lama ===
        _prune_old_backups(out_dir, max_keep=MAX_BACKUPS_PER_CONVO)

        template = self.env.get_template(self.template_name)
        rendered_html = template.render(
            title=title,
            created_at=data.get("created_at", "Unknown Date"),
            messages=data.get("messages", []),
            messages_json=json.dumps(data.get("messages", []), ensure_ascii=False),
            convo_count=convo_count,
            convo_id=convo_id,
            favicon_link=get_favicon_link(),
            logo_svg=LOGO_SVG_INLINE,
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        # Auto-update index
        try:
            from tools.dist_index import write_all
            json_path, html_path = write_all()
        except Exception as e:
            try:
                from tools.loading import print_warn
                print_warn(f"Gagal update index: {e}")
            except Exception:
                print(f"[!] Gagal update index: {e}")

        return os.path.abspath(output_path)
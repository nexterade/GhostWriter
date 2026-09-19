import os
import re
import shutil
import json
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader

from tools.theme import (
    get_favicon_link,
    LOGO_SVG_INLINE,
)


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
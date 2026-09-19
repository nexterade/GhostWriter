import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from parsers.base import BaseParser


ROLE_ALIASES = {
    "user": "user",
    "human": "user",
    "you": "user",
    "me": "user",
    "assistant": "assistant",
    "ai": "assistant",
    "bot": "assistant",
    "deepseek": "assistant",
    "chatgpt": "assistant",
    "claude": "assistant",
    "gemini": "assistant",
    "system": "system",
}

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
BOLD_PATTERN = re.compile(r"^\*\*(.+?):?\*\*\s*$")
ITALIC_PATTERN = re.compile(r"^\*(.+?):?\*\s*$")


class MarkdownChatParser(BaseParser):
    """Parser untuk file .md dengan format chat mentah (heading user/assistant)."""

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.raw_text = None

    def validate(self) -> bool:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.raw_text = f.read()
            return bool(self.raw_text and self.raw_text.strip())
        except Exception:
            return False

    def _match_role(self, candidate: str) -> Optional[str]:
        """Cocokin string ke role alias. Return normalized role atau None."""
        if not candidate:
            return None
        clean = candidate.strip().strip(":").strip().lower()
        clean = re.sub(r"[^a-z]", "", clean)
        return ROLE_ALIASES.get(clean)

    def _detect_header(self, line: str) -> Optional[tuple]:
        """
        Deteksi apakah line adalah header role.
        Return (role, level) atau None.
        Support: '## User', '### Assistant', '**User:**', '*AI*'
        """
        stripped = line.strip()
        if not stripped:
            return None

        m = HEADING_PATTERN.match(stripped)
        if m:
            level = len(m.group(1))
            role = self._match_role(m.group(2))
            if role:
                return (role, level)

        m = BOLD_PATTERN.match(stripped)
        if m:
            role = self._match_role(m.group(1))
            if role:
                return (role, 0)

        m = ITALIC_PATTERN.match(stripped)
        if m:
            role = self._match_role(m.group(1))
            if role:
                return (role, 0)

        return None

    def _extract_title(self) -> str:
        """Ambil judul dari H1 pertama, atau fallback ke nama file."""
        if not self.raw_text:
            return "Markdown Chat"
        for line in self.raw_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                return stripped[2:].strip() or "Markdown Chat"
        base = os.path.splitext(os.path.basename(self.file_path))[0]
        return base or "Markdown Chat"

    def list_conversations(self) -> List[Dict[str, Any]]:
        return [{
            "index": 0,
            "title": self._extract_title(),
            "created_at": "",
            "node_count": 0,
        }]

    def parse(self, convo_index: Optional[int] = None) -> Dict[str, Any]:
        if self.raw_text is None:
            if not self.validate():
                raise ValueError(f"Gagal membaca file markdown: {self.file_path}")

        title = self._extract_title()
        lines = self.raw_text.splitlines()

        messages: List[Dict[str, str]] = []
        current_role: Optional[str] = None
        current_buffer: List[str] = []
        min_heading_level = 6

        def flush():
            if current_role is None:
                return
            content = "\n".join(current_buffer).strip()
            if content:
                messages.append({
                    "role": current_role,
                    "content": content,
                    "timestamp": "",
                })

        for line in lines:
            header = self._detect_header(line)
            if header:
                role, level = header
                flush()
                current_role = role
                current_buffer = []
                if level > 0:
                    min_heading_level = min(min_heading_level, level)
                continue

            if current_role is not None:
                current_buffer.append(line)

        flush()

        if min_heading_level < 6:
            strip_pattern = re.compile(r"^#{1," + str(min_heading_level) + r"}\s+")
            pass

        created_at = datetime.fromtimestamp(
            os.path.getmtime(self.file_path)
        ).strftime("%Y-%m-%d %H:%M") if os.path.exists(self.file_path) else ""

        return {
            "title": title,
            "created_at": created_at,
            "messages": messages,
        }
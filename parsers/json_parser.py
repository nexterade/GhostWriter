import os
import json
import base64
import mimetypes
from datetime import datetime
from typing import Dict, Any, List, Optional
from parsers.base import BaseParser


class JSONChatParser(BaseParser):
    """Parser adaptif untuk export ChatGPT, DeepSeek, dan JSON generik dengan resolusi file absolut."""

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.raw_data = None
        self.base_dir = os.path.dirname(os.path.abspath(file_path))

    def validate(self) -> bool:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.raw_data = json.load(f)
            return True
        except Exception:
            return False

    def list_conversations(self) -> List[Dict[str, Any]]:
        if self.raw_data is None and not self.validate():
            return []

        convo_list = []
        if isinstance(self.raw_data, list):
            for idx, item in enumerate(self.raw_data):
                if not isinstance(item, dict):
                    continue

                # Format DeepSeek raw: {chat_session: {...}, chat_messages: [...]}
                if "chat_messages" in item:
                    session = item.get("chat_session", {}) or {}
                    title = session.get("title") or f"Obrolan #{idx + 1} (DeepSeek)"
                    inserted = session.get("inserted_at") or item.get("inserted_at")
                    time_str = self._format_epoch(inserted)
                    convo_list.append({
                        "index": idx,
                        "title": title,
                        "created_at": time_str,
                        "node_count": len(item.get("chat_messages", []) or []),
                    })
                    continue

                # Format OpenAI mapping / generic
                title = (item.get("title", "") or "").strip() or f"Obrolan #{idx + 1} (Tanpa Judul)"
                raw_time = item.get("inserted_at") or item.get("create_time", "")
                time_str = self._format_epoch(raw_time)

                node_count = len(item.get("mapping", {}) or {})
                convo_list.append({
                    "index": idx,
                    "title": title,
                    "created_at": time_str,
                    "node_count": node_count,
                })

        elif isinstance(self.raw_data, dict):
            if "chat_messages" in self.raw_data:
                session = self.raw_data.get("chat_session", {}) or {}
                convo_list.append({
                    "index": 0,
                    "title": session.get("title") or "DeepSeek Chat",
                    "created_at": self._format_epoch(session.get("inserted_at")),
                    "node_count": len(self.raw_data.get("chat_messages", []) or []),
                })
            else:
                title = self.raw_data.get("title", "Obrolan Tunggal")
                convo_list.append({
                    "index": 0,
                    "title": title,
                    "created_at": "",
                    "node_count": len(self.raw_data.get("mapping", {}) or {}),
                })

        return convo_list

    def parse(self, convo_index: Optional[int] = None) -> Dict[str, Any]:
        if self.raw_data is None:
            if not self.validate():
                raise ValueError(f"Gagal memvalidasi atau membaca file JSON: {self.file_path}")

        # Format: array of conversations (bulk backup, atau list dari extension)
        if isinstance(self.raw_data, list) and len(self.raw_data) > 0:
            if convo_index is not None and 0 <= convo_index < len(self.raw_data):
                target_convo = self.raw_data[convo_index]
            else:
                target_convo = self._pick_best_conversation(self.raw_data)

            if not isinstance(target_convo, dict):
                raise ValueError("Item percakapan bukan object JSON yang valid.")

            if "chat_messages" in target_convo:
                return self._parse_deepseek_raw(target_convo)
            return self._parse_conversation_node(target_convo)

        # Format: single conversation (dict)
        if isinstance(self.raw_data, dict):
            if "chat_messages" in self.raw_data:
                return self._parse_deepseek_raw(self.raw_data)
            if "mapping" in self.raw_data:
                return self._parse_conversation_node(self.raw_data)
            if "messages" in self.raw_data:
                return self._parse_generic_dict(self.raw_data)

        raise ValueError("Format JSON tidak dikenali.")

    def _pick_best_conversation(self, convo_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        for convo in convo_list:
            if not isinstance(convo, dict):
                continue
            session = convo.get("chat_session") if "chat_messages" in convo else convo
            title = (session or {}).get("title", "") or ""
            if title.strip():
                return convo
        return convo_list[0]

    def _format_epoch(self, raw: Any) -> str:
        """Convert epoch float/int atau string ISO ke 'YYYY-MM-DD HH:MM'."""
        if raw is None or raw == "":
            return ""
        if isinstance(raw, (int, float)):
            try:
                return datetime.fromtimestamp(raw).strftime("%Y-%m-%d %H:%M")
            except (OSError, ValueError, OverflowError):
                return ""
        return str(raw)[:16].replace("T", " ")

    def _find_local_file(self, filename: str) -> Optional[str]:
        """Mencari lokasi fisik file di direktori kerja aktif dan folder attachments."""
        cwd = os.getcwd()
        candidates = [
            os.path.join(cwd, "attachments", filename),
            os.path.join(cwd, filename),
            os.path.join(self.base_dir, "attachments", filename),
            os.path.join(self.base_dir, filename),
        ]
        for path in candidates:
            if os.path.exists(path) and os.path.isfile(path) and os.path.getsize(path) > 0:
                return os.path.abspath(path)
        return None

    def _format_size(self, size_bytes: Optional[int]) -> str:
        if not size_bytes or size_bytes <= 0:
            return ""
        val = float(size_bytes)
        if val < 1024:
            return f"{int(val)} B"
        elif val < 1024 * 1024:
            return f"{val / 1024:.1f} KB"
        else:
            return f"{val / (1024 * 1024):.1f} MB"

    def _build_attachment_card(self, file_info: Dict[str, Any]) -> str:
        name = file_info.get("file_name") or file_info.get("name") or "Attachment"
        size_bytes = file_info.get("file_size") or file_info.get("size")
        size_str = self._format_size(size_bytes)

        _, ext = os.path.splitext(name)
        ext = ext.lower().replace(".", "")

        icon = "📄"
        if ext in ["png", "jpg", "jpeg", "webp", "gif"]:
            icon = "🖼️"
        elif ext in ["py", "js", "html", "css", "json", "sh"]:
            icon = "💻"
        elif ext in ["zip", "rar", "tar", "gz", "7z"]:
            icon = "📦"
        elif ext in ["pdf", "doc", "docx", "txt", "md"]:
            icon = "📝"

        local_path = self._find_local_file(name)
        preview_html = ""

        if local_path and ext in ["png", "jpg", "jpeg", "webp", "gif"]:
            try:
                mime, _ = mimetypes.guess_type(local_path)
                mime = mime or "image/png"
                with open(local_path, "rb") as img_f:
                    b64 = base64.b64encode(img_f.read()).decode("utf-8")
                preview_html = f'<div class="attachment-preview-img"><img src="data:{mime};base64,{b64}" alt="{name}"/></div>'
            except Exception:
                preview_html = ""

        card_html = (
            f'<div class="attachment-box">'
            f'{preview_html}'
            f'<div class="attachment-info">'
            f'<span class="attachment-icon">{icon}</span>'
            f'<div class="attachment-text">'
            f'<span class="attachment-name" title="{name}">{name}</span>'
            f'<span class="attachment-size">{size_str}</span>'
            f'</div></div></div>'
        )
        return card_html

    def _parse_deepseek_raw(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse format raw API DeepSeek: {chat_session: {...}, chat_messages: [...]}.
        Flat array, 1 objek = 1 pesan, ada files/thinking_content/search_results.
        """
        session = data.get("chat_session", {}) or {}
        title = session.get("title") or "DeepSeek Chat"
        created_str = self._format_epoch(session.get("inserted_at") or data.get("inserted_at"))

        chat_messages = data.get("chat_messages", []) or []
        messages: List[Dict[str, str]] = []

        for msg in chat_messages:
            if not isinstance(msg, dict):
                continue

            role_raw = (msg.get("role") or "").lower()
            role = "user" if role_raw == "user" else "assistant"

            content = msg.get("content") or ""
            thinking = msg.get("thinking_content")
            files = msg.get("files") or []
            search_results = msg.get("search_results") or []

            timestamp = self._format_epoch(msg.get("inserted_at"))
            time_display = timestamp.split(" ")[-1] if " " in timestamp else timestamp

            parts: List[str] = []

            # Attachment cards (umumnya di pesan user)
            if files:
                cards = []
                for f in files:
                    if isinstance(f, dict):
                        card = self._build_attachment_card(f)
                        if card:
                            cards.append(card)
                if cards:
                    parts.append("".join(cards))

            # Thinking process (khusus assistant, kalo ada DeepThink)
            if role == "assistant" and thinking:
                parts.append(
                    "<details style='margin-bottom: 12px; opacity: 0.85; border-left: 2px solid #38bdf8; padding-left: 8px;'>"
                    "<summary style='cursor: pointer; color: #38bdf8; font-weight: 500;'>Thought Process (Penalaran)</summary>\n\n"
                    f"> {thinking}\n\n"
                    "</details>"
                )

            # Body text
            if content and content.strip():
                parts.append(content)

            # Search citations (khusus assistant)
            if role == "assistant" and search_results:
                citations = []
                for sr in search_results:
                    if not isinstance(sr, dict):
                        continue
                    url = sr.get("url", "")
                    sr_title = sr.get("title") or url
                    if url:
                        citations.append(
                            f'<li><a href="{url}" target="_blank" rel="noopener">{sr_title}</a></li>'
                        )
                if citations:
                    parts.append(
                        "<details style='margin-top: 12px; font-size: 0.9em; opacity: 0.8;'>"
                        f"<summary style='cursor: pointer;'>🔗 {len(citations)} Sumber Referensi</summary>"
                        f"<ul style='margin-top: 8px;'>{''.join(citations)}</ul>"
                        "</details>"
                    )

            combined = "\n\n".join(p for p in parts if p and p.strip())
            if not combined.strip():
                continue

            messages.append({
                "role": role,
                "content": combined,
                "timestamp": time_display,
            })

        return {
            "title": title,
            "created_at": created_str,
            "messages": messages,
        }

    def _parse_conversation_node(self, convo: Dict[str, Any]) -> Dict[str, Any]:
        title = convo.get("title") or "Obrolan AI"

        created_str = ""
        if "inserted_at" in convo:
            created_str = str(convo["inserted_at"])[:16].replace("T", " ")
        elif "create_time" in convo:
            ct = convo["create_time"]
            created_str = datetime.fromtimestamp(ct).strftime("%Y-%m-%d %H:%M") if ct else ""

        mapping = convo.get("mapping", {}) or {}
        messages: List[Dict[str, str]] = []

        for node_id, node in mapping.items():
            if not isinstance(node, dict):
                continue
            msg_obj = node.get("message")
            if not msg_obj:
                continue

            if "fragments" in msg_obj:
                fragments = msg_obj.get("fragments", []) or []
                user_text = []
                user_attachments = []
                ai_text = []
                think_text = []

                for frag in fragments:
                    if not isinstance(frag, dict):
                        continue
                    f_type = frag.get("type")
                    content = frag.get("content", "")

                    if f_type == "REQUEST":
                        user_text.append(content)
                    elif f_type == "RESPONSE":
                        ai_text.append(content)
                    elif f_type == "THINK":
                        think_text.append(content)
                    elif f_type == "FILE":
                        for f in frag.get("files", []) or []:
                            if isinstance(f, dict):
                                user_attachments.append(self._build_attachment_card(f))

                ins_time = str(msg_obj.get("inserted_at", ""))[:16].replace("T", " ")
                time_display = ins_time.split(" ")[-1] if " " in ins_time else ""

                if user_text or user_attachments:
                    combined_attachments = "".join(user_attachments)
                    body_text = "\n\n".join(user_text) if user_text else ""

                    combined_content = ""
                    if combined_attachments:
                        combined_content += f"{combined_attachments}\n\n"
                    if body_text:
                        combined_content += body_text

                    messages.append({
                        "role": "user",
                        "content": combined_content.strip(),
                        "timestamp": time_display,
                    })

                if ai_text or think_text:
                    full_ai_content = ""
                    if think_text:
                        full_ai_content += (
                            "<details style='margin-bottom: 12px; opacity: 0.85; border-left: 2px solid #38bdf8; padding-left: 8px;'>"
                            "<summary style='cursor: pointer; color: #38bdf8; font-weight: 500;'>Thought Process (Penalaran)</summary>\n\n"
                            f"> {think_text[0]}\n\n"
                            "</details>\n\n"
                        )
                    if ai_text:
                        full_ai_content += "\n\n".join(ai_text)

                    if full_ai_content.strip():
                        messages.append({
                            "role": "assistant",
                            "content": full_ai_content,
                            "timestamp": time_display,
                        })

            elif "author" in msg_obj:
                author = msg_obj.get("author", {})
                role = author.get("role")
                if role not in ["user", "assistant"]:
                    continue

                content_obj = msg_obj.get("content", {})
                parts = content_obj.get("parts", [])
                text_content = "".join([str(p) for p in parts if isinstance(p, str)])

                if not text_content.strip():
                    continue

                msg_time = msg_obj.get("create_time")
                time_str = datetime.fromtimestamp(msg_time).strftime("%H:%M") if msg_time else ""

                messages.append({
                    "role": role,
                    "content": text_content,
                    "timestamp": time_str,
                })

        return {
            "title": title,
            "created_at": created_str,
            "messages": messages,
        }

    def _parse_generic_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": data.get("title", "Obrolan AI"),
            "created_at": data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M")),
            "messages": [
                {
                    "role": m.get("role", "user"),
                    "content": m.get("content", ""),
                    "timestamp": m.get("timestamp", ""),
                }
                for m in data.get("messages", [])
                if isinstance(m, dict)
            ],
        }
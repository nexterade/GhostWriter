import os
import json
import time
import random
import sys
import requests
from typing import Dict, Any, List, Optional, Tuple, Callable

from tools.loading import (
    LoadingSpinner, print_status, print_success, print_error,
    print_warn, print_info, print_section, print_kv, print_bullet,
    print_numbered, progress_bar
)
from tools.theme import C, get_theme


DEEPSEEK_API_BASE = "https://chat.deepseek.com/api/v0"
MAX_RETRIES = 3
RETRY_BACKOFF = 1.5

DELAY_MIN = float(os.environ.get("GW_DELAY_MIN", "1.0"))
DELAY_MAX = float(os.environ.get("GW_DELAY_MAX", "3.0"))
SESSION_DELAY_MIN = float(os.environ.get("GW_SESSION_DELAY_MIN", "3.0"))
SESSION_DELAY_MAX = float(os.environ.get("GW_SESSION_DELAY_MAX", "7.0"))
RETRY_DELAY_MIN = float(os.environ.get("GW_RETRY_DELAY_MIN", "5.0"))
RETRY_DELAY_MAX = float(os.environ.get("GW_RETRY_DELAY_MAX", "10.0"))

STATE_FILE = "deepseek_backup_state.json"

VALID_ATTACHMENT_EXT = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp",
    ".pdf", ".txt", ".csv", ".json", ".zip",
    ".mp3", ".wav", ".mp4", ".mov", ".webm",
}

MAGIC_SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpeg"),
    (b"%PDF-", "pdf"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
    (b"PK\x03\x04", "zip/docx/xlsx"),
]


# === CUSTOM EXCEPTIONS ===
class AuthExpiredError(Exception):
    """Token expired / invalid — dipake buat mbedain dari error biasa."""
    pass


class InvalidResponseError(Exception):
    """Response dari API strukturnya gak valid."""
    pass


def _human_delay(label: str = ""):
    d = random.uniform(DELAY_MIN, DELAY_MAX)
    if label:
        print_info(f"{label} — delay {d:.1f}s")
    time.sleep(d)


def _session_delay(label: str = ""):
    d = random.uniform(SESSION_DELAY_MIN, SESSION_DELAY_MAX)
    if label:
        print_info(f"{label} — delay {d:.1f}s")
    time.sleep(d)


def _retry_delay(label: str = ""):
    d = random.uniform(RETRY_DELAY_MIN, RETRY_DELAY_MAX)
    if label:
        print_warn(f"{label} — retry dalam {d:.1f}s")
    time.sleep(d)


def _looks_like_binary(content: bytes) -> Tuple[bool, str]:
    if len(content) < 4:
        return False, "too-short"
    for sig, name in MAGIC_SIGNATURES:
        if content.startswith(sig):
            return True, name
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return True, "webp"
    sample = content[:512]
    non_printable = sum(1 for b in sample if b < 9 or (13 < b < 32) or b > 126)
    if non_printable / max(len(sample), 1) > 0.10:
        return True, "unknown-binary"
    return False, "text-like"


def _load_state() -> Dict[str, Any]:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"sessions": {}}


def _save_state(state: Dict[str, Any]):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print_error(f"Gagal simpan state: {e}")


def _extract_biz_data(payload: Any) -> Dict[str, Any]:
    """Extract biz_data dari response, dengan guard clause."""
    if not isinstance(payload, dict):
        return {}

    data = payload.get("data")
    if not isinstance(data, dict):
        return {}

    biz = data.get("biz_data")
    if isinstance(biz, dict):
        return biz

    return data


def _detect_auth_error(payload: Any) -> bool:
    """Detect apakah response nunjukin token expired / invalid."""
    if not isinstance(payload, dict):
        return False

    code = payload.get("code")
    if code in (401, 403):
        return True

    data = payload.get("data")
    if isinstance(data, dict):
        inner_code = data.get("code")
        if inner_code in (401, 403):
            return True

    msg = str(payload.get("msg") or payload.get("message") or "").lower()
    auth_keywords = ("token expired", "invalid token", "unauthorized", "token invalid", "auth failed")
    if any(kw in msg for kw in auth_keywords):
        return True

    return False


# === MESSAGE PROGRESS ===
class MessageProgress:
    """Progress bar per-message. Update di baris yang sama pake \\r + \\033[K."""

    def __init__(self, session_label: str = ""):
        self.total = 0
        self.current = 0
        self.session_label = session_label
        self.enabled = get_theme().enabled
        self._last_width = 0

    def set_total(self, total: int):
        self.total = total
        self.current = 0
        self._render()

    def increment(self, n: int = 1):
        self.current += n
        if self.current > self.total:
            self.current = self.total
        self._render()

    def _render(self):
        if not self.enabled or self.total == 0:
            return

        pct = min(self.current / self.total, 1.0)
        width = 20
        filled = int(width * pct)
        empty = width - filled

        if filled > 0:
            fill_mid = filled // 2
            bar = (
                C.ACCENT_DIM + "█" * fill_mid
                + C.ACCENT + "█" * (filled - fill_mid)
            )
        else:
            bar = ""
        empty_bar = C.GRAY + C.DIM + "░" * empty + C.RESET

        pct_color = C.GREEN if pct >= 0.75 else (C.YELLOW if pct >= 0.4 else C.ACCENT)
        label = f" {C.GRAY}{self.session_label}{C.RESET}" if self.session_label else ""

        line = (
            f"  {C.GRAY}[{C.RESET}{bar}{empty_bar}{C.GRAY}]{C.RESET} "
            f"{pct_color}{self.current}/{self.total}{C.RESET} {C.DIM}pesan{C.RESET}"
            f"{label}"
        )

        import re
        ansi_re = re.compile(r"\033\[[0-9;]*m")
        plain_len = len(ansi_re.sub("", line))
        pad = max(0, self._last_width - plain_len)
        self._last_width = plain_len

        sys.stdout.write(f"\r\033[K{line}{' ' * pad}")
        sys.stdout.flush()

    def finish(self, final_label: str = None):
        if not self.enabled:
            return
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()
        if final_label:
            print_success(final_label)


class DeepSeekLiveBackup:
    def __init__(self, user_token: str, download_dir: str = "attachments",
                 incremental: bool = True, force_full: bool = False):
        self.token = user_token.strip()
        self.download_dir = download_dir
        self.incremental = incremental
        self.force_full = force_full
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
            "Content-Type": "application/json",
            "Accept": "*/*",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.pending_attachments: List[Dict[str, Any]] = []
        self._processed_attachments = set()
        self._attachment_download_disabled = False
        self.token_expired = False
        os.makedirs(self.download_dir, exist_ok=True)
        self.state = _load_state()

    def _request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        kwargs.setdefault("timeout", 20)
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                res = self.session.request(method, url, **kwargs)
                if res.status_code in (429, 500, 502, 503, 504):
                    if attempt < MAX_RETRIES:
                        _retry_delay(f"Status {res.status_code}, retry {attempt}/{MAX_RETRIES}")
                        continue
                return res
            except requests.RequestException as e:
                if attempt < MAX_RETRIES:
                    _retry_delay(f"Koneksi error: {e}")
                else:
                    print_error(f"Gagal setelah {MAX_RETRIES} percobaan: {e}")
                    return None
        return None

    def _safe_json(self, res: requests.Response) -> Any:
        """Parse JSON dengan aman. Return None kalo gagal."""
        if res is None:
            return None
        try:
            return res.json()
        except ValueError:
            return None

    def _check_auth_from_response(self, res: requests.Response) -> bool:
        """Cek apakah response nunjukin token expired."""
        if res is None:
            return False

        if res.status_code in (401, 403):
            self.token_expired = True
            return True

        payload = self._safe_json(res)
        if _detect_auth_error(payload):
            self.token_expired = True
            return True

        return False

    def test_connection(self) -> bool:
        """Verify token. Return False kalo invalid / expired."""
        res = self._request("GET", f"{DEEPSEEK_API_BASE}/users/current", timeout=10)
        if res is None:
            return False

        if res.status_code != 200:
            if res.status_code in (401, 403):
                self.token_expired = True
            return False

        if self._check_auth_from_response(res):
            return False

        payload = self._safe_json(res)
        if not isinstance(payload, dict):
            return False

        return True

    def fetch_session_list(self, max_pages: int = 20) -> List[Dict[str, Any]]:
        all_sessions: List[Dict[str, Any]] = []
        next_page_id: Optional[str] = None
        seen_ids = set()

        spinner = LoadingSpinner("Mengambil daftar obrolan...")
        spinner.start()

        try:
            for page in range(1, max_pages + 1):
                url = f"{DEEPSEEK_API_BASE}/chat_session/fetch_page"
                params = {}
                if next_page_id:
                    params["next_page_id"] = next_page_id

                spinner.update(f"Fetch page {page}... ({len(all_sessions)} obrolan)")

                res = self._request("GET", url, params=params)

                if self._check_auth_from_response(res):
                    spinner.stop("Token expired — silakan login ulang", status="error")
                    raise AuthExpiredError("Token expired saat fetch daftar obrolan")

                if res is None or res.status_code != 200:
                    status = res.status_code if res else "no-response"
                    spinner.stop(f"Gagal fetch page {page} (Status {status})", status="error")
                    break

                data = self._safe_json(res)
                if not isinstance(data, dict):
                    spinner.stop(
                        f"Response page {page} bukan dict (got {type(data).__name__})",
                        status="error"
                    )
                    break

                biz = _extract_biz_data(data)
                sessions = (
                    biz.get("chat_sessions")
                    or biz.get("sessions")
                    or biz.get("items")
                    or []
                )

                if not isinstance(sessions, list):
                    sessions = []

                if not sessions:
                    break

                new_count = 0
                for s in sessions:
                    if not isinstance(s, dict):
                        continue
                    s_id = s.get("id")
                    if s_id and s_id not in seen_ids:
                        seen_ids.add(s_id)
                        all_sessions.append(s)
                        new_count += 1

                spinner.update(f"Page {page}: +{new_count} (total: {len(all_sessions)})")

                next_page_id = (
                    biz.get("next_page_id")
                    or biz.get("next")
                    or biz.get("cursor")
                    or None
                )
                if not next_page_id or new_count == 0:
                    break

                _human_delay(f"Pindah ke page {page + 1}")
        finally:
            if spinner.running:
                spinner.stop(f"Selesai — {len(all_sessions)} obrolan diambil", status="ok")

        return all_sessions

    def fetch_session_detail(self, session_id: str) -> Optional[Dict[str, Any]]:
        url = f"{DEEPSEEK_API_BASE}/chat/history_messages"
        params = {"chat_session_id": session_id}
        res = self._request("GET", url, params=params, timeout=25)

        if self._check_auth_from_response(res):
            raise AuthExpiredError("Token expired saat fetch detail obrolan")

        if res is None or res.status_code != 200:
            return None

        data = self._safe_json(res)
        if not isinstance(data, dict):
            return None

        return _extract_biz_data(data)

    # ============================================================
    # STATE MANAGEMENT (PER-OBROLAN)
    # ============================================================

    def _get_last_message_id(self, session_id: str) -> Optional[int]:
        return self.state.get("sessions", {}).get(session_id, {}).get("last_message_id")

    def _update_last_message_id(self, session_id: str, message_id: int):
        if "sessions" not in self.state:
            self.state["sessions"] = {}
        if session_id not in self.state["sessions"]:
            self.state["sessions"][session_id] = {}
        self.state["sessions"][session_id]["last_message_id"] = message_id
        self.state["sessions"][session_id]["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    # ============================================================
    # MESSAGE PARSING
    # ============================================================

    def _resolve_role(self, msg, fragments):
        for key in ("role", "author", "sender"):
            val = msg.get(key)
            if isinstance(val, str) and val.lower() in ("user", "assistant", "system"):
                return val.lower()
        inner = msg.get("message")
        if isinstance(inner, dict):
            for key in ("role", "author"):
                val = inner.get(key)
                if isinstance(val, str) and val.lower() in ("user", "assistant", "system"):
                    return val.lower()
        if fragments:
            types = {f.get("type") for f in fragments if isinstance(f, dict)}
            if "REQUEST" in types and "RESPONSE" not in types:
                return "user"
            if "RESPONSE" in types and "REQUEST" not in types:
                return "assistant"
        return "assistant"

    def _extract_content(self, msg, fragments):
        parts = []
        for frag in fragments:
            if not isinstance(frag, dict):
                continue
            ftype = frag.get("type")
            if ftype in ("REQUEST", "RESPONSE", "TEXT"):
                c = frag.get("content")
                if isinstance(c, str) and c.strip():
                    parts.append(c)
        if parts:
            return "\n\n".join(parts)
        c = msg.get("content")
        if isinstance(c, str):
            return c
        inner = msg.get("message")
        if isinstance(inner, dict):
            c = inner.get("content")
            if isinstance(c, str):
                return c
        return ""

    def _normalize_timestamp(self, raw):
        if raw is None:
            return ""
        if isinstance(raw, (int, float)):
            try:
                return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(raw))
            except (OSError, ValueError):
                return ""
        return str(raw)

    # ============================================================
    # ATTACHMENT DOWNLOAD
    # ============================================================

    def download_attachment(self, file_id, file_name, file_size=None, skip_if_local=False):
        save_path = os.path.join(self.download_dir, file_name)
        attachment_key = (file_id, file_name)

        # === EARLY RETURNS (sebelum delay & network) ===

        if attachment_key in self._processed_attachments:
            return "skipped"
        self._processed_attachments.add(attachment_key)

        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            local_size = os.path.getsize(save_path)
            if not (file_size and local_size != file_size):
                return "success"

        if skip_if_local:
            return "skipped"

        # Circuit breaker aktif
        if self._attachment_download_disabled:
            self.pending_attachments.append({
                "file_name": file_name, "file_id": file_id,
                "file_size": file_size, "reason": "circuit_breaker_active",
            })
            return "pending"

        if not file_id:
            self.pending_attachments.append({
                "file_name": file_name, "file_id": None,
                "file_size": file_size, "reason": "no_file_id",
            })
            return "pending"

        _human_delay()
        url = f"{DEEPSEEK_API_BASE}/file/download"
        res = self._request("GET", url, params={"file_id": file_id}, timeout=30, allow_redirects=True)

        if res is None:
            self.pending_attachments.append({
                "file_name": file_name, "file_id": file_id,
                "file_size": file_size, "reason": "request_failed",
            })
            return "pending"

        ctype = res.headers.get("Content-Type", "").lower()

        if "application/json" in ctype:
            payload = self._safe_json(res)
            download_url = None
            if isinstance(payload, dict):
                biz = _extract_biz_data(payload)
                download_url = (
                    biz.get("url") or biz.get("download_url")
                    or payload.get("url")
                )
                if not download_url and isinstance(payload.get("data"), dict):
                    download_url = payload["data"].get("url")

            if download_url:
                res = self._request("GET", download_url, timeout=60, stream=True)
                if res is None:
                    self.pending_attachments.append({
                        "file_name": file_name, "file_id": file_id,
                        "file_size": file_size, "reason": "presigned_url_failed",
                    })
                    return "pending"
                ctype = res.headers.get("Content-Type", "").lower()

        if "text/html" in ctype:
            self._attachment_download_disabled = True
            self.pending_attachments.append({
                "file_name": file_name, "file_id": file_id,
                "file_size": file_size, "reason": "html_response_need_session",
            })
            return "pending"

        if res.status_code != 200 or len(res.content) == 0:
            self.pending_attachments.append({
                "file_name": file_name, "file_id": file_id,
                "file_size": file_size, "reason": f"status_{res.status_code}",
            })
            return "pending"

        is_binary, fmt = _looks_like_binary(res.content)
        if not is_binary:
            self.pending_attachments.append({
                "file_name": file_name, "file_id": file_id,
                "file_size": file_size, "reason": f"not_binary_{fmt}",
            })
            return "pending"

        with open(save_path, "wb") as f:
            f.write(res.content)
        return "success"

    def _collect_attachments(self, msg, fragments):
        collected = []
        seen = set()

        def _is_valid(name):
            if not name or not isinstance(name, str):
                return False
            ext = os.path.splitext(name)[1].lower()
            return ext in VALID_ATTACHMENT_EXT

        def _add(entry):
            if not isinstance(entry, dict):
                return
            f_name = entry.get("file_name") or entry.get("name") or ""
            f_id = entry.get("file_id") or entry.get("id")
            f_size = entry.get("file_size") or entry.get("size")
            if not _is_valid(f_name):
                return
            key = (f_id, f_name)
            if key in seen:
                return
            seen.add(key)
            collected.append({
                "file_id": str(f_id) if f_id else None,
                "file_name": f_name,
                "file_size": f_size,
            })

        for frag in fragments:
            if not isinstance(frag, dict):
                continue
            if frag.get("type") != "FILE":
                continue
            for f in frag.get("files", []) or []:
                _add(f)
        for f in msg.get("files", []) or []:
            _add(f)
        inner = msg.get("message")
        if isinstance(inner, dict):
            for f in inner.get("files", []) or []:
                _add(f)
        return collected

    # ============================================================
    # BACKUP OBROLAN (MAIN FLOW)
    # ============================================================

    def backup_session(self, session: Dict[str, Any], debug: bool = False,
                       session_label: str = "") -> Optional[Dict[str, Any]]:
        s_id = session.get("id")
        title = session.get("title") or "Tanpa Judul"

        # FIX v2.4.0: title dalam quote biar jelas ini judul obrolan
        print_kv("Obrolan", f'💬 "{title}"')
        print_kv("ID", s_id[:12] + "..." if s_id else "-")

        spinner = LoadingSpinner(f'Mengambil isi obrolan...')
        spinner.start()
        detail = None
        try:
            detail = self.fetch_session_detail(s_id)
        except AuthExpiredError:
            spinner.stop("Token expired", status="error")
            raise
        finally:
            if detail:
                spinner.stop(f'Isi obrolan berhasil diambil', status="ok")
            elif not self.token_expired:
                spinner.stop(f'Gagal ambil isi obrolan', status="error")

        if not detail:
            return None

        if debug:
            print_info(f"Raw keys: {list(detail.keys())}")

        chat_messages = (
            detail.get("chat_messages")
            or detail.get("messages")
            or detail.get("history_messages")
            or []
        )

        if not isinstance(chat_messages, list):
            chat_messages = []

        total_msgs = len(chat_messages)
        print_info(f"{total_msgs} pesan terdeteksi")

        if not chat_messages:
            return None

        last_message_id = None
        for msg in reversed(chat_messages):
            if isinstance(msg, dict) and msg.get("message_id") is not None:
                last_message_id = msg.get("message_id")
                break

        prev_last_id = self._get_last_message_id(s_id) if self.incremental and not self.force_full else None

        if prev_last_id is not None and last_message_id is not None:
            if last_message_id == prev_last_id:
                print_info(f'Obrolan ini gak ada update. Skip.')
                return None
            else:
                print_info(f'Ada update baru ({prev_last_id} → {last_message_id})')

        mp = MessageProgress(session_label)
        mp.set_total(total_msgs)
        seen_file_ids = set()

        mapping: Dict[str, Any] = {}
        prev_id: Optional[str] = None

        for idx, msg in enumerate(chat_messages):
            if not isinstance(msg, dict):
                mp.increment()
                continue

            node_id = str(idx + 1)
            fragments = msg.get("fragments", []) or []
            if not isinstance(fragments, list):
                fragments = []

            for att in self._collect_attachments(msg, fragments):
                att_key = (att["file_id"], att["file_name"])
                skip_this = att_key in seen_file_ids
                seen_file_ids.add(att_key)
                self.download_attachment(
                    att["file_id"], att["file_name"],
                    att.get("file_size"), skip_if_local=skip_this,
                )

            role = self._resolve_role(msg, fragments)
            content = self._extract_content(msg, fragments)
            timestamp = self._normalize_timestamp(msg.get("inserted_at"))

            final_fragments = fragments if fragments else [{
                "type": "REQUEST" if role == "user" else "RESPONSE",
                "content": content,
            }]

            mapping[node_id] = {
                "id": node_id,
                "parent": prev_id or "root",
                "children": [],
                "message": {
                    "role": role,
                    "inserted_at": timestamp,
                    "model": msg.get("model", ""),
                    "fragments": final_fragments,
                },
            }
            if prev_id:
                mapping[prev_id]["children"].append(node_id)
            prev_id = node_id

            mp.increment()

        mp.finish()

        if self.pending_attachments:
            pending_now = len(self.pending_attachments)
            print_warn(f"📎 {pending_now} lampiran perlu taruh manual")

        if last_message_id is not None:
            self._update_last_message_id(s_id, last_message_id)
            _save_state(self.state)

        return {
            "id": s_id,
            "title": title,
            "inserted_at": self._normalize_timestamp(session.get("inserted_at")),
            "updated_at": self._normalize_timestamp(session.get("updated_at")),
            "mapping": mapping,
        }

    # ============================================================
    # PENDING MANIFEST
    # ============================================================

    def write_pending_manifest(self) -> Optional[str]:
        if not self.pending_attachments:
            return None

        manifest_path = os.path.join(self.download_dir, "PENDING.md")

        seen = set()
        unique = []
        for item in self.pending_attachments:
            key = item["file_name"]
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)

        lines = [
            "# 📎 Lampiran Pending — Perlu Taruh Manual",
            "",
            "File-file di bawah ini terdeteksi sebagai lampiran di obrolan DeepSeek,",
            "tapi **tidak bisa di-download otomatis** karena DeepSeek balikin HTML challenge.",
            "",
            "## 🔧 Cara Fix (5 menit)",
            "",
            "1. **Buka obrolan asli** di browser DeepSeek",
            "2. **Klik lampiran** → Save As / Download",
            "3. **Simpan ke folder** `./attachments/` (nama file harus persis sama)",
            "4. **Re-render** obrolan — file bakal otomatis ke-resolve via Base64 injection",
            "",
            "## 📋 Daftar File yang Perlu Di-download",
            "",
        ]
        for item in unique:
            size_str = f" (~{item['file_size']} bytes)" if item.get("file_size") else ""
            reason = item.get("reason", "unknown")
            lines.append(f"- `{item['file_name']}`{size_str} — alasan: `{reason}`")

        lines.extend([
            "",
            "---",
            "",
            "*Manifest ini auto-generated oleh GhostWriter. Re-run backup buat update.*",
        ])

        content = "\n".join(lines) + "\n"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(content)
        return manifest_path
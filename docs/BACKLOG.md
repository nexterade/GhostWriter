# GhostWriter — Backlog & Roadmap

## 🎯 Active Backlog

- [x] **FEAT-01: Interactive CLI Wizard** — Navigasi interaktif berbasis terminal di `main.py`.
- [x] **FEAT-02: DeepSeek Live Backup** — Penarikan percakapan live via user Bearer token.
- [x] **FEAT-03: Token Caching** — Simpan sesi login lokal di `.deepseek_token`.
- [x] **FEAT-04: Base64 Attachment Injection** — Render lokal gambar attachment jika file fisik tersedia di `./attachments/`.
- [x] **FEAT-05: Pretty URL Viewer** — Struktur `public/history/<id>/index.html` (SEO-friendly, gampang sharing).
- [x] **FEAT-06: Local HTTP Server** — `serve.py` dengan auto-open browser & Termux detection.
- [x] **FEAT-07: Index Sync Tool** — `sync.py` untuk regenerate index tanpa render ulang.

---

## ✅ Completed PRs

### Batch 0: Live Backup Robustness
- [x] **PR-00A: Pagination Cursor-Based**
  - Loop `next_page_id` / `next` / `cursor` sampai habis di `fetch_session_list()`.
- [x] **PR-00B: Retry Eksponensial**
  - Wrapper `_request()` dengan `MAX_RETRIES=3`, backoff `1.5^n` untuk 429/5xx.
- [x] **PR-00C: Bulk Selection Wizard**
  - Input `1`, `1,3,5`, `1-5`, `all` di `main.py`.
- [x] **PR-00D: Token Cache Hardening**
  - Auto-invalidate kalo expired + `chmod 600` di `.deepseek_token`.
- [x] **PR-00E: Debug Mode**
  - `GW_DEBUG=1` → dump sample message mentah dari API.
- [x] **PR-00F: Attachment Magic Bytes Validation**
  - Cek signature PNG/JPEG/WebP/PDF/GIF/ZIP sebelum simpan.
- [x] **PR-00G: HTML Guard**
  - Skip response dengan `Content-Type: text/html` (challenge page).
- [x] **PR-00H: Pending Manifest**
  - Auto-generate `attachments/PENDING.md`.

### Batch 0.5: JSON Parser Expansion
- [x] **PR-00I: DeepSeek Raw Format Support**
  - `JSONChatParser._parse_deepseek_raw()` handle `{chat_session, chat_messages}`.
- [x] **PR-00J: thinking_content → `<details>` Block**
- [x] **PR-00K: search_results → Citation Block**
- [x] **PR-00L: `_format_epoch()` Helper**
- [x] **PR-00M: Attachment Card "Missing" State**

### Batch 1: Format Expansion
- [x] **PR-01: Markdown Parser (`parsers/md_parser.py`)**
  - Support heading `###`/`##`/`#`, bold `**User:**`, italic `*AI*`.
  - Role alias: user, human, assistant, ai, bot, deepseek, chatgpt, claude, gemini.
- [x] **PR-02: DOCX Parser (`parsers/docx_parser.py`)**
  - Ekstraksi via `python-docx`.
- [x] **PR-03: Parser Router Integration**
  - Routing otomatis via `get_parser_for_file()` di `main.py`.

### Batch 1.5: CLI Theme & UX
- [x] **PR-05: Midnight Theme CLI**
  - `tools/theme.py` — ANSI 256 palette, auto-disable kalo non-TTY.
- [x] **PR-06: Loading Spinner + Progress Bar**
  - `tools/loading.py` — spinner braille/dots/ascii, status badge, progress bar gradient.
- [x] **PR-07: Interactive Checklist**
  - `tools/checklist.py` — j/k navigation, space toggle, fallback mode angka.
- [x] **PR-08: Human-like Delay + Jitter**
  - Configurable via `GW_DELAY_MIN`, `GW_SESSION_DELAY_MIN`, dll.
- [x] **PR-09: Incremental Backup**
  - State file `deepseek_backup_state.json` track `last_message_id` per sesi.
- [x] **PR-10: Attachment Inline Progress**
  - Counter update in-place, gak spam.

### Batch 2: Viewer & UI Enhancements
- [x] **PR-04: Multi-Chat Sidebar UI**
  - Sidebar fetch dari `public/index.json`, auto-show kalo >1 convo.
- [x] **PR-07A: LaTeX / KaTeX Rendering**
  - Auto-render dengan delimiters `$...$`, `$$...$$`, `\(...\)`, `\[...\]`.
- [x] **PR-08A: Fully Self-Contained Offline Bundle**
  - Vendor assets auto-copy ke `public/vendor/`, fallback CDN.
- [x] **PR-11: Search + Copy + Collapsible**
  - Search dengan highlight, copy message, collapsible long messages.
- [x] **PR-12: Dark/Light Theme Toggle**
  - Sync via localStorage, persist antar sesi.
- [x] **PR-13: Scroll Position Memory**
  - Per-chat, simpen di localStorage.
- [x] **PR-14: Right Rail — User Message Navigator**
  - Auto-open desktop, drawer mode mobile.
- [x] **PR-15: Print Stylesheet**
  - `@media print` bikin output rapi.

### Batch 3: Landing Page & Index
- [x] **PR-16: Dist Index Generator**
  - `tools/dist_index.py` — scan `public/history/`, tulis `index.json`.
- [x] **PR-17: Landing Page (index.html)**
  - Card list, search, sort, theme toggle.
- [x] **PR-18: Auto-Update Index**
  - `exporter.py` panggil `write_all()` tiap render.

### Batch 3.5: Struktur Migration & Bugfix (v2.2)
- [x] **PR-19: Migrasi `dist/` → `public/history/<id>/`**
  - Pretty URL: `/history/<id>/index.html`.
  - Vendor di `public/vendor/` (shared, bukan per-convo).
- [x] **PR-20: Local HTTP Server (`serve.py`)**
  - Auto-open browser, Termux detection, no-cache headers.
- [x] **PR-21: Index Sync Tool (`sync.py`)**
  - Manual regenerate index tanpa full render.
- [x] **PR-22: BUGFIX — Kurung Kurawal JS Salah Posisi**
  - **FATAL**: `viewer.html` `loadDistIndex()` — `section.appendChild(el)`
    di luar callback `addEventListener`, bikin parse error cascade yang
    matiin SELURUH `<script>`.
- [x] **PR-23: BUGFIX — `_ensure_vendor()` Cek Isi Folder**
  - Sebelumnya cuma cek eksistensi folder. Kalo folder ada tapi kosong,
    vendor gak ke-copy ulang. Sekarang cek `os.listdir(dst)`.
- [x] **PR-24: BUGFIX — Hapus Duplikat Fetch `index.json`**
  - STEP 16 di viewer.html dihapus, logika auto-show sidebar dipindah
    ke STEP 5 (fetch cuma 1x).
- [x] **PR-25: BUGFIX — `_session_delay` Import di Top-Level**
  - Sebelumnya import di dalam loop backup (anti-pattern).
- [x] **PR-26: BUGFIX — Backup Output ke `backups/`**
  - Sebelumnya nulis di root (`backup_bulk.json`), bikin root penuh.
- [x] **PR-27: BUGFIX — Hapus `convo_count` Dependency**
  - Viewer sekarang andelin `index.json` sebagai single source of truth.
- [x] **PR-28: Date Grouping di Landing Page**
  - Section: Hari Ini, Kemarin, 7 Hari Terakhir, 30 Hari Terakhir, Lebih Lama.
- [x] **PR-29: Dedup by Title di Index**
  - `_normalize_title()` strip timestamp suffix + angka kurung.
  
### Batch 3.6: Documentation Rule Update (v2.2.1)
- [x] **PR-30A: Multi-Batch File Delivery Rule**
  - CHECKPOINT.md section 3.10 baru: AI wajib kirim file multi-batch
    satu-satu dengan konfirmasi per file.
  - Alasan: cegah user skip file, salah timpa, atau gak test per file.

---

## ⏳ Pending PRs

### Batch 4: Polish & Cleanup
- [ ] **PR-30: Fix Dedup Edge Case**
  - `_normalize_title()` salah strip "Chat (1)" vs "Chat (2)".
  - Solusi: dedup by ID prefix, keep highest mtime.
- [ ] **PR-31: Skip Delay Kalo Attachment Pasti Pending**
  - Kalo attachment udah pasti `html_response_need_session`, skip delay
    1-3s biar gak buang waktu.
- [ ] **PR-32: Backup Versioning**
  - Opsi: `backup_bulk_YYYYMMDD_HHMMSS.json` (timestamp suffix).
  - Atau: folder `backups/YYYY-MM-DD/`.
- [ ] **PR-33: Prune Stale `public/history/`**
  - Hapus folder yang gak ada di source backup.
  - Atau: flag `--clean` di `sync.py`.

### Batch 5: Fitur Baru
- [ ] **PR-34: Termux API Integration**
  - Checklist pake `termux-dialog` native Android.
- [ ] **PR-35: Full-Text Search di Index**
  - Search body content, bukan cuma title.
- [ ] **PR-36: Export Individual Convo to PDF**
  - Tombol di viewer → window.print() dengan clean layout.
- [ ] **PR-37: Category/Tag untuk Convo**
  - Edit metadata manual via UI, filter di index.
- [ ] **PR-38: Diff View**
  - Bandingin 2 versi convo (kalo ada update).

---

## 📊 Milestone Tracker
**Phase 1**: Local JSON Converter [✓✓✓✓✓] DONE
**Phase 2**: Live Backup + Parser Polish [✓✓✓✓✓] DONE
**Phase 3**: Format Expansion + UI [✓✓✓✓✓] DONE
**Phase 4**: Polish & Stabilization [✓✓✓✓ ] IN PROGRESS
**Phase 5**: Advanced Features [ ] PENDING

---

## 🎯 Prioritas Berikutnya

1. **Batch 4** — Polish & Cleanup (PR-30 s/d PR-33)
2. **Batch 5** — Fitur Baru (PR-34 s/d PR-38)

---

**Last Updated:** 2026-09-19
**Maintainer:** GhostWriter Dev Team (Multi-AI Collaboration)
**Current Version:** v2.2-GW
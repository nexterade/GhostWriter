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
- [x] **PR-00B: Retry Eksponensial**
- [x] **PR-00C: Bulk Selection Wizard**
- [x] **PR-00D: Token Cache Hardening**
- [x] **PR-00E: Debug Mode**
- [x] **PR-00F: Attachment Magic Bytes Validation**
- [x] **PR-00G: HTML Guard**
- [x] **PR-00H: Pending Manifest**

### Batch 0.5: JSON Parser Expansion
- [x] **PR-00I: DeepSeek Raw Format Support**
- [x] **PR-00J: thinking_content → `<details>` Block**
- [x] **PR-00K: search_results → Citation Block**
- [x] **PR-00L: `_format_epoch()` Helper**
- [x] **PR-00M: Attachment Card "Missing" State**

### Batch 1: Format Expansion
- [x] **PR-01: Markdown Parser**
- [x] **PR-02: DOCX Parser**
- [x] **PR-03: Parser Router Integration**

### Batch 1.5: CLI Theme & UX
- [x] **PR-05: Midnight Theme CLI**
- [x] **PR-06: Loading Spinner + Progress Bar**
- [x] **PR-07: Interactive Checklist**
- [x] **PR-08: Human-like Delay + Jitter**
- [x] **PR-09: Incremental Backup**
- [x] **PR-10: Attachment Inline Progress**

### Batch 2: Viewer & UI Enhancements
- [x] **PR-04: Multi-Chat Sidebar UI**
- [x] **PR-07A: LaTeX / KaTeX Rendering**
- [x] **PR-08A: Fully Self-Contained Offline Bundle**
- [x] **PR-11: Search + Copy + Collapsible**
- [x] **PR-12: Dark/Light Theme Toggle**
- [x] **PR-13: Scroll Position Memory**
- [x] **PR-14: Right Rail — User Message Navigator**
- [x] **PR-15: Print Stylesheet**

### Batch 3: Landing Page & Index
- [x] **PR-16: Dist Index Generator**
- [x] **PR-17: Landing Page (index.html)**
- [x] **PR-18: Auto-Update Index**

### Batch 3.5: Struktur Migration & Bugfix (v2.2)
- [x] **PR-19: Migrasi `dist/` → `public/history/<id>/`**
- [x] **PR-20: Local HTTP Server (`serve.py`)**
- [x] **PR-21: Index Sync Tool (`sync.py`)**
- [x] **PR-22: BUGFIX — Kurung Kurawal JS Salah Posisi**
- [x] **PR-23: BUGFIX — `_ensure_vendor()` Cek Isi Folder**
- [x] **PR-24: BUGFIX — Hapus Duplikat Fetch `index.json`**
- [x] **PR-25: BUGFIX — `_session_delay` Import di Top-Level**
- [x] **PR-26: BUGFIX — Backup Output ke `backups/`**
- [x] **PR-27: BUGFIX — Hapus `convo_count` Dependency**
- [x] **PR-28: Date Grouping di Landing Page**
- [x] **PR-29: Dedup by Title di Index**

### Batch 3.6: Documentation Rule Update (v2.2.1)
- [x] **PR-30A: Multi-Batch File Delivery Rule**

### Batch 3.7: Circuit Breaker (v2.2.2)
- [x] **PR-31: Skip Delay Kalo Attachment Pasti Pending**

### Batch 3.8: Action A — Data Safety (v2.2.3)
- [x] **PR-39: Auto-Backup Sebelum Overwrite**
  - `_backup_existing_file()` + `_prune_old_backups()` di `exporter.py`.
  - Simpen maksimal 3 versi backup per convo (`index-YYYYMMDD-HHMMSS.html.bak`).
- [x] **PR-40: Integrity Check Sebelum Render**
  - `_validate_chat_data()` di `main.py`.
  - Cek: title, messages list, >0 pesan, role valid, content valid.
  - Abort kalo >50% pesan kosong (indikasi parse gagal).
- [x] **PR-40A: Graceful Token Expired Handling**
  - `AuthExpiredError` exception di `deepseek_backup.py`.
  - `_request()` detect auth error (HTTP 401/403 atau body code 401/403).
  - `fetch_session_list()`, `fetch_session_detail()` guard clause.
  - `main.py` wrap wizard handlers di `_safe_run()`.
  - Auto-invalidate token cache, balik ke menu (gak crash).

### Batch 3.9: Action B — UX Quick Wins (v2.3.0)
- [x] **PR-42: Keyboard Shortcut Overlay / Help Panel**
  - Tombol `?` di header + shortcut `?` buat buka modal.
  - Modal berisi 4 section: Navigasi, Search, Scroll, Pesan.
  - Esc buat close, klik backdrop juga.
- [x] **PR-43: Export Single Message**
  - Dropdown menu per message (⋯) dengan 3 opsi:
    - 📋 Copy as Markdown
    - 💾 Save as .md (download file)
    - 🔗 Copy Permalink (link ke `#msg-N`)
  - Toast notification feedback.

### Batch 3.10: UI Refactor Mobile-Friendly (v2.3.0)
- [x] **PR-42A: Mobile Viewport Fix (dvh + safe-area)**
  - Ganti `100vh` → `100dvh` di body/main-area/sidebar/rail.
  - Tambah `env(safe-area-inset-bottom)` di chat-container, floating-nav, stats-bar.
  - Fix address bar overlap di mobile.
- [x] **PR-42B: Floating Nav Sembunyi Pas Search Aktif**
  - `body.searching` class trigger hide floating nav.
  - Esc priority: modal > search > sidebar/rail.
  - Search box accent tetep muncul walau gak fokus.
- [x] **PR-42C: Keyboard Mobile Viewport Fix**
  - VisualViewport API detect keyboard + set `--vv-height` variable.
  - `body.keyboard-active` class buat CSS hook.
  - Sticky header biar gak ke-scroll keluar.
  - `scroll-padding` di chat-container biar auto-scroll aman.
- [x] **PR-42D: UI Refactor — Search Bar Bottom + Stats Header**
  - Search box pindah dari header ke bottom (mirip DeepSeek/ChatGPT mobile).
  - Stats footer pindah ke bawah header, sticky, gak hidden di mobile.
  - Header slim: title + `?` + `🌙` + `⋮` (dropdown).
  - Dropdown `⋮` berisi Print + Right Rail toggle.
  - Search nav buttons (Prev/Next) buat mobile (gak ada Enter key).
  - Clear button `✕` + counter badge `[N]` di search bar.
  - Floating nav (▲▼) pindah ke atas search bar.
  - Fix bug fundamental keyboard mobile (search gak ketutup lagi).

---

## ⏳ Pending PRs — Kategorisasi Action Fixed

---

### 🎯 ACTION D — Polish Backlog Lama
**Files**: `tools/dist_index.py`, `main.py`, `sync.py`
**Effort**: ~2-3 jam
**Priority**: MEDIUM

- [ ] **PR-30: Fix Dedup Edge Case**
  - `_normalize_title()` salah strip "Chat (1)" vs "Chat (2)".
  - Solusi: dedup by ID prefix, keep highest mtime.
- [ ] **PR-32: Backup Versioning**
  - Opsi: `backup_bulk_YYYYMMDD_HHMMSS.json` (timestamp suffix).
- [ ] **PR-33: Prune Stale `public/history/`**
  - Flag `--clean` di `sync.py` dengan dry-run mode & konfirmasi.

### 🎯 ACTION C — Index Safety & Scale
**Files**: `tools/dist_index.py`, `sync.py`
**Effort**: ~4-5 jam
**Priority**: HIGH

- [ ] **PR-41: Checksum / Manifest di Index.json**
- [ ] **PR-46: Pagination / Infinite Scroll di Landing Page**
- [ ] **PR-48: Auto-Detect Broken Links di Index**

### 🎯 ACTION E — Perf & Onboarding
**Files**: `templates/viewer.html`, `tools/dist_index.py`, `parsers/json_parser.py`
**Effort**: ~3 jam
**Priority**: MEDIUM

- [ ] **PR-44: Onboarding Tour Pertama Kali**
- [ ] **PR-45: Lazy Load Attachment Images**

### 🎯 ACTION F — PDF Export
**Files**: `templates/viewer.html`, `main.py`
**Effort**: ~2-4 jam
**Priority**: MEDIUM
**Status**: DEFERRED

- [ ] **PR-36: Export Individual Convo to PDF**
  - Note: Dengan UI baru, tombol PDF udah ada di dropdown `⋮` (via `window.print()`).
  - Yang kurang: print CSS tweak khusus + cleanup.

### 🎯 ACTION G — CLI Convenience
**Files**: `main.py`
**Effort**: ~30 menit
**Priority**: LOW

- [ ] **PR-47: CLI Flag `--stats`**

### 🎯 ACTION H — Termux Integration
**Files**: `tools/checklist.py`, `main.py`
**Effort**: ~1-2 jam
**Priority**: MEDIUM

- [ ] **PR-34: Termux API Integration**

### 🎯 ACTION I — Advanced Features
**Files**: `templates/viewer.html`, `tools/dist_index.py`
**Effort**: ~10-14 jam
**Priority**: LOW
**Status**: BACKLOG

- [ ] **PR-37: Category/Tag untuk Convo**
- [ ] **PR-38: Diff View**

---

## 📊 Action Tracker

| Action | Nama | Files | Effort | Priority | Status |
|---|---|---|---|---|---|
| A | Data Safety | exporter.py, main.py, deepseek_backup.py | 1.5j | HIGH | ✅ Done |
| B | UX Quick Wins | viewer.html | 2.5j | HIGH | ✅ Done |
| UI | Mobile Refactor | viewer.html | 3j | HIGH | ✅ Done |
| C | Index Safety & Scale | dist_index.py, sync.py | 4-5j | HIGH | ⏳ Pending |
| D | Polish Backlog Lama | dist_index.py, main.py, sync.py | 2-3j | MEDIUM | ⏳ **Next** |
| E | Perf & Onboarding | viewer.html, dist_index.py, json_parser.py | 3j | MEDIUM | ⏳ Pending |
| F | PDF Export | viewer.html, main.py | 2-4j | MEDIUM | 🕐 Deferred |
| G | CLI Convenience | main.py | 30m | LOW | ⏳ Pending |
| H | Termux Integration | checklist.py, main.py | 1-2j | MEDIUM | ⏳ Pending |
| I | Advanced Features | viewer.html, dist_index.py | 10-14j | LOW | 📋 Backlog |

---

## 📊 Milestone Tracker

**Phase 1**: Local JSON Converter [✓✓✓✓✓] DONE
**Phase 2**: Live Backup + Parser Polish [✓✓✓✓✓] DONE
**Phase 3**: Format Expansion + UI [✓✓✓✓✓] DONE
**Phase 4**: Polish & Stabilization [✓✓✓  ] IN PROGRESS
**Phase 5**: Advanced Features [      ] PENDING

---

## 🎯 Prioritas Berikutnya

1. **Action D** — Polish Backlog Lama (PR-30, PR-32, PR-33)
2. **Action C** — Index Safety & Scale (PR-41, PR-46, PR-48)
3. **Action E** — Perf & Onboarding

---

**Last Updated:** 2026-09-19
**Maintainer:** GhostWriter Dev Team (Multi-AI Collaboration)
**Current Version:** v2.3.0-GW
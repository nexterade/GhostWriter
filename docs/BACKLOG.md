# GhostWriter — Backlog & Roadmap

## 🎯 Active Backlog

- [x] **FEAT-01: Interactive CLI Wizard** — Navigasi interaktif berbasis terminal di `main.py`.
- [x] **FEAT-02: DeepSeek Live Backup** — Penarikan percakapan live via user Bearer token.
- [x] **FEAT-03: Token Caching** — Simpan sesi login lokal di `.deepseek_token`.
- [x] **FEAT-04: Base64 Attachment Injection** — Render lokal gambar attachment jika file fisik tersedia di `./attachments/`.
- [x] **FEAT-05: Pretty URL Viewer** — Struktur `public/history/<id>/index.html` (SEO-friendly, gampang sharing).
- [x] **FEAT-06: Local HTTP Server** — `serve.py` dengan auto-open browser & Termux detection.
- [x] **FEAT-07: Index Sync Tool** — `sync.py` untuk regenerate index tanpa render ulang.
- [x] **FEAT-08: Multi-Scroll-Effect** — 5 variasi scroll effect configurable.
- [x] **FEAT-09: Multi-Loading-Effect** — Loading overlay configurable.
- [x] **FEAT-10: Bidirectional Swipe Gesture** — Swipe buka/tutup drawer.
- [x] **FEAT-11: Auto-Close Drawer** — Buka 1 drawer → auto-close drawer lain.

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
- [x] **PR-40: Integrity Check Sebelum Render**
- [x] **PR-40A: Graceful Token Expired Handling**

### Batch 3.9: Action B — UX Quick Wins (v2.3.0)
- [x] **PR-42: Keyboard Shortcut Overlay / Help Panel**
- [x] **PR-43: Export Single Message**

### Batch 3.10: UI Refactor Mobile-Friendly (v2.3.0)
- [x] **PR-42A: Mobile Viewport Fix (dvh + safe-area)**
- [x] **PR-42B: Floating Nav Sembunyi Pas Search Aktif**
- [x] **PR-42C: Keyboard Mobile Viewport Fix**
- [x] **PR-42D: UI Refactor — Search Bar Bottom + Stats Header**

### Batch 3.11: User-Friendly CLI Redesign (v2.4.0)
- [x] **PR-42E: Menu Redesign — Soft & Friendly + Nomor [N]**
- [x] **PR-42F: Tutorial Upgrade**
- [x] **PR-42G: Konsistensi Istilah**

### Batch 4: Action D — Polish Backlog Lama (v2.5.0)
- [x] **PR-30: Fix Dedup Edge Case**
- [x] **PR-32: Backup Versioning**
- [x] **PR-33: Prune Stale public/history/**

### Batch 5: Mobile Polish v2.6.0 (2026-09-19)
- [x] **PR-42H: Disable Zoom (Meta + CSS)**
- [x] **PR-42I: Zoom Layout Fix (iOS Safari Fallback)**
- [x] **PR-42J: Scroll Fade + Dim + Scale Animation**
- [x] **PR-36: PDF Export CSS Upgrade**

### Batch 6: Swipe & Reorder v2.6.1 (2026-09-19)
- [x] **PR-42K: Swipe Gesture Fix (Edge Priority)**
- [x] **PR-42L: Header Buttons Reorder**
- [x] **PR-42M: Message Menu Smart Positioning**

### Batch 7: Blank Fix v2.6.3 (2026-09-19)
- [x] **PR-42N: Fix `chatContainer` ReferenceError**

### Batch 8: Loading Overlay v2.6.4 (2026-09-19)
- [x] **PR-42O: Full-Screen Loading Overlay**

### Batch 9: Sidebar Cleanup v2.6.6 (2026-09-19)
- [x] **PR-42P: Simplify Sidebar Header**
- [x] **PR-42Q: Tombol Close Pindah ke Footer**
- [x] **PR-42R: Bidirectional Swipe + Auto-Close**
- [x] **PR-42S: Help Modal Update**

---

## ⏳ Pending PRs — Kategorisasi Action Fixed

---

### 🎯 ACTION C — Index Safety & Scale
**Files**: `tools/dist_index.py`, `sync.py`
**Effort**: ~4-5 jam
**Priority**: HIGH

- [ ] **PR-41: Checksum / Manifest di Index.json**
  - Taro checksum (MD5/SHA256) tiap HTML di `index.json`.
  - Landing page verify (opsional, async). Kalo mismatch, badge "⚠️ stale".
  - File: `tools/dist_index.py`.

- [ ] **PR-46: Pagination / Infinite Scroll di Landing Page**
  - Pagination 25/50/100 per page atau infinite scroll (load 20 pertama).
  - File: `tools/dist_index.py` + landing page JS.

- [ ] **PR-48: Auto-Detect Broken Links di Index**
  - `sync.py` flag `--verify` buat cek semua link di `index.json` apakah
    file-nya ada. Output list broken, opsi auto-fix (hapus dari index).
  - File: `sync.py` + `tools/dist_index.py`.

---

### 🎯 ACTION E — Perf & Onboarding
**Files**: `templates/viewer.html`, `tools/dist_index.py`, `parsers/json_parser.py`
**Effort**: ~3 jam
**Priority**: MEDIUM

- [ ] **PR-44: Onboarding Tour Pertama Kali**
  - Kalo `public/history/` kosong (first time), landing page nampilin
    step-by-step guide (render, serve, buka browser) + CTA button.
  - File: `tools/dist_index.py` (empty state).

- [ ] **PR-45: Lazy Load Attachment Images**
  - Ganti Base64 inline jadi lazy-loaded `<img data-src>`.
  - Load via `IntersectionObserver` pas masuk viewport.
  - File: `parsers/json_parser.py` + `templates/viewer.html`.

---

### 🎯 ACTION F — PDF Export Lanjutan
**Files**: `templates/viewer.html`, `main.py`
**Effort**: ~2-4 jam
**Priority**: MEDIUM
**Status**: DEFERRED (sebagian udah done via PR-36)

- [ ] **PR-36B: Auto-Set PDF Title + Print Preview Tweak**
  - Auto-set PDF title dari convo title.
  - Print preview polish.

---

### 🎯 ACTION G — CLI Convenience
**Files**: `main.py`
**Effort**: ~30 menit
**Priority**: LOW

- [ ] **PR-47: CLI Flag `--stats`**
  - `python3 main.py --stats` print ringkasan project.
  - Total convo, total message, total size, latest render, top 3 convo.
  - File: `main.py`.

---

### 🎯 ACTION H — Termux Integration
**Files**: `tools/checklist.py`, `main.py`
**Effort**: ~1-2 jam
**Priority**: MEDIUM

- [ ] **PR-34: Termux API Integration**
  - Checklist pake `termux-dialog` native Android (radio, text, confirm).
  - File: `tools/checklist.py` + `main.py`.

---

### 🎯 ACTION I — Advanced Features
**Files**: `templates/viewer.html`, `tools/dist_index.py`
**Effort**: ~10-14 jam
**Priority**: LOW
**Status**: BACKLOG (butuh design dulu)

- [ ] **PR-37: Category/Tag untuk Convo**
- [ ] **PR-38: Diff View**

---

### 🎯 ACTION J — Import Platform Lain (Universal) ✨ NEW
**Files**: `parsers/*.py`, `main.py`, `docs/*.md`
**Effort**: ~14 jam (multi-sesi)
**Priority**: MEDIUM-HIGH (Phase 5)
**Status**: PLANNED (belum eksekusi)

**Tujuan**: Support import dari platform AI lain (ChatGPT, Claude, Gemini,
Mistral, Poe) dengan **auto-detect** + **universal parser framework**.

#### 📐 Arsitektur (3 Layer)

  ┌─────────────────────────────────────────┐
  │ LAYER 1: DETECTOR                       │
  │ - Cek struktur file (keys, fields)      │
  │ - Cek filename pattern                  │
  │ - Cek signature (magic bytes)           │
  ├─────────────────────────────────────────┤
  │ LAYER 2: PARSER REGISTRY                │
  │ - ChatGPT, Claude, Gemini, DeepSeek...  │
  │ - Universal fallback (generic)          │
  ├─────────────────────────────────────────┤
  │ LAYER 3: NORMALIZER                     │
  │ - Semua parser return skema seragam     │
  │ - {title, created_at, messages: [...]}  │
  └─────────────────────────────────────────┘

#### 📋 Sub-PR Breakdown

- [ ] **PR-50: Universal Detector Framework**
  - Bikin `parsers/universal_detector.py`.
  - Auto-detect platform dari struktur file.
  - Deteksi via:
    * Filename pattern (misal `conversations.json` → ChatGPT)
    * Key signature (misal `mapping` + `author` → ChatGPT)
    * Key signature (misal `chat_messages` + role `human` → Claude)
  - Return: platform name + parser class.
  - **Effort**: ~2 jam.

- [ ] **PR-51: ChatGPT Parser**
  - Bikin `parsers/chatgpt_parser.py`.
  - Handle format `conversations.json` (Settings → Data Controls → Export).
  - Handle mapping tree dengan `parent_id`/`children`.
  - Handle content types: `text`, `code`, `image`, `multimodal_text`.
  - **Effort**: ~1.5 jam.
  - **Sample**: Cari di GitHub gist (banyak yang share).

- [ ] **PR-52: Claude Parser**
  - Bikin `parsers/claude_parser.py`.
  - Handle format export Claude (content blocks array).
  - Role: `human` / `assistant` / `system`.
  - Handle content blocks: `text`, `image`, `tool_use`, `tool_result`.
  - **Effort**: ~1.5 jam.
  - **Sample**: Schema docs + dummy.

- [ ] **PR-53: Gemini Parser**
  - Bikin `parsers/gemini_parser.py`.
  - Handle Google Takeout format (HTML fragments, paling complex).
  - Parse HTML: `<div>` per message, class-based detection.
  - **Effort**: ~3 jam.
  - **Sample**: Takeout export (bisa minta user kirim).

- [ ] **PR-54: Mistral Le Chat Parser**
  - Bikin `parsers/mistral_parser.py`.
  - Format mirip Claude (content blocks).
  - **Effort**: ~1 jam.

- [ ] **PR-55: Poe Parser**
  - Bikin `parsers/poe_parser.py`.
  - Format JSON dari Poe export.
  - **Effort**: ~1 jam.

- [ ] **PR-56: Generic Fallback Parser**
  - Bikin `parsers/generic_fallback.py`.
  - Catch-all parser buat format yang gak dikenal.
  - Heuristic: cari field `messages` / `chat` / `conversation`.
  - Coba ekstrak: title, timestamp, role, content.
  - Kalo gagal, kasih **error message jelas** + hint format yang didukung.
  - **Effort**: ~1 jam.

- [ ] **PR-57: Integrate Detector ke main.py**
  - Update `main.py` — pake `universal_detector.detect_and_parse()`.
  - Ganti `get_parser_for_file()` yang sekarang cuma cek extension.
  - **Effort**: ~1 jam.

- [ ] **PR-58: Per-Platform Testing**
  - Bikin test case per platform.
  - Sample file: bisa dari publik atau dummy.
  - **Effort**: ~2 jam.

- [ ] **PR-59: Docs — Tutorial Import Per Platform**
  - Update `docs/STATE.md` — tambah section "Supported Platforms".
  - Bikin `docs/IMPORT_GUIDE.md` (BARU) — step-by-step per platform.
  - **Effort**: ~1 jam.

#### 🎯 Platform Coverage

| # | Platform | Format | Effort | Priority |
|---|---|---|---|---|
| 1 | **ChatGPT** | `conversations.json` (Settings export) | 1.5j | HIGH |
| 2 | **Claude** | JSON (content blocks) | 1.5j | HIGH |
| 3 | **Gemini** | Google Takeout (HTML fragments) | 3j | MEDIUM |
| 4 | **Mistral** | JSON | 1j | MEDIUM |
| 5 | **Poe** | JSON | 1j | LOW |
| 6 | **Generic** | Fallback apapun | 1j | HIGH |

#### ⏱️ Timeline (Multi-Sesi)

- **Sesi 1** (~4 jam): Universal detector + ChatGPT + Generic fallback
- **Sesi 2** (~4 jam): Claude + Mistral + integrate ke main.py
- **Sesi 3** (~4 jam): Gemini + Poe
- **Sesi 4** (~2 jam): Docs + testing + release v2.7.0-GW

**Total**: ~14 jam, 4 sesi.

#### ⚠️ Risiko & Catatan

  - **Schema platform bisa berubah** — ChatGPT ganti format 3x dalam 2 tahun.
    Parser harus **defensive** — cek field sebelum akses.
  - **Sample file terbatas** — beberapa platform (Poe, Claude) susah dapet sample.
    Solusi: bikin **dummy** berdasarkan schema docs.
  - **Gemini paling complex** — Google Takeout format HTML, bukan JSON.
    Butuh **HTML parser** (BeautifulSoup atau regex).
  - **Performance** — auto-detect bisa **lambat** kalo file gede (100+ MB).
    Solusi: **peek first 1KB** buat deteksi, bukan load full file.
  - **Test coverage** — wajib test per platform **sebelum release**.
    Bikin folder `tests/samples/` (gitignored) buat dummy.

#### 📚 Referensi

  - **ChatGPT export schema**: github.com/gpt4free/gpt4free (contoh)
  - **Claude export**: docs.anthropic.com (export format)
  - **Gemini Takeout**: support.google.com/takeout
  - **ActivityPub / Data Portability**: activitypub.rocks

---

## 📊 Action Tracker

| Action | Nama | Files | Effort | Priority | Status |
|---|---|---|---|---|---|
| A | Data Safety | exporter.py, main.py, deepseek_backup.py | 1.5j | HIGH | ✅ Done |
| B | UX Quick Wins | viewer.html | 2.5j | HIGH | ✅ Done |
| UI | Mobile Refactor | viewer.html | 3j | HIGH | ✅ Done |
| CLI | User-Friendly Redesign | main.py, deepseek_backup.py | 2j | HIGH | ✅ Done |
| D | Polish Backlog Lama | dist_index.py, main.py, sync.py | 2-3j | MEDIUM | ✅ Done |
| MOBILE | Mobile Polish (v2.6.0) | viewer.html | 3j | HIGH | ✅ Done |
| SWIPE | Swipe & Reorder (v2.6.1) | viewer.html | 1j | HIGH | ✅ Done |
| BLANK | Blank Fix (v2.6.3) | viewer.html | 0.5j | HIGH | ✅ Done |
| LOAD | Loading Overlay (v2.6.4) | viewer.html | 1.5j | MEDIUM | ✅ Done |
| CLEAN | Sidebar Cleanup (v2.6.6) | viewer.html | 1j | MEDIUM | ✅ Done |
| C | Index Safety & Scale | dist_index.py, sync.py | 4-5j | HIGH | ⏳ Next |
| E | Perf & Onboarding | viewer.html, dist_index.py, json_parser.py | 3j | MEDIUM | ⏳ Pending |
| F | PDF Export Lanjutan | viewer.html, main.py | 2-4j | MEDIUM | 🕐 Deferred |
| G | CLI Convenience | main.py | 30m | LOW | ⏳ Pending |
| H | Termux Integration | checklist.py, main.py | 1-2j | MEDIUM | ⏳ Pending |
| I | Advanced Features | viewer.html, dist_index.py | 10-14j | LOW | 📋 Backlog |
| **J** | **Import Platform Lain** | **parsers/*.py, main.py** | **14j** | **MEDIUM-HIGH** | **📋 Planned** |

---

## 📊 Milestone Tracker

**Phase 1**: Local JSON Converter [✓✓✓✓✓] DONE
**Phase 2**: Live Backup + Parser Polish [✓✓✓✓✓] DONE
**Phase 3**: Format Expansion + UI [✓✓✓✓✓] DONE
**Phase 4**: Polish & Stabilization [✓✓✓✓ ] IN PROGRESS
**Phase 5**: Import Platform Lain & Advanced [      ] PLANNED

---

## 🎯 Prioritas Berikutnya

1. **Action C** — Index Safety & Scale (PR-41, PR-46, PR-48) — 4-5 jam
2. **Action E** — Perf & Onboarding — 3 jam
3. **Action J** — Import Platform Lain (Phase 5) — 14 jam, multi-sesi

---

**Last Updated:** 2026-09-19
**Maintainer:** GhostWriter Dev Team (Multi-AI Collaboration)
**Current Version:** v2.6.6-GW
**Next Version:** v2.7.0-GW (Phase 5 — Import Platform Lain)
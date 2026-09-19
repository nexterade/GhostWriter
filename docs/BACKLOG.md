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
  - CHECKPOINT.md section 3.11 baru.

### Batch 3.7: Circuit Breaker (v2.2.2)
- [x] **PR-31: Skip Delay Kalo Attachment Pasti Pending**
  - Circuit breaker di `deepseek_backup.py`.

---

## ⏳ Pending PRs — Kategorisasi Action Fixed

Semua PR pending dikelompokkan jadi **1 Action = 1 Batch File = 1 Sesi Kerja**.
Urutan action berdasarkan dependency & priority.

---

### 🎯 ACTION A — Data Safety Batch
**Files**: `exporter.py`, `main.py`
**Effort**: ~1.5 jam
**Priority**: HIGH (data loss prevention)

- [ ] **PR-39: Auto-Backup Sebelum Overwrite**
  - Sebelum timpa `public/history/<id>/index.html`, rename file lama ke
    `.bak` atau `index-YYYYMMDD-HHMMSS.html`.
  - Simpen 1-3 versi terakhir. Kalo udah lewat batas, hapus yang paling lama.
  - File: `exporter.py` (fungsi `export`).

- [ ] **PR-40: Integrity Check Sebelum Render**
  - Sebelum render, validasi source JSON:
    * JSON valid parse?
    * Jumlah message > 0?
    * Title gak kosong?
    * Attachment (kalo ada) ada file fisiknya?
  - Kalo gagal, abort dengan error jelas — jangan render parsial.
  - File: `main.py` (fungsi `_do_render`).

---

### 🎯 ACTION B — UX Quick Wins Batch
**Files**: `templates/viewer.html`
**Effort**: ~2.5 jam
**Priority**: HIGH (discoverability)

- [ ] **PR-42: Keyboard Shortcut Overlay / Help Panel**
  - Tombol `?` di header (atau shortcut `?`) yang munculin modal overlay
    daftar semua keyboard shortcut.
  - Bisa di-dismiss pake `Esc` atau klik backdrop.
  - File: `templates/viewer.html`.

- [ ] **PR-43: Export Single Message (Copy to Clipboard / Save .md)**
  - Dropdown menu di setiap message:
    * 📋 Copy as Markdown
    * 💾 Save as .md (download 1 message)
    * 🔗 Copy permalink (link ke message spesifik)
  - File: `templates/viewer.html`.

---

### 🎯 ACTION C — Index Safety & Scale Batch
**Files**: `tools/dist_index.py`, landing page template
**Effort**: ~4-5 jam
**Priority**: HIGH (scale + integrity)

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

### 🎯 ACTION D — Polish Backlog Lama Batch
**Files**: `tools/dist_index.py`, `main.py`, `sync.py`
**Effort**: ~2-3 jam
**Priority**: MEDIUM (polish)

- [ ] **PR-30: Fix Dedup Edge Case**
  - `_normalize_title()` salah strip "Chat (1)" vs "Chat (2)".
  - Solusi: dedup by ID prefix, keep highest mtime. Atau ubah pattern
    `\(\d+\)` cuma di-strip kalo ada convo lain dengan title sama persis.
  - File: `tools/dist_index.py`.

- [ ] **PR-32: Backup Versioning**
  - Opsi: `backup_bulk_YYYYMMDD_HHMMSS.json` (timestamp suffix).
  - Atau: folder `backups/YYYY-MM-DD/`.
  - File: `main.py`.

- [ ] **PR-33: Prune Stale `public/history/`**
  - Hapus folder yang gak ada di source backup.
  - Flag `--clean` di `sync.py` dengan dry-run mode & konfirmasi.
  - File: `sync.py` + `tools/dist_index.py`.

---

### 🎯 ACTION E — Performance & Onboarding Batch
**Files**: `templates/viewer.html`, `tools/dist_index.py`, `parsers/json_parser.py`
**Effort**: ~3 jam
**Priority**: MEDIUM (perf + UX)

- [ ] **PR-44: Onboarding Tour Pertama Kali**
  - Kalo `public/history/` kosong (first time), landing page nampilin
    step-by-step guide (render, serve, buka browser) + CTA button.
  - File: `tools/dist_index.py` (empty state).

- [ ] **PR-45: Lazy Load Attachment Images**
  - Ganti Base64 inline jadi lazy-loaded `<img data-src>`.
  - Load via `IntersectionObserver` pas masuk viewport.
  - File: `parsers/json_parser.py` + `templates/viewer.html`.

---

### 🎯 ACTION F — PDF Export Batch
**Files**: `templates/viewer.html`, `main.py`
**Effort**: ~2-4 jam
**Priority**: MEDIUM (sharing)
**Status**: DEFERRED (ditunda 2026-09-19)

- [ ] **PR-36: Export Individual Convo to PDF**
  - Tombol `📥 Export PDF` di header yang call `window.print()`.
  - Print CSS tweak: page break per message-row, hide sidebar/rail/tombol,
    repeat header, font serif, syntax highlighting grayscale.
  - File: `templates/viewer.html` + `main.py` (opsional CLI flag).

---

### 🎯 ACTION G — CLI Convenience Batch
**Files**: `main.py`, `sync.py`
**Effort**: ~30 menit
**Priority**: LOW (convenience)

- [ ] **PR-47: CLI Flag `--stats`**
  - `python3 main.py --stats` print ringkasan project:
    total convo, total message, total size, latest render, top 3 convo.
  - File: `main.py`.

---

### 🎯 ACTION H — Termux Integration Batch
**Files**: `tools/checklist.py`, `main.py`
**Effort**: ~1-2 jam
**Priority**: MEDIUM (kalo lu main di Termux)

- [ ] **PR-34: Termux API Integration**
  - Checklist pake `termux-dialog` native Android (radio, text, confirm).
  - File: `tools/checklist.py` + `main.py`.

---

### 🎯 ACTION I — Advanced Features Batch
**Files**: `templates/viewer.html`, `tools/dist_index.py`, storage
**Effort**: ~10-14 jam
**Priority**: LOW (niche)
**Status**: BACKLOG (butuh design dulu)

- [ ] **PR-37: Category/Tag untuk Convo**
  - Edit metadata manual via UI, filter di index.
  - Butuh persistensi (di mana simpen tag?).
  - File: `templates/viewer.html` + `tools/dist_index.py`.

- [ ] **PR-38: Diff View**
  - Bandingin 2 versi convo (kalo ada update).
  - Butuh library diff + UI side-by-side.
  - File: `templates/viewer.html`.

---

## 📊 Action Tracker

| Action | Nama | Files | Effort | Priority | Status |
|---|---|---|---|---|---|
| A | Data Safety | exporter.py, main.py | 1.5j | HIGH | ⏳ Pending |
| B | UX Quick Wins | viewer.html | 2.5j | HIGH | ⏳ Pending |
| C | Index Safety & Scale | dist_index.py, sync.py | 4-5j | HIGH | ⏳ Pending |
| D | Polish Backlog Lama | dist_index.py, main.py, sync.py | 2-3j | MEDIUM | ⏳ Pending |
| E | Perf & Onboarding | viewer.html, dist_index.py, json_parser.py | 3j | MEDIUM | ⏳ Pending |
| F | PDF Export | viewer.html, main.py | 2-4j | MEDIUM | 🕐 Deferred |
| G | CLI Convenience | main.py | 30m | LOW | ⏳ Pending |
| H | Termux Integration | checklist.py, main.py | 1-2j | MEDIUM | ⏳ Pending |
| I | Advanced Features | viewer.html, dist_index.py | 10-14j | LOW | 📋 Backlog |

**Total kalau gas semua**: ~28-36 jam
**Total kalau gas A-D doang (High + Medium)**: ~10-13 jam

---

## 📊 Milestone Tracker

**Phase 1**: Local JSON Converter [✓✓✓✓✓] DONE
**Phase 2**: Live Backup + Parser Polish [✓✓✓✓✓] DONE
**Phase 3**: Format Expansion + UI [✓✓✓✓✓] DONE
**Phase 4**: Polish & Stabilization [✓✓✓✓ ] IN PROGRESS (PR-31 done, sisa lain digabung jadi Action A-D)
**Phase 5**: Advanced Features [ ] PENDING (Action E-I)

---

## 🎯 Prioritas Berikutnya — Rekomendasi Urutan

Kalo lu mau gas **sprint mulai besok**, urutan yang gue saranin:

1. **Action A (Data Safety)** — 1.5 jam
   - Kenapa: **Data loss prevention**, gak bisa ditunda.
   - Deliverable: `exporter.py` & `main.py` aman.

2. **Action B (UX Quick Wins)** — 2.5 jam
   - Kenapa: **Discoverability**, high impact, low effort.
   - Deliverable: Overlay shortcut + export per message.

3. **Action D (Polish Backlog Lama)** — 2-3 jam
   - Kenapa: **Beresin hutang teknis** dulu sebelum scale.
   - Deliverable: Dedup fix, versioning, prune.

4. **Action C (Index Safety & Scale)** — 4-5 jam
   - Kenapa: **Buat scale ke 500+ convo**.
   - Deliverable: Pagination, checksum, verify tool.

5. **Action E (Perf & Onboarding)** — 3 jam
   - Kenapa: **Polish akhir** Phase 4.
   - Deliverable: Lazy load + onboarding.

6. **Action F (PDF Export)** — 2-4 jam (kalo udah mood)
7. **Action G (CLI Stats)** — 30 menit (isi-isian)
8. **Action H (Termux)** — 1-2 jam (kalo main Termux)
9. **Action I (Advanced)** — 10-14 jam (kapan-kapan)

---

**Last Updated:** 2026-09-19
**Maintainer:** GhostWriter Dev Team (Multi-AI Collaboration)
**Current Version:** v2.2.2-GW
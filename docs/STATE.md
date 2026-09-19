================================================================================
                    GHOSTWRITER — PROJECT STATE & PROGRESS
================================================================================
Project  : GhostWriter 👻📜 (AI Chat Dump to Web Interface Engine)
Version  : v2.6.6-GW
Phase    : Phase 4 (Polish & Stabilization — IN PROGRESS)
Updated  : 2026-09-19
================================================================================


================================================================================
1. EXECUTIVE SUMMARY
================================================================================

GhostWriter bertransformasi dari CLI parser lokal menjadi tool dual-mode
production-ready:

  [1] Local Converter
      Mengonversi arsip JSON/MD/DOCX offline ke antarmuka web interaktif
      bertema Midnight.

  [2] DeepSeek Live Fetcher
      Terintegrasi langsung via wizard CLI menggunakan Bearer token dari
      Local Storage untuk menarik seluruh riwayat chat + metadata dari
      akun DeepSeek pengguna.

Update terbaru (2026-09-19 — v2.6.6):
  ✓ Sidebar cleanup — hapus tombol search & theme di header, pindah tombol
    close ke footer.
  ✓ Bidirectional swipe gesture — swipe buka + tutup drawer.
  ✓ Auto-close drawer — buka 1 drawer → auto-close drawer lain.

Update terbaru (2026-09-19 — v2.6.4):
  ✓ Full-screen loading overlay dengan progress bar + shimmer effect.
  ✓ Auto-adapt theme (CSS variables).
  ✓ Logo pulse + status text auto-switch.
  ✓ Safety net 3s + reduced-motion support.

Update terbaru (2026-09-19 — v2.6.3):
  ✓ Fix `chatContainer` ReferenceError yang bikin viewer blank.

Update terbaru (2026-09-19 — v2.6.1):
  ✓ Swipe gesture fix (edge priority).
  ✓ Header buttons reorder: `?` → `🌙` → `⋮` → `👤`.
  ✓ Message menu smart positioning.

Update terbaru (2026-09-19 — v2.6.0):
  ✓ Disable zoom (meta + CSS).
  ✓ Zoom layout fix (iOS Safari fallback).
  ✓ Scroll fade + dim + scale animation.
  ✓ PDF export CSS upgrade.

Update terbaru (2026-09-19 — v2.5.0):
  ✓ Action D (Polish Backlog Lama) SELESAI — PR-30, PR-32, PR-33.

Update terbaru (2026-09-19 — v2.4.0):
  ✓ User-Friendly CLI Redesign.

Update terbaru (2026-09-19 — v2.3.0):
  ✓ UI Refactor mobile.
  ✓ 5 bug mobile viewport fixed.
  ✓ Action A (Data Safety) selesai.
  ✓ Action B (UX Quick Wins) selesai.

Update sebelumnya (2026-09-18 — Phase 3 COMPLETE):
  ✓ Multi-format parser: JSON (3 skema), Markdown, DOCX
  ✓ CLI konsisten tema Midnight
  ✓ Incremental backup
  ✓ Human-like delay + jitter anti-suspend
  ✓ HTML viewer enhancements
  ✓ Landing page index.html
  ✓ Auto-generate index.json + index.html
  ✓ Attachment pending manifest
  ✓ Print stylesheet & scroll position memory


================================================================================
2. PROJECT DIRECTORY TREE
================================================================================

GhostWriter/
├── .deepseek_token              [Auto] Token cache (chmod 600)
├── .gitignore                   Ignore public, backups, attachments, cache
├── main.py                      CLI Wizard (lokal & live fetcher)
├── exporter.py                  HTML compiler + auto-index trigger
├── serve.py                     Local HTTP server (auto-detect Termux)
├── sync.py                      Index regenerator + prune stale
├── requirements.txt             Dependencies
│
├── attachments/                 Penyimpanan fisik attachment
│   └── PENDING.md               [Auto] Manifest manual download
│
├── backups/                     Dump JSON hasil live fetcher (versioned)
│   └── backup_*_YYYYMMDD_HHMMSS.json  [Auto] Maks 5 versi terakhir
│
├── public/                      Output HTML + index (di-serve via serve.py)
│   ├── index.html               [Auto] Landing page
│   ├── index.json               [Auto] Metadata index
│   ├── vendor/                  [Auto] Vendor assets
│   └── history/
│       └── <convo_id>/          [Auto] Per-convo folder
│           ├── index.html       Viewer individual
│           └── index-*.html.bak Backup otomatis (maks 3 versi)
│
├── docs/                        Dokumentasi
│   ├── BACKLOG.md
│   ├── CHECKPOINT.md
│   ├── IMPORT_GUIDE.md          [Planned] Tutorial import per platform
│   └── STATE.md
│
├── parsers/                     Modul ekstraksi
│   ├── __init__.py
│   ├── base.py                  ABC BaseParser
│   ├── json_parser.py           Parser JSON adaptif 3 format
│   ├── md_parser.py             Parser Markdown chat
│   ├── docx_parser.py           Parser DOCX chat
│   ├── universal_detector.py    [Planned] Auto-detect platform
│   ├── chatgpt_parser.py        [Planned] ChatGPT parser
│   ├── claude_parser.py         [Planned] Claude parser
│   ├── gemini_parser.py         [Planned] Gemini parser
│   ├── mistral_parser.py        [Planned] Mistral parser
│   ├── poe_parser.py            [Planned] Poe parser
│   └── generic_fallback.py      [Planned] Catch-all fallback
│
├── templates/                   Template engine
│   ├── viewer.html              Viewer individual (Jinja2)
│   └── index.html               Landing page (generated)
│
├── tools/                       Utility & API fetchers
│   ├── __init__.py
│   ├── theme.py                 Midnight color theme
│   ├── loading.py               Spinner, status, progress bar
│   ├── checklist.py             Interactive checklist
│   ├── dist_index.py            Index generator
│   ├── download_vendor.py       Vendor assets downloader
│   └── deepseek_backup.py       Live fetcher
│
└── vendor/                      Vendor assets


================================================================================
3. IMPLEMENTED FEATURES & TECHNICAL FINDINGS
================================================================================

3.1 Multi-Format Parser
────────────────────────────────────────────────────────────────────────────────

JSONChatParser — 3 skema:

  ┌─────────────────────┬──────────────────────────────────────────────┐
  │ Format              │ Struktur                                     │
  ├─────────────────────┼──────────────────────────────────────────────┤
  │ OpenAI mapping      │ {mapping: {node_id: {message: {fragments}}}} │
  │ Generic dict        │ {messages: [{role, content}]}                │
  │ DeepSeek raw        │ {chat_session: {...}, chat_messages: [...]}  │
  └─────────────────────┴──────────────────────────────────────────────┘

MarkdownChatParser:
  ✓ Support heading (###, ##, #) + bold (**User:**) + italic (*User*)
  ✓ Role alias: user, human, assistant, ai, bot, deepseek, chatgpt, claude, gemini
  ✓ Auto-extract title dari H1 pertama

DocxChatParser:
  ✓ Pakai python-docx
  ✓ Same role alias seperti MD parser


3.2 DeepSeek Live Backup — PRODUCTION READY
────────────────────────────────────────────────────────────────────────────────

Fitur:
  ✓ Pagination penuh cursor-based
  ✓ Retry eksponensial 429/5xx
  ✓ Bulk selection: '1', '1,3,5', '1-5', 'all', 'c'
  ✓ Token caching .deepseek_token dengan chmod 600
  ✓ Auto-invalidate token expired
  ✓ Debug mode via GW_DEBUG=1
  ✓ Session tracking
  ✓ Incremental backup via state file
  ✓ PR-31: Circuit breaker untuk attachment pending
  ✓ PR-40A: Graceful token expired handling

Anti-Suspend Strategy:
  ✓ Human-like delay + jitter (1-3s)
  ✓ Session delay (3-7s)
  ✓ Retry delay (5-10s)
  ✓ Configurable via env var

Attachment Strategy:
  ✓ Magic bytes validation
  ✓ HTML guard
  ✓ Size match check
  ✓ Pending manifest auto-generated
  ✓ Inline progress counter


3.3 Attachment Resolution & Constraints
────────────────────────────────────────────────────────────────────────────────

Forensic Discovery:
  • Endpoint /chat/history_messages: metadata lengkap file
  • Endpoint /file/download: BROKEN via Bearer token (HTML challenge)
  • Butuh session cookie (ds_session_id) yang cuma ada di browser

Architectural Solution:
  • json_parser.py handle resolusi lokal via _find_local_file()
  • File gambar otomatis Base64 inline
  • File non-gambar dirender sebagai attachment card
  • User diarahkan lewat attachments/PENDING.md


3.4 CLI Theme (tools/theme.py)
────────────────────────────────────────────────────────────────────────────────

Midnight palette (ANSI 256):
  • ACCENT = #38bdf8, PURPLE = #a78bfa, GREEN = #4ade80
  • YELLOW = #facc15, RED = #f87171, GRAY = #94a3b8, WHITE = #f8fafc

Components:
  • LoadingSpinner — braille/dots/ascii frames
  • print_section, print_status, progress_bar
  • print_bullet, print_numbered, print_kv, print_banner


3.5 HTML Viewer (templates/viewer.html) — v2.6.6 REFACTORED
────────────────────────────────────────────────────────────────────────────────

Layout:
  ┌─────────────────────────────────────────┐
  │  HEADER (slim)                          │
  │  [☰] Title              [?] [🌙] [⋮] [👤]│
  ├─────────────────────────────────────────┤
  │  STATS BAR (sticky)                     │
  ├─────────────────────────────────────────┤
  │  CHAT CONTAINER (scrollable)            │
  │  [▲▼ floating nav]                      │
  ├─────────────────────────────────────────┤
  │  SEARCH BAR (bottom, sticky)            │
  │  [🔍 Cari...]            [N] [✕]        │
  │  [▲ Prev] [▼ Next]                      │
  └─────────────────────────────────────────┘

Sidebar kiri:
  Header: brand (👻 GhostWriter) — minimalis
  List  : multi-convo + date grouping
  Footer: 👻 vX.X-GW + tombol ✕

Right rail:
  Header: 👤 Pesan User + tombol ✕
  List  : user message navigator

Features:
  ✓ Markdown rendering (Marked.js)
  ✓ Syntax highlighting (highlight.js tokyo-night-dark)
  ✓ KaTeX math rendering
  ✓ Search + next match highlight (bottom bar)
  ✓ Copy message + copy code block
  ✓ Collapsible long messages (>800 char)
  ✓ Dark/light theme toggle (localStorage)
  ✓ Scroll position memory
  ✓ Right rail: user message navigator
  ✓ Left sidebar: multi-convo (fetch index.json)
  ✓ Attachment card (Base64 inline)
  ✓ Thinking block styling (details/summary 🧠)
  ✓ Stats bar (pesan, char, token, durasi)
  ✓ Print stylesheet / PDF export upgrade
  ✓ Keyboard shortcuts: /, ?, j, k, Home, End, Esc
  ✓ Floating scroll nav
  ✓ Pretty URL: /history/<convo_id>/
  ✓ Help modal (? shortcut)
  ✓ Message menu (⋯ dropdown)
  ✓ Header dropdown (⋮) — Print only
  ✓ Loading overlay (progress bar) v2.6.4

Mobile Fixes:
  ✓ dvh + safe-area
  ✓ body.searching hide floating nav
  ✓ VisualViewport API (keyboard)
  ✓ Search bar bottom
  ✓ Disable zoom (meta + CSS)
  ✓ Zoom layout fix (iOS fallback)
  ✓ Scroll fade + dim + scale
  ✓ Swipe gesture fix (edge priority)
  ✓ Header buttons reorder
  ✓ Message menu smart positioning
  ✓ Fix chatContainer ReferenceError
  ✓ Full-screen loading overlay
  ✓ Sidebar cleanup
  ✓ Bidirectional swipe + auto-close drawer

Responsive:
  ✓ Mobile: sidebar + right rail drawer overlay
  ✓ Tablet: right rail hidden
  ✓ Desktop: dua-duanya visible

CSS Variables:
  ✓ Semua warna via CSS variables → auto-adapt theme
  ✓ Loading overlay & progress bar auto-adapt

Accessibility:
  ✓ prefers-reduced-motion support
  ✓ Keyboard navigation
  ✓ Touch gesture (swipe bidirectional)


3.6 Landing Page (public/index.html)
────────────────────────────────────────────────────────────────────────────────

Auto-generated oleh tools/dist_index.py:

  ✓ Card list semua convo di public/history/
  ✓ Search real-time (title + timestamp)
  ✓ Sort: Terbaru, Judul (A-Z), Pesan Terbanyak, Ukuran Terbesar
  ✓ Group by date: Hari Ini, Kemarin, 7 Hari Terakhir, 30 Hari, Lebih Lama
  ✓ 2-pass dedup (normal + aggressive fallback)
  ✓ Theme toggle (sync dengan viewer)
  ✓ Stats: visible vs total count
  ✓ Keyboard shortcut: / fokus search
  ✓ Responsive


3.7 Local HTTP Server (serve.py)
────────────────────────────────────────────────────────────────────────────────

  ✓ Serve folder public/ di http://localhost:8000/
  ✓ Auto-detect Termux (termux-open-url)
  ✓ Auto-open browser
  ✓ QuietHandler — filter log asset statis
  ✓ No-cache headers
  ✓ Port conflict handling


3.8 Index Sync + Prune (sync.py)
────────────────────────────────────────────────────────────────────────────────

Usage:
  python3 sync.py                        # Sync biasa
  python3 sync.py --clean                # Sync + prune (konfirmasi)
  python3 sync.py --clean --dry-run      # Preview
  python3 sync.py --clean --yes          # Prune tanpa konfirmasi
  python3 sync.py --clean --keep ID1,ID2 # Manual: keep ID1 & ID2

Fitur:
  ✓ Auto-detect valid convo IDs dari backups/*.json
  ✓ Manual mode --keep
  ✓ Dry-run preview
  ✓ Konfirmasi sebelum hapus
  ✓ Report freed bytes
  ✓ Regenerate index.json + index.html


3.9 Action Fixed Framework
────────────────────────────────────────────────────────────────────────────────

Action Done:
  A (Data Safety)          : PR-39, PR-40, PR-40A ✅
  B (UX Quick Wins)        : PR-42, PR-43 ✅
  UI Refactor (Mobile)     : PR-42A, 42B, 42C, 42D ✅
  CLI Redesign             : PR-42E, 42F, 42G ✅
  D (Polish Backlog)       : PR-30, PR-32, PR-33 ✅
  Mobile Polish v2.6.0     : PR-42H, 42I, 42J, 36 ✅
  Swipe & Reorder v2.6.1   : PR-42K, 42L, 42M ✅
  Blank Fix v2.6.3         : PR-42N ✅
  Loading Overlay v2.6.4   : PR-42O ✅
  Sidebar Cleanup v2.6.6   : PR-42P, 42Q, 42R, 42S ✅

Action Pending:
  C (Index Safety & Scale) : PR-41, PR-46, PR-48 ⏳ NEXT
  E (Perf & Onboarding)    : PR-44, PR-45 ⏳ Pending
  F (PDF Export Lanjutan)  : PR-36B 🕐 Deferred
  G (CLI Convenience)      : PR-47 ⏳ Pending
  H (Termux Integration)   : PR-34 ⏳ Pending
  I (Advanced Features)    : PR-37, PR-38 📋 Backlog
  J (Import Platform Lain) : PR-50 s/d PR-59 📋 PLANNED


3.10 PHASE 5 — PLANNED FEATURES
────────────────────────────────────────────────────────────────────────────────

Action J — Import Platform Lain (Universal)

  VISI:
    Support import dari platform AI lain (ChatGPT, Claude, Gemini,
    Mistral, Poe) dengan auto-detect + universal parser framework.
    User tinggal drop file backup ke folder, GhostWriter auto-detect
    platform, terus render.

  ARSITEKTUR (3 Layer):

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
    │ - {title, created_at, messages: [...]} │
    └─────────────────────────────────────────┘

  PLATFORM COVERAGE:

    ┌────┬──────────────┬─────────────────────────────┬──────────┐
    │ #  │ Platform     │ Format                      │ Effort   │
    ├────┼──────────────┼─────────────────────────────┼──────────┤
    │ 1  │ ChatGPT      │ conversations.json          │ 1.5 jam  │
    │ 2  │ Claude       │ JSON (content blocks)       │ 1.5 jam  │
    │ 3  │ Gemini       │ Google Takeout (HTML)       │ 3 jam    │
    │ 4  │ Mistral      │ JSON                        │ 1 jam    │
    │ 5  │ Poe          │ JSON                        │ 1 jam    │
    │ 6  │ Generic      │ Fallback apapun             │ 1 jam    │
    └────┴──────────────┴─────────────────────────────┴──────────┘

  SUB-PR BREAKDOWN:

    - PR-50: Universal Detector Framework (2 jam)
    - PR-51: ChatGPT Parser (1.5 jam)
    - PR-52: Claude Parser (1.5 jam)
    - PR-53: Gemini Parser (3 jam)
    - PR-54: Mistral Le Chat Parser (1 jam)
    - PR-55: Poe Parser (1 jam)
    - PR-56: Generic Fallback Parser (1 jam)
    - PR-57: Integrate Detector ke main.py (1 jam)
    - PR-58: Per-Platform Testing (2 jam)
    - PR-59: Docs Import Guide (1 jam)

  TIMELINE (Multi-Sesi):

    Sesi 1 (~4 jam): Universal detector + ChatGPT + Generic fallback
    Sesi 2 (~4 jam): Claude + Mistral + integrate ke main.py
    Sesi 3 (~4 jam): Gemini + Poe
    Sesi 4 (~2 jam): Docs + testing + release v2.7.0-GW

    TOTAL: ~14 jam, 4 sesi.

  RISIKO:

    • Schema platform bisa berubah (ChatGPT ganti 3x dalam 2 tahun).
      Parser harus defensive — cek field sebelum akses.
    • Sample file terbatas (Poe, Claude susah dapet sample).
      Solusi: bikin dummy dari schema docs.
    • Gemini paling complex (Google Takeout HTML fragments).
      Butuh HTML parser (BeautifulSoup atau regex).
    • Auto-detect bisa lambat kalo file gede (100+ MB).
      Solusi: peek first 1KB buat deteksi, bukan load full.
    • Test coverage wajib per platform sebelum release.

  REFERENSI:

    • ChatGPT export schema: github.com/gpt4free/gpt4free
    • Claude export: docs.anthropic.com
    • Gemini Takeout: support.google.com/takeout
    • Data Portability: activitypub.rocks, GDPR Article 20

  STATUS: PLANNED — belum eksekusi. Detail lengkap di BACKLOG.md
          section ACTION J.


================================================================================
4. KNOWN LIMITATIONS
================================================================================

  [1] Attachment binary tidak bisa di-download via API
      → Butuh session cookie browser.
      → Solusi: user taruh manual di ./attachments/
      → Mitigasi PR-31: circuit breaker.

  [2] file_id di history_messages kadang kosong
      → API strip metadata untuk security.

  [3] CDN fallback kalo vendor/ kosong

  [4] Termux raw input gak works di on-screen keyboard
      → Checklist interaktif fallback ke mode angka
      → Solusi planned: PR-34 (Action H)

  [5] Scale issue di landing page
      → Kalo 500+ convo, semua card di-render sekaligus (lag).
      → Solusi planned: PR-46 (Action C)

  [6] Gak ada checksum / integrity verification di index
      → Solusi planned: PR-41 (Action C)

  [7] iOS Safari tetep bisa zoom
      → Layout pake "zoomed" class buat fallback
      → Mendingan, gak rusak

  [8] Cuma support DeepSeek + generic + MD/DOCX (Phase 5 planned
      support ChatGPT, Claude, Gemini, dll — see 3.10)


================================================================================
5. PROGRESS SNAPSHOT
================================================================================

  ┌──────────┬────────────────────────────────────┬──────────────┐
  │ Phase    │ Item                               │ Status       │
  ├──────────┼────────────────────────────────────┼──────────────┤
  │ Phase 1  │ Local JSON converter               │ ✅ Done      │
  │ Phase 2  │ DeepSeek live backup               │ ✅ Done      │
  │ Phase 2  │ Attachment strategy                │ ✅ Done      │
  │ Phase 2  │ Multi-format JSON parser           │ ✅ Done      │
  │ Phase 3  │ MD/DOCX parser                     │ ✅ Done      │
  │ Phase 3  │ CLI theme Midnight                 │ ✅ Done      │
  │ Phase 3  │ HTML viewer enhancements           │ ✅ Done      │
  │ Phase 3  │ Landing page + index generator     │ ✅ Done      │
  │ Phase 4  │ Struktur public/history/ migration │ ✅ Done      │
  │ Phase 4  │ serve.py + sync.py                 │ ✅ Done      │
  │ Phase 4  │ BUGFIX #1-#6                       │ ✅ Done      │
  │ Phase 4  │ PR-31 Circuit breaker              │ ✅ Done      │
  │ Phase 4  │ PR-40A Token expired handling      │ ✅ Done      │
  │ Phase 4  │ Action A (Data Safety)             │ ✅ Done      │
  │ Phase 4  │ Action B (UX Quick Wins)           │ ✅ Done      │
  │ Phase 4  │ UI Refactor Mobile                 │ ✅ Done      │
  │ Phase 4  │ User-Friendly CLI Redesign         │ ✅ Done      │
  │ Phase 4  │ Action D (Polish Backlog)          │ ✅ Done      │
  │ Phase 4  │ Mobile Polish v2.6.0               │ ✅ Done      │
  │ Phase 4  │ Swipe & Reorder v2.6.1             │ ✅ Done      │
  │ Phase 4  │ Blank Fix v2.6.3                   │ ✅ Done      │
  │ Phase 4  │ Loading Overlay v2.6.4             │ ✅ Done      │
  │ Phase 4  │ Sidebar Cleanup v2.6.6             │ ✅ Done      │
  │ Phase 4  │ Action C (Index Safety & Scale)    │ ⏳ Next      │
  │ Phase 5  │ Action E (Perf & Onboarding)       │ ⏳ Pending   │
  │ Phase 5  │ Action F (PDF Export Lanjutan)     │ 🕐 Deferred  │
  │ Phase 5  │ Action G (CLI Convenience)         │ ⏳ Pending   │
  │ Phase 5  │ Action H (Termux Integration)      │ ⏳ Pending   │
  │ Phase 5  │ Action I (Advanced Features)       │ 📋 Backlog   │
  │ Phase 5  │ Action J (Import Platform Lain)    │ 📋 Planned   │
  └──────────┴────────────────────────────────────┴──────────────┘


================================================================================
6. NEXT STEPS
================================================================================

Priority 1 — Action C: Index Safety & Scale (4-5 jam)
  • PR-41: Checksum / Manifest di Index.json
  • PR-46: Pagination / Infinite Scroll di Landing Page
  • PR-48: Auto-Detect Broken Links di Index
  • Files: tools/dist_index.py, sync.py

Priority 2 — Action E: Perf & Onboarding (3 jam)
  • PR-44: Onboarding Tour Pertama Kali
  • PR-45: Lazy Load Attachment Images
  • Files: templates/viewer.html, tools/dist_index.py, parsers/json_parser.py

Priority 3 — Action G: CLI Convenience (30 menit)
  • PR-47: CLI Flag --stats
  • Files: main.py

Priority 4 — Action F: PDF Export Lanjutan (2-4 jam)
  • PR-36B: Auto-Set PDF Title + Print Preview Tweak

Priority 5 — Action H: Termux Integration (1-2 jam)
  • PR-34: Termux API Integration

Priority 6 — Action I: Advanced Features (10-14 jam, BACKLOG)
  • PR-37: Category/Tag untuk Convo
  • PR-38: Diff View

Priority 7 — Action J: Import Platform Lain (14 jam, 4 sesi, PLANNED)
  • PR-50: Universal Detector Framework
  • PR-51: ChatGPT Parser
  • PR-52: Claude Parser
  • PR-53: Gemini Parser
  • PR-54: Mistral Parser
  • PR-55: Poe Parser
  • PR-56: Generic Fallback Parser
  • PR-57: Integrate Detector ke main.py
  • PR-58: Per-Platform Testing
  • PR-59: Docs Import Guide
  • Files: parsers/*.py, main.py, docs/IMPORT_GUIDE.md


================================================================================
7. FORENSIC NOTES
================================================================================

7.1 Session API DeepSeek — Raw Response Keys
────────────────────────────────────────────────────────────────────────────────

{
  "chat_session": {
    "id", "title", "inserted_at", "updated_at",
    "model_type", "current_message_id", "version"
  },
  "chat_messages": [
    {
      "message_id", "parent_id", "role", "content",
      "files", "thinking_content", "search_results",
      "inserted_at", "model"
    }
  ],
  "cache_valid": false,
  "route_id": null
}

Catatan:
  • role UPPERCASE (USER, ASSISTANT)
  • inserted_at float epoch
  • files[].id = "file-{uuid}" format
  • search_results cuma muncul kalo search_enabled: true
  • thinking_content cuma muncul kalo thinking_enabled: true


7.2 Endpoint Behaviors
────────────────────────────────────────────────────────────────────────────────

  /users/current
    → verify token valid

  /chat_session/fetch_page
    → list sesi dengan cursor pagination

  /chat/history_messages?chat_session_id=X
    → full message dump per sesi

  /file/download?file_id=X
    → BROKEN via Bearer token, balikin HTML challenge


7.3 Account Suspension Lessons Learned
────────────────────────────────────────────────────────────────────────────────

Trigger hypothesis:
  • Repeated prompt upload → flag "cross-platform copying"
  • Pattern request berubah drastis → risk control trigger

Mitigation:
  • Human-like delay + jitter (1-3s)
  • Session delay (3-7s)
  • Retry delay (5-10s)
  • Incremental backup


7.4 JavaScript Parse Error Cascade (Bugfix v2.2)
────────────────────────────────────────────────────────────────────────────────

Fenomena:
  Kurung kurawal `}` salah posisi di viewer.html (loadDistIndex)
  bikin SELURUH <script> gagal parse.

Lesson:
  • Browser JS parser forgiving — error muncul di baris yang gak berhubungan.
  • Selalu cek Console (F12).


7.5 Circuit Breaker Pattern (v2.2.2)
────────────────────────────────────────────────────────────────────────────────

Konteks:
  Kalo backup convo banyak attachment, tiap attachment butuh delay 1-3s.
  Tapi kalo endpoint /file/download balikin HTML, SEMUA request gagal.

Solusi (PR-31):
  Circuit breaker — 1x kena HTML challenge → set flag.

Efek: 50-150 detik → 1-3 detik (97% saving).


7.6 Mobile Viewport Fragmentation (v2.3.0)
────────────────────────────────────────────────────────────────────────────────

Fenomena:
  Keyboard mobile + address bar + safe-area bikin layout rusak.

Solusi (PR-42A/B/C/D):
  • CSS: 100dvh + env(safe-area-inset-bottom)
  • CSS: body.searching hide floating nav
  • JS: window.visualViewport API
  • UI: Search bar pindah ke bottom


7.7 Backup Versioning + Retention (v2.5.0)
────────────────────────────────────────────────────────────────────────────────

Solusi (PR-32):
  • Backup filename dengan timestamp
  • Retention policy: maks 5 versi
  • Helper: _generate_backup_name() + _prune_old_backups()


7.8 Prune Stale Folder (v2.5.0)
────────────────────────────────────────────────────────────────────────────────

Solusi (PR-33):
  • Flag --clean di sync.py
  • Auto-detect valid IDs dari backups/*.json
  • Dry-run mode + konfirmasi


7.9 Scroll Fade + Dim + Scale (v2.6.0)
────────────────────────────────────────────────────────────────────────────────

Solusi (PR-42J):
  • 4 state: init, active, dim-above, dim-below
  • IntersectionObserver 2-pass
  • CSS: opacity + transform (GPU-accelerated)


7.10 Loading Overlay (v2.6.4)
────────────────────────────────────────────────────────────────────────────────

Solusi (PR-42O):
  • Full-screen overlay dengan logo pulse + progress bar
  • Fake progress 0 → 85% → 100%
  • Shimmer effect + auto-adapt theme
  • Safety net 3s


7.11 Bidirectional Swipe Gesture (v2.6.6)
────────────────────────────────────────────────────────────────────────────────

Solusi (PR-42R):
  • Swipe bidirectional: buka + tutup drawer
  • Edge priority: dari tepi = gak skip
  • Auto-close: buka 1 drawer → nutup yang lain


================================================================================
8. UNIVERSAL IMPORT — TECHNICAL SPEC (PLANNED)
================================================================================

8.1 Arsitektur
────────────────────────────────────────────────────────────────────────────────

Tujuan:
  Universal import dari semua platform AI chat. User tinggal drop file
  backup ke folder project, GhostWriter auto-detect platform, terus render.

Layer 1 — DETECTOR (parsers/universal_detector.py):

  Input: file path.
  Output: platform name + parser class (kalo match) atau None.

  Detection strategy:

    1. Filename pattern:
       - "conversations.json" → ChatGPT
       - "chat_messages.json" → Claude
       - "Takeout/Gemini/*.html" → Gemini
       - "backup_*.json" dengan "chat_session" → DeepSeek
       - "*.md" → Markdown parser
       - "*.docx" → DOCX parser

    2. Key signature (peek first 1KB):
       - Keys {mapping, conversation_id, author} → ChatGPT
       - Keys {chat_messages, role: "human"} → Claude
       - Keys {chat_session, chat_messages} → DeepSeek
       - Keys {messages, role} → Generic
       - HTML <div class="...conversation..."> → Gemini Takeout

    3. Fallback: generic_parser (heuristic detection).

  Performance:
    Peek first 1KB aja buat deteksi (gak load full file).
    Kalo file < 1KB, load full.

Layer 2 — PARSER REGISTRY (parsers/*.py):

  Semua parser inherit dari BaseParser (ABC). Interface:

    class BaseParser(ABC):
        @abstractmethod
        def validate(self) -> bool: ...
        @abstractmethod
        def list_conversations(self) -> List[Dict]: ...
        @abstractmethod
        def parse(self, convo_index: int = None) -> Dict: ...

  Registry:
    PLATFORM_PARSERS = {
      "chatgpt": ChatGPTParser,
      "claude": ClaudeParser,
      "gemini": GeminiParser,
      "mistral": MistralParser,
      "poe": PoeParser,
      "deepseek": JSONChatParser,
      "markdown": MarkdownChatParser,
      "docx": DocxChatParser,
      "generic": GenericParser,
    }

Layer 3 — NORMALIZER (built-in di BaseParser):

  Semua parser WAJIB return skema seragam:

    {
      "title": str,
      "created_at": str,
      "messages": [
        {
          "role": "user" | "assistant" | "system",
          "content": str,
          "timestamp": str
        }
      ]
    }

  Kalo format punya multiple convo (misal ChatGPT conversations.json),
  parser return list of convo, dan main.py render semuanya.


8.2 Platform Schema Notes
────────────────────────────────────────────────────────────────────────────────

ChatGPT (conversations.json):
  - Root: array of conversations.
  - Per convo: {title, create_time, mapping, current_node}.
  - mapping: {node_id: {id, message, parent, children}}.
  - message: {id, author: {role}, content: {content_type, parts}, create_time}.
  - content_type: "text" | "code" | "multimodal_text".
  - parts: array (string atau object dengan asset_pointer).
  - Traversal: dari current_node ke parent recursively, reverse order.

Claude (export JSON):
  - Root: {uuid, name, created_at, chat_messages}.
  - chat_messages: array.
  - Per message: {uuid, text, content: [blocks], sender, created_at}.
  - sender: "human" | "assistant".
  - content blocks: {type: "text", text} | {type: "image", source} |
    {type: "tool_use", name, input} | {type: "tool_result", content}.

Gemini (Google Takeout):
  - Format: HTML fragments (bukan JSON).
  - File: "My Activity/Gemini Apps/My Activity.html" atau
    "Takeout/Gemini/*.html".
  - Struktur: <div class="outer-cell"> per aktivitas.
  - Per aktivitas: {timestamp, prompt, response} dalam <div>.
  - Parsing: BeautifulSoup atau regex (html.parser).
  - Paling complex — butuh HTML parser.

Mistral Le Chat:
  - Format: JSON (mirip Claude).
  - Per message: {role, content}.
  - Content: string atau array of blocks.

Poe (Quora):
  - Format: JSON.
  - Per convo: {title, messages: [{role, content, timestamp}]}.


8.3 Roadmap Eksekusi
────────────────────────────────────────────────────────────────────────────────

Sesi 1 (~4 jam) — Foundation:
  1. PR-50: Universal Detector Framework
  2. PR-51: ChatGPT Parser
  3. PR-56: Generic Fallback Parser
  4. PR-57: Integrate Detector ke main.py
  Deliverable: Bisa auto-detect + parse ChatGPT.

Sesi 2 (~4 jam) — Populer Platforms:
  1. PR-52: Claude Parser
  2. PR-54: Mistral Parser
  3. Update detector
  Deliverable: Support ChatGPT, Claude, Mistral, DeepSeek, MD, DOCX.

Sesi 3 (~4 jam) — Complex Platforms:
  1. PR-53: Gemini Parser (HTML fragments)
  2. PR-55: Poe Parser
  3. Update detector
  Deliverable: Full 6 platform support.

Sesi 4 (~2 jam) — Polish:
  1. PR-58: Per-Platform Testing
  2. PR-59: Docs Import Guide (docs/IMPORT_GUIDE.md)
  3. Update STATE.md + BACKLOG.md
  4. Bump version ke v2.7.0-GW + release
  Deliverable: v2.7.0-GW released.


8.4 File Structure (After Phase 5)
────────────────────────────────────────────────────────────────────────────────

  parsers/
  ├── __init__.py
  ├── base.py                    (ABC)
  ├── json_parser.py             (DeepSeek + generic)
  ├── md_parser.py               (Markdown)
  ├── docx_parser.py             (DOCX)
  ├── universal_detector.py      [NEW] Auto-detect
  ├── chatgpt_parser.py          [NEW]
  ├── claude_parser.py           [NEW]
  ├── gemini_parser.py           [NEW]
  ├── mistral_parser.py          [NEW]
  ├── poe_parser.py              [NEW]
  └── generic_fallback.py        [NEW]


8.5 Testing Strategy
────────────────────────────────────────────────────────────────────────────────

Sample files (taruh di tests/samples/, gitignored):
  - chatgpt_sample.json       (cari di GitHub gist)
  - claude_sample.json        (dummy dari schema)
  - gemini_sample.html        (dummy HTML)
  - mistral_sample.json       (dummy)
  - poe_sample.json           (dummy)

Test case per platform:
  - Validasi: file valid → parse sukses
  - List convo: hitung jumlah convo bener
  - Parse convo #0: cek message count, title, timestamps
  - Edge case: file kosong, file corrupt, file schema beda


8.6 Referensi
────────────────────────────────────────────────────────────────────────────────

  • ChatGPT: github.com/gpt4free/gpt4free (contoh parser)
  • Claude: docs.anthropic.com/en/docs/export
  • Gemini Takeout: support.google.com/takeout/answer/7021273
  • GDPR Article 20: gdpr-info.eu/art-20-gdpr
  • ActivityPub: activitypub.rocks
  • IndieWeb: indieweb.org


================================================================================
                     END OF STATE — GHOSTWRITER v2.6.6-GW
================================================================================
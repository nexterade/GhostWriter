================================================================================
STATE.md — GhostWriter+
Snapshot Status Teknis, Arsitektur, & Fitur
================================================================================
Versi    : v2.6.9-GW
Update   : 2026-09-20
Author   : @nexterade
Berlaku  : Seluruh komponen proyek GhostWriter+
📎 FILE TERKAIT:
   · CHECKPOINT.md   : aturan baku & filosofi proyek
   · docs/BACKLOG.md : checklist PR & fitur pending
================================================================================


================================================================================
1. OVERVIEW PROYEK
================================================================================

GhostWriter adalah tool CLI Python untuk mengarsipkan dan membaca konten
digital secara lokal, dengan output HTML interaktif yang bisa dibuka via
browser lokal.

Fitur utama:
  · Render arsip obrolan AI (DeepSeek, dsb) jadi web viewer interaktif
  · Live backup dari akun DeepSeek (via token DevTools)
  · Import PDF ebook (image mode — cocok buat scan)
  · Import comic ZIP (manga, webtoon, comic strip)
  · Landing page unified dengan tab, search, sort, filter

Target user:
  · Developer yang mau arsip chat AI secara lokal
  · Pembaca ebook/comic yang mau viewer ringan offline

Prinsip:
  · Local-first — semua data disimpan di device user
  · No-cloud — gak ada server backend, semua static HTML
  · Fast — ringan, bisa jalan di Termux/Android
  · Konsisten visual — theme dark/light, animasi smooth


================================================================================
2. ARSITEKTUR FOLDER
================================================================================

project/
├── main.py                          # CLI entry point + wizard mode
├── serve.py                         # Local HTTP server (serve public/)
├── sync.py                          # Regenerate index.json + index.html
├── exporter.py                      # HTMLExporter buat chat viewer
├── requirements.txt                 # Python dependencies
├── README.md                        # Dokumentasi umum
├── CONTRIBUTING.md                  # Panduan kontribusi
├── Licence.md                       # Lisensi
├── CHECKPOINT.md                    # Aturan baku proyek (root, bukan docs/)
│
├── docs/                            # Dokumentasi dinamis
│   ├── STATE.md                     # ← file ini (snapshot status)
│   └── BACKLOG.md                   # Checklist PR & fitur pending
│
├── inputs/                          # Folder input default
│   ├── *.json / *.md / *.docx       # File backup chat
│   ├── *.pdf                        # PDF ebook
│   └── *.zip                        # Comic ZIP
│
├── public/                          # Output HTML (di-serve)
│   ├── index.html                   # Landing page (auto-generated)
│   ├── index.json                   # Metadata index (auto-generated)
│   ├── history/                     # Chat viewer output
│   │   └── <convo_id>/
│   │       └── index.html
│   ├── readers/                     # Ebook output
│   │   └── <slug>/
│   │       ├── index.html
│   │       └── images/
│   │           ├── page_001.jpg
│   │           └── ...
│   ├── comics/                      # Comic output
│   │   └── <slug>/
│   │       ├── index.html
│   │       └── images/
│   │           ├── page_001.jpg
│   │           └── ...
│   ├── vendor/                      # JS/CSS libraries
│   │   ├── marked.min.js
│   │   ├── highlight.min.js
│   │   ├── katex.min.js
│   │   └── ...
│   └── data/                        # (optional) extra data
│
├── templates/                       # Template HTML
│   ├── viewer.html                  # Template chat viewer
│   └── reader.html                  # Template ebook/comic reader
│
├── parsers/                         # Parser file input
│   ├── __init__.py
│   ├── json_parser.py               # JSONChatParser
│   ├── md_parser.py                 # MarkdownChatParser
│   └── docx_parser.py               # DocxChatParser
│
├── importers/                       # Importer PDF & Comic
│   ├── __init__.py
│   ├── _reader_common.py            # Helper DRY (slug, render, payload)
│   ├── pdf_importer.py              # handle_pdf_import()
│   └── comic_importer.py            # handle_comic_import()
│
├── tools/                           # Utility modules
│   ├── __init__.py
│   ├── theme.py                     # C (colors), get_theme(), LOGO_SVG_INLINE
│   ├── loading.py                   # LoadingSpinner, print_* helpers
│   ├── checklist.py                 # interactive_checklist()
│   ├── dist_index.py                # Index generator (chat + ebook + comic)
│   └── deepseek_backup.py           # DeepSeekLiveBackup class
│
├── backups/                         # Backup file chat (.json)
│   └── backup_<slug>_<timestamp>.json
│
├── attachments/                     # Attachment chat (manual download)
│   └── PENDING.md                   # List attachment yang perlu download manual
│
├── .deepseek_token                  # Token cache (chmod 600)
└── .gitignore                       # Ignore: public/, backups/, inputs/, dll


================================================================================
3. DEPENDENCY & ENVIRONMENT
================================================================================

Python version:
  · Python 3.8+ (tested di Termux Python 3.11)

Python packages (requirements.txt):
  · pypdf              # Baca metadata & count halaman PDF
  · pdf2image          # Render PDF → PIL images (butuh Poppler)
  · Pillow             # Save image ke disk
  · python-docx        # Parse file .docx
  · requests           # HTTP request (DeepSeek backup)

System dependencies:
  · Poppler (pdftoppm) — WAJIB buat PDF importer
    - Termux  : pkg install poppler
    - Ubuntu  : sudo apt install poppler-utils
    - macOS   : brew install poppler

Tested environment:
  · Termux (Android) — primary
  · Ubuntu 22.04 — secondary
  · Windows 10/11 — partial (belum test Poppler)


================================================================================
4. ALUR KERJA (WORKFLOW)
================================================================================

4.1 IMPORT CHAT DARI BACKUP JSON
─────────────────────────────────
1. User taruh file .json backup di inputs/
2. Jalankan: python3 main.py
3. Pilih menu [1] — Render backup lokal
4. Pilih file dari list atau input path manual
5. main.py:
   - Parse file via JSONChatParser / MarkdownChatParser / DocxChatParser
   - Validasi integrity (PR-40)
   - Export ke public/history/<convo_id>/index.html
6. Landing page (index.json) update otomatis via sync.py

4.2 LIVE BACKUP DARI DEEPSEEK
──────────────────────────────
1. Jalankan: python3 main.py
2. Pilih menu [2] — Sedot live dari DeepSeek
3. Paste token dari DevTools (chat.deepseek.com)
4. Pilih obrolan (range / checklist / all)
5. main.py:
   - Fetch daftar obrolan via API DeepSeek
   - Backup per obrolan ke backups/backup_<slug>_<timestamp>.json
   - Auto-prune backup lama (keep 5 versi terbaru)
   - Auto-render ke public/history/
6. Attachment yang diblokir DeepSeek ditulis di attachments/PENDING.md

4.3 IMPORT PDF EBOOK
─────────────────────
1. User taruh file .pdf di inputs/
2. Jalankan: python3 main.py
3. Pilih menu [3] — Import Ebook PDF
4. Pilih PDF dari list atau input path manual
5. importers/pdf_importer.py:
   - Baca metadata (title, author, pages) via pypdf
   - Render tiap halaman → JPEG (DPI 150, quality 85) via pdf2image
   - Save ke public/readers/<slug>/images/page_NNN.jpg
   - Generate HTML via render_reader_html() pakai templates/reader.html
6. Landing page update otomatis

4.4 IMPORT COMIC ZIP
─────────────────────
1. User taruh file .zip di inputs/
2. Jalankan: python3 main.py
3. Pilih menu [4] — Import Comic ZIP
4. Pilih ZIP dari list atau input path manual
5. importers/comic_importer.py:
   - Inspect ZIP (list image, natural sort)
   - Extract image → keep format asli (.jpg/.png/.webp/dll)
   - Save ke public/comics/<slug>/images/page_NNN.<ext>
   - Generate HTML via render_reader_html() pakai templates/reader.html
6. Landing page update otomatis


================================================================================
5. STRUKTUR DATA (SCHEMA)
================================================================================

5.1 CHAT DATA (hasil parse)
────────────────────────────
{
  "title": "Judul Percakapan",
  "messages": [
    {
      "role": "user" | "assistant" | "system",
      "content": "Isi pesan (markdown)",
      "timestamp": "HH:MM" (optional),
      "attachments": [...] (optional)
    }
  ]
}

5.2 READER PAYLOAD (ebook/comic)
─────────────────────────────────
{
  "title": "Judul Ebook/Comic",
  "author": "Author Name" (optional, ""),
  "pages": 145,
  "sections": [
    {
      "page": 1,
      "type": "image",
      "src": "images/page_001.jpg"
    },
    {
      "page": 2,
      "type": "image",
      "src": "images/page_002.jpg"
    }
  ]
}

5.3 INDEX.JSON SCHEMA
──────────────────────
{
  "count": 27,
  "count_by_type": {
    "chat": 24,
    "ebook": 2,
    "comic": 1
  },
  "generated_at": "2026-09-20T03:15:45",
  "items": [
    {
      "id": "1789829764",
      "folder": "history/1789829764",
      "title": "Pahami GhostWriter",
      "type": "chat",
      "size_kb": 881.7,
      "msg_count": 108,
      "pages": 0,
      "created_at": "",
      "first_created": "18:24",
      "mtime": 1789829742.06
    },
    {
      "id": "jatuh-cinta-ke-angkasa",
      "folder": "readers/jatuh-cinta-ke-angkasa",
      "title": "Jatuh Cinta ke Angkasa",
      "type": "ebook",
      "size_kb": 16001.7,
      "msg_count": 0,
      "pages": 145,
      "created_at": "Ebook · 145 halaman · Nabilla Anasty Fahzaria",
      "first_created": "",
      "mtime": 1789829742.06
    },
    {
      "id": "bukatsu-ato-senpai-...",
      "folder": "comics/bukatsu-ato-senpai-...",
      "title": "Bukatsu Ato Senpai ...",
      "type": "comic",
      "size_kb": 4096.0,
      "msg_count": 0,
      "pages": 12,
      "created_at": "Comic · 12 halaman · Comic Source",
      "first_created": "",
      "mtime": 1789829742.06
    }
  ]
}


================================================================================
6. STATUS FITUR — DONE ✅
================================================================================

6.1 CORE
────────────────────────────────────
✅ Wizard mode interaktif (menu 6 opsi)
✅ CLI mode: python3 main.py backup.json --all --chat-index N
✅ Config input dir (inputs/, fallback root)
✅ Token cache (.deepseek_token, chmod 600)

6.2 PARSER
────────────────────────────────────
✅ JSONChatParser — parse file backup JSON
✅ MarkdownChatParser — parse file .md
✅ DocxChatParser — parse file .docx
✅ Integrity check (PR-40) — validate chat_data

6.3 RENDER CHAT
────────────────────────────────────
✅ HTMLExporter — render chat_data → HTML
✅ Template viewer.html dengan:
   - Sidebar kiri (history list, group by date)
   - Right rail (navigasi pesan user)
   - Search & highlight
   - Copy pesan (per pesan + copy code)
   - Export pesan (markdown, link, save .md)
   - Theme toggle (dark/light)
   - Print / Save as PDF (CSS @media print)
   - Keyboard shortcuts (?, /, j/k, Home/End, Esc)
   - Swipe gesture (mobile)
   - Loading overlay
   - Floating nav (scroll top/bottom)

6.4 LIVE BACKUP DEEPSEEK
────────────────────────────────────
✅ Fetch session list dari akun DeepSeek
✅ Incremental & full mode
✅ Checklist interaktif (tools/checklist.py)
✅ Backup versioning (keep 5 versi terbaru)
✅ Attachment manifest (attachments/PENDING.md)
✅ Auto-invalidate token expired

6.5 IMPORT PDF
────────────────────────────────────
✅ PDF importer (image-only mode, DPI 150, JPEG q85)
✅ Metadata extraction (title, author, pages)
✅ Poppler check (graceful error kalau missing)
✅ Progress spinner per step
✅ Cleanup on fail (hapus folder output)
✅ Hapus folder lama kalau slug sama (fix duplikat)

6.6 IMPORT COMIC
────────────────────────────────────
✅ Comic ZIP importer (keep format asli)
✅ Natural sort (1, 2, 10 — bukan 1, 10, 2)
✅ Skip __MACOSX, ._*, .DS_Store, Thumbs.db
✅ Flatten nested folder
✅ Progress spinner per step
✅ Cleanup on fail
✅ Hapus folder lama kalau slug sama

6.7 READER VIEWER (reader.html)
────────────────────────────────────
✅ Loading overlay
✅ Sidebar kiri (info judul, page jump)
✅ Right rail (page number nav)
✅ Header (sidebar toggle, badge tipe, theme, fullscreen, page nav)
✅ Stats bar (total halaman, halaman saat ini, tipe)
✅ Floating nav (prev/next page, scroll top/bottom)
✅ Help modal (keyboard shortcuts)
✅ Theme toggle (dark/light)
✅ Fullscreen mode (via tombol ⛶)
✅ Swipe gesture (mobile)
✅ Keyboard shortcuts (?, f, j/k, Home/End, Esc)
✅ Image lazy load (loading="lazy")
✅ Scroll fade animation (IntersectionObserver)
✅ Auto-save scroll position (localStorage)
✅ Auto-resume scroll position (localStorage)
✅ Toast notification

6.8 LANDING PAGE (index.html)
────────────────────────────────────
✅ Tab bar: [Semua] [Chat] [Ebook] [Comic]
✅ Search global (filter by title)
✅ Sort: Terbaru / Judul A-Z / Pesan Terbanyak / Halaman Terbanyak / Ukuran
✅ Date grouping (Hari Ini, Kemarin, 7 Hari Terakhir, ...)
✅ Badge tipe (emoji per tipe)
✅ Meta info per tipe (chat: msg_count, ebook/comic: pages)
✅ Theme toggle
✅ Persist active tab (localStorage)
✅ Count by type di tab
✅ Keyboard shortcut (/) — focus search

6.9 SYNC & INDEX
────────────────────────────────────
✅ sync.py — regenerate index.json + index.html
✅ scan_dist() — scan public/history/*/index.html
✅ scan_readers() — scan public/readers/*/index.html
✅ scan_comics() — scan public/comics/*/index.html
✅ Dedup by title (PR-30)
✅ Date grouping
✅ Auto-sync setelah render (chat/PDF/comic)


================================================================================
7. STATUS FITUR — PENDING ⏳
================================================================================

7.1 TIER 1 — READER (High Impact, Low Effort)
──────────────────────────────────────────────
⏳ R1  Auto-bookmark + Resume notif (mostly done, tinggal notif)
⏳ R2  Toggle hide navbar
⏳ R3  Fullscreen exit fix (mobile) — CRITICAL: tombol keluar hilang
⏳ R4  Zoom pinch / double-tap
⏳ R5  Reading progress bar
⏳ R6  Page slider (scrubber)

7.2 TIER 2 — READER (Nice-to-Have)
───────────────────────────────────
⏳ R7  Thumbnail grid navigasi
⏳ R8  Reading stats (waktu baca, halaman/hari, streak)
⏳ R9  Night mode auto (18:00-06:00)
⏳ R10 Brightness control (slider)
⏳ R11 Fit mode toggle (width/height/original/cover)
⏳ R12 Continuous vs Paged mode
⏳ R13 Two-page view (landscape)
⏳ R14 RTL mode (manga)
⏳ R15 Webtoon mode (gap 0, full-width)

7.3 TIER 1 — VIEWER (High Impact, Low Effort)
──────────────────────────────────────────────
⏳ V1  Auto-scroll resume polish (mostly done)
⏳ V2  Export chat → Markdown (all)
⏳ V3  Export chat → PDF polish
⏳ V4  Export chat → JSON
⏳ V5  Search regex support
⏳ V6  Copy all from AI (1 click)

7.4 TIER 2 — VIEWER (Nice-to-Have)
───────────────────────────────────
⏳ V8  Collapse/expand semua bubble panjang
⏳ V9  Filter by role (user/AI)
⏳ V10 Chat stats lengkap (kata, char, token per role)
⏳ V11 Reading time estimate
⏳ V12 Highlight / bookmark pesan (butuh backend)
⏳ V13 Note per pesan (butuh backend)

7.5 TIER 1 — GLOBAL (High Impact, Low Effort)
──────────────────────────────────────────────
⏳ G1  Auto-sync setelah render (PARTIAL — perlu difinalisasi)
⏳ G2  Keyboard nav di landing (j/k, Enter)
⏳ G3  Recent activity section
⏳ G4  Favorites / starred (butuh localStorage)
⏳ G5  Grid vs list view toggle
⏳ G6  Dark/light auto (sesuai sistem)

7.6 TIER 2 — GLOBAL (Nice-to-Have)
───────────────────────────────────
⏳ G8  Filter by date range
⏳ G9  Stats dashboard

7.7 PR PENDING (dari analisis awal)
────────────────────────────────────
⏳ 2.1 Refactor _prompt & _prompt_yes_no → tools/prompt.py
⏳ 2.2 Pindahin _print_post_render_hint() → tools/loading.py
⏳ 2.3 Rapihin import argparse di main.py (unused?)
⏳ 4.1 Update README.md — tambah fitur PDF & Comic
⏳ 4.2 Update CONTRIBUTING.md — panduan importers
⏳ 4.3 Update CHECKPOINT.md — aturan importers & reader
⏳ 6.2 Optimize scan_dist() — 1x baca HTML (bukan 3x)
⏳ 6.3 Cache _get_menu_context() — biar gak scan folder tiap menu
⏳ 6.4 Virtualisasi reader.html — buat 100+ halaman
⏳ 6.5 Optimize search viewer.html — TreeWalker bisa slow

7.8 FITUR YANG DI-SKIP (Tier 3 — sengaja)
──────────────────────────────────────────
❌ R16 PWA / Offline install
❌ R17 Annotation / highlight PDF
❌ R18 OCR text search
❌ R19 Bookmark manual (label)
❌ R20 Notes per halaman
❌ V14 Search multi-chat
❌ V15 Chat comparison
❌ V16 LLM tag extraction
❌ G7 Tag / kategori (butuh UI editor)
❌ G10 Export/import data (kompleks)
❌ G11 PWA install
❌ G12 Multi-user
❌ G13 Sync ke cloud
❌ G14 Web clipper


================================================================================
8. DECISION LOG (KEPUTUSAN TEKNIS)
================================================================================

8.1 PDF IMPORTER — IMAGE MODE ONLY
───────────────────────────────────
Keputusan : Skip text extraction, image-only.
Alasan    : PDF scan modern kebanyakan image-based, text extraction
            gak reliable. User explicitly request image mode.
Impact    : Gak ada OCR, gak ada search text. Kalau butuh, tambah nanti.

8.2 KEEP FORMAT ASLI (COMIC)
─────────────────────────────
Keputusan : Comic importer keep format asli (.jpg, .png, .webp, dll).
Alasan    : Re-encode bisa lossy, hemat CPU, preserve animasi GIF.
Impact    : Image lebih variatif, tapi gak masalah buat browser modern.

8.3 NATURAL SORT (COMIC)
─────────────────────────
Keputusan : Pakai natural sort (1, 2, 10) bukan alfabet (1, 10, 2).
Alasan    : Comic biasanya urut halaman, natural sort lebih intuitif.
Implement : re.split(r'(\d+)', name) → compare list.

8.4 FOLDER OVERWRITE (PDF/COMIC)
─────────────────────────────────
Keputusan : Hapus folder lama kalau slug sama (bukan bikin `-2`).
Alasan    : User render ulang file sama, gak mau numpuk folder.
Fallback  : Kalau hapus gagal (permission error), pakai _unique_folder_name.

8.5 TAB DI LANDING PAGE
────────────────────────
Keputusan : Tab bar [Semua] [Chat] [Ebook] [Comic], default Chat.
Alasan    : Backward-compatible (user lama gak bingung), scalable.
Implement : data-type attribute per item, filter via JS.

8.6 AUTO-SYNC SETELAH RENDER
─────────────────────────────
Keputusan : Auto-jalanin sync.py via subprocess (isolated).
Alasan    : Kalau sync.py error, handler tetap sukses.
Status    : PARTIAL — perlu difinalisasi (lihat BACKLOG).

8.7 CSS IMAGE READER
─────────────────────
Keputusan : .reader-page { overflow: visible, no bg, no border }.
Alasan    : Fix image crop + hilangkan padding gelap.
Impact    : Image full-width, edge-to-edge.

8.8 FULLSCREEN MODE
────────────────────
Keputusan : Hide sidebar, right rail, header, stats bar. Image 100vw.
Alasan    : Fokus baca, immersive.
Issue     : Tombol exit hilang di mobile (lihat BACKLOG R3).

8.9 THEME STORAGE
──────────────────
Keputusan : localStorage key `gw-theme` (shared semua viewer).
Alasan    : Konsisten di seluruh app, user pilih sekali.
Impact    : Chat viewer, reader, landing page pakai theme sama.


================================================================================
9. TESTING CHECKLIST
================================================================================

9.1 SMOKE TEST (setelah clone)
───────────────────────────────
1. python3 main.py → menu muncul 6 opsi
2. Pilih [5] Tutorial → tampil lengkap
3. Pilih [0] → keluar dengan pesan

9.2 IMPORT PDF TEST
────────────────────
1. Taruh PDF 5-10 halaman di inputs/
2. python3 main.py → [3] → pilih PDF
3. Cek public/readers/<slug>/index.html ada
4. Cek public/readers/<slug>/images/page_001.jpg ada
5. Buka via serve.py → image muncul full-width
6. Cek landing page → ebook muncul dengan N halaman

9.3 IMPORT COMIC TEST
──────────────────────
1. Taruh ZIP 5-10 gambar di inputs/
2. python3 main.py → [4] → pilih ZIP
3. Cek public/comics/<slug>/index.html ada
4. Cek urutan halaman benar (natural sort)
5. Buka via serve.py → image muncul full-width
6. Cek landing page → comic muncul

9.4 CHAT RENDER TEST
─────────────────────
1. Taruh file .json backup di inputs/
2. python3 main.py → [1] → pilih file
3. Cek public/history/<convo_id>/index.html ada
4. Buka via serve.py → bubble markdown, code highlight, katex
5. Cek sidebar, right rail, search, copy, export

9.5 SYNC TEST
──────────────
1. python3 sync.py
2. Cek public/index.json ada `count_by_type`
3. Cek public/index.html tab bar muncul
4. Cek default tab = chat


================================================================================
10. KNOWN ISSUES
================================================================================

10.1 CRITICAL
──────────────
🔴 Fullscreen exit button hilang di mobile
   File   : templates/reader.html
   Impact : User gak bisa keluar fullscreen di HP
   Fix    : Floating exit button + double-tap + Esc

10.2 MEDIUM
────────────
🟡 Landing page "0 halaman" untuk ebook/comic
   File   : tools/dist_index.py
   Status : FIXED — _extract_pages pakai f.read() full
   
🟡 Duplikat folder `-2` setelah render ulang
   File   : importers/pdf_importer.py, comic_importer.py
   Status : FIXED — hapus folder lama sebelum render

10.3 LOW
─────────
🟢 scan_dist() baca HTML 3x per convo (title, msg_count, created_at)
   File   : tools/dist_index.py
   Fix    : 1x baca + regex multi-group

🟢 IntersectionObserver reader.html berat kalau 100+ halaman
   Fix    : Virtualization (render cuma yang keliatan)


================================================================================
11. REFERENSI FILE KRITIS
================================================================================

- CHECKPOINT.md                 : Aturan baku proyek (WAJIB baca dulu)
- main.py                       : CLI entry point
- tools/dist_index.py           : Index generator (chat + ebook + comic)
- templates/viewer.html         : Template chat viewer (~1500 baris)
- templates/reader.html         : Template ebook/comic reader (~1800 baris)
- importers/_reader_common.py   : Shared helper PDF & Comic
- importers/pdf_importer.py     : PDF importer logic
- importers/comic_importer.py   : Comic ZIP importer logic


================================================================================
END OF STATE.md — GhostWriter v2.6.9
================================================================================
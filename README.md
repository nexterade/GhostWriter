# 👻 GhostWriter+

> **AI Chat & Digital Content Archive** — Konversi arsip obrolan AI, ebook PDF, dan comic ZIP jadi web viewer interaktif bertema Midnight.

[![Version](https://img.shields.io/badge/version-v2.6.9--GW-blue)](https://github.com/nexterade/GhostWriter)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)

---

## ✨ Fitur

### 💬 Chat Archive
- **Multi-format Parser** — JSON, Markdown, DOCX
- **DeepSeek Live Backup** — via Bearer token (auto-refresh)
- **Incremental Backup** — skip obrolan tanpa update
- **Anti-Suspend Strategy** — human-like delay + jitter
- **Attachment Manifest** — list file yang perlu download manual
- **HTML Viewer** — search, copy, collapsible, KaTeX, syntax highlight
- **Export** — save as .md, .json, atau print → PDF

### 📖 Ebook Reader (PDF)
- **Image Mode** — render tiap halaman PDF jadi JPEG (cocok buat scan)
- **Metadata Extraction** — title, author, page count via pypdf
- **Auto-DPI 150** — balance antara kualitas & ukuran file
- **Progress Spinner** — feedback per step (analisis, render, save)
- **Auto-Cleanup** — hapus folder lama kalau slug sama

### 🎨 Comic Reader (ZIP)
- **Multi-format** — .jpg, .jpeg, .png, .webp, .gif, .bmp, .avif
- **Natural Sort** — 1, 2, 10 (bukan 1, 10, 2)
- **Skip Junk** — __MACOSX, ._*, .DS_Store, Thumbs.db
- **Flatten Nested** — semua gambar jadi 1 urutan
- **Keep Format Asli** — gak re-encode (preserve animasi GIF)

### 📚 Landing Page (Unified)
- **Tab Bar** — [📚 Semua] [💬 Chat] [📖 Ebook] [🎨 Comic]
- **Search Global** — filter by title (semua tipe)
- **Sort** — Terbaru, Judul A-Z, Pesan Terbanyak, Halaman Terbanyak, Ukuran
- **Date Grouping** — Hari Ini, Kemarin, 7 Hari, 30 Hari, Lebih Lama
- **Auto-Sync** — landing page update otomatis setelah render/import
- **Persist Tab** — tab terakhir ke-restore (localStorage)

### 🎨 Theme & UX
- **Dark/Light Mode** — toggle di semua viewer (localStorage)
- **CLI Midnight Theme** — spinner, progress bar, checklist
- **Loading Overlay** — progress bar animasi
- **Keyboard Shortcuts** — `?`, `/`, `j/k`, `Home/End`, `f`, `Esc`
- **Swipe Gesture** — mobile-friendly (buka/tutup sidebar)
- **Print-Friendly** — CSS @media print buat chat & reader

---

## 📦 Instalasi

### 1. Clone repo

    git clone https://github.com/nexterade/GhostWriter.git
    cd GhostWriter

### 2. Install Python dependencies

    pip install -r requirements.txt

**Isi `requirements.txt`:**
- `pypdf` — baca metadata PDF
- `pdf2image` — render PDF ke image
- `Pillow` — save image
- `python-docx` — parse .docx
- `requests` — HTTP request (DeepSeek backup)

### 3. Install Poppler (WAJIB buat PDF import)

Poppler (`pdftoppm`) dibutuhkan buat render PDF. Install sesuai OS:

**Termux (Android):**
    pkg install poppler

**Ubuntu / Debian:**
    sudo apt install poppler-utils

**macOS:**
    brew install poppler

**Windows:** download dari [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases), tambahin ke PATH.

---

## 🚀 Cara Pakai

### Mode Wizard Interaktif

    python3 main.py

Muncul menu 6 opsi:
- `[1]` Render backup lokal — Chat (.json / .md / .docx)
- `[2]` Sedot live dari DeepSeek — tarik obrolan dari akun
- `[3]` Import Ebook PDF — render PDF jadi reader HTML
- `[4]` Import Comic ZIP — extract image dari ZIP
- `[5]` Tutorial & Panduan — panduan lengkap + troubleshooting
- `[0]` Keluar

### Mode CLI Langsung

Render chat dari file backup:

    python3 main.py backup_chat.json
    python3 main.py backup_chat.json --all
    python3 main.py backup_chat.json --chat-index 0

### Taruh File di `inputs/`

Default folder input:
- `inputs/*.json` / `*.md` / `*.docx` — file backup chat
- `inputs/*.pdf` — ebook PDF
- `inputs/*.zip` — comic ZIP

Kalau folder `inputs/` gak ada, fallback ke root project.

### Sync Manual

Sync index (kalau nambah/hapus folder manual):

    python3 sync.py

Auto-sync **udah jalan** setiap render/import selesai.

### Prune Folder Stale

Hapus folder yang gak ada di backup source:

    python3 sync.py --clean
    python3 sync.py --clean --dry-run
    python3 sync.py --clean --yes

---

## 🖥️ Serve Output

**Wajib pakai HTTP server**, bukan `file://` (karena viewer fetch `index.json` via HTTP).

    python3 serve.py

Browser kebuka otomatis ke `http://localhost:8000/`.

**Opsi:**
    python3 serve.py --port 8080
    python3 serve.py --no-open

**Termux:** auto-detect & pakai `termux-open-url`.

---

## ⌨️ Keyboard Shortcuts

### Chat Viewer
| Key | Aksi |
|-----|------|
| `?` | Buka panel keyboard shortcuts |
| `/` | Fokus ke search box |
| `j` / `k` | Navigate pesan berikutnya / sebelumnya |
| `Home` | Scroll ke paling atas |
| `End` | Scroll ke paling bawah |
| `Esc` | Tutup sidebar / right rail / modal |

### Ebook / Comic Reader
| Key | Aksi |
|-----|------|
| `?` | Buka panel keyboard shortcuts |
| `f` | Toggle fullscreen |
| `j` / `k` | Halaman berikutnya / sebelumnya |
| `Home` | Scroll ke atas |
| `End` | Scroll ke bawah |
| `Esc` | Tutup sidebar / right rail / modal |

---

## 📁 Struktur

    GhostWriter+/
    ├── main.py                          # CLI entry point + wizard
    ├── serve.py                         # Local HTTP server
    ├── sync.py                          # Regenerate index + prune stale
    ├── exporter.py                      # HTMLExporter buat chat
    ├── requirements.txt                 # Python dependencies
    ├── README.md                        # ← file ini
    ├── CONTRIBUTING.md                  # Panduan kontribusi
    ├── Licence.md                       # MIT License
    ├── CHECKPOINT.md                    # Aturan baku proyek
    │
    ├── docs/                            # Dokumentasi dinamis
    │   ├── STATE.md                     # Snapshot status teknis
    │   └── BACKLOG.md                   # Checklist PR & fitur pending
    │
    ├── inputs/                          # Folder input default
    │   ├── *.json / *.md / *.docx       # Backup chat
    │   ├── *.pdf                        # Ebook PDF
    │   └── *.zip                        # Comic ZIP
    │
    ├── public/                          # Output HTML (di-serve)
    │   ├── index.html                   # Landing page (auto)
    │   ├── index.json                   # Metadata index (auto)
    │   ├── history/                     # Chat viewer output
    │   ├── readers/                     # Ebook output
    │   ├── comics/                      # Comic output
    │   └── vendor/                      # JS/CSS libraries
    │
    ├── templates/                       # Template HTML
    │   ├── viewer.html                  # Chat viewer
    │   └── reader.html                  # Ebook/comic reader
    │
    ├── parsers/                         # Parser input
    │   ├── json_parser.py
    │   ├── md_parser.py
    │   └── docx_parser.py
    │
    ├── importers/                       # Importer PDF & Comic
    │   ├── _reader_common.py            # Helper DRY
    │   ├── pdf_importer.py              # PDF → reader HTML
    │   └── comic_importer.py            # ZIP → reader HTML
    │
    ├── tools/                           # Utility modules
    │   ├── theme.py                     # Colors, theme
    │   ├── loading.py                   # Spinner, print helpers
    │   ├── checklist.py                 # Interactive checklist
    │   ├── dist_index.py                # Index generator
    │   └── deepseek_backup.py           # DeepSeek backup class
    │
    ├── backups/                         # Backup chat (.json)
    ├── attachments/                     # Attachment manual download
    └── .deepseek_token                  # Token cache (chmod 600)

---

## 🔧 Troubleshooting

### "fetch index.json failed"
Pastiin akses via `http://localhost:8000/`, **bukan** `file://`.

### Port 8000 udah dipake
Ganti port: `python3 serve.py --port 8080`
Atau kill proses lama: `lsof -ti:8000 | xargs kill`

### PDF gak ke-render / error poppler
Install Poppler dulu (lihat **Instalasi → Poppler**).

### Import PDF lambat
Normal — 100 halaman bisa 5-15 menit (tergantung device & DPI).

### Gambar di comic/ebook gak ke-render
1. Cek Console browser (F12) — biasanya path salah
2. Atau format gak didukung (.avif butuh browser modern)

### Token expired terus-terusan
GhostWriter auto-invalidate token cache. Login ulang pake token baru dari DevTools.

### Landing page gak ke-update
Jalankan manual: `python3 sync.py`

### Lampiran gak ke-render
Buka `attachments/PENDING.md` — ikutin langkahnya. DeepSeek blokir download otomatis.

---

## 💡 Tips & Trik

| Tips | Command |
|------|---------|
| Render 1 obrolan doang | `python3 main.py backup.json --chat-index 0` |
| Render semua obrolan | `python3 main.py backup.json --all` |
| Ganti port server | `python3 serve.py --port 8080` |
| Sync tanpa render ulang | `python3 sync.py` |
| Debug mode | `GW_DEBUG=1 python3 main.py` |
| Ganti delay backup | `GW_DELAY_MIN=2 GW_DELAY_MAX=4 python3 main.py` |
| Prune folder stale | `python3 sync.py --clean` |
| Preview prune | `python3 sync.py --clean --dry-run` |

---

## 📜 Lisensi

MIT — lihat [LICENSE](Licence.md).

---

## 🙏 Credits

Dibuat dengan 👻 oleh **[@nexterade](https://github.com/nexterade)**.

**Third-party libraries:**
- [Marked.js](https://marked.js.org/) — Markdown parser
- [highlight.js](https://highlightjs.org/) — Syntax highlighting
- [KaTeX](https://katex.org/) — Math rendering

**Python dependencies:**
- [pypdf](https://pypdf.readthedocs.io/) — PDF metadata
- [pdf2image](https://github.com/Belval/pdf2image) — PDF rendering
- [Pillow](https://python-pillow.org/) — Image processing
- [python-docx](https://python-docx.readthedocs.io/) — DOCX parsing
- [Poppler](https://poppler.freedesktop.org/) — PDF rendering backend

---

## ⚠️ Disclaimer

Tool ini untuk **arsip pribadi**. Gunakan dengan bijak. Jangan distribusi konten yang gak lu punya hak-nya.
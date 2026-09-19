# 👻 GhostWriter

> AI Chat Dump to Web Interface Engine — Konversi arsip obrolan AI jadi web interaktif bertema Midnight.

## ✨ Fitur

- Multi-format Parser (JSON, Markdown, DOCX)
- DeepSeek Live Backup via Bearer token
- Incremental Backup (state tracking)
- Anti-Suspend Strategy (human-like delay + jitter)
- CLI Midnight Theme (spinner, progress bar, checklist)
- HTML Viewer (search, copy, collapsible, KaTeX, syntax highlight)
- Landing Page (search, sort, group by date, dedup)
- Subfolder Output (dist/<slug>/index.html)

## 📦 Instalasi

Clone repo, masuk folder, lalu install dependencies:

    git clone https://github.com/USERNAME/GhostWriter.git
    cd GhostWriter
    pip install -r requirements.txt

## 🚀 Cara Pakai

Mode wizard interaktif:

    python3 main.py

Mode CLI langsung:

    python3 main.py backup_chat.json

Sync index (setelah hapus/tambah folder manual):

    python3 sync.py

## 🖥️ Serve Output

Wajib pakai HTTP server, bukan file://

    python3 -m http.server 8000

Buka: http://localhost:8000/dist/

## 📁 Struktur

    GhostWriter/
    ├── main.py
    ├── exporter.py
    ├── sync.py
    ├── parsers/
    ├── templates/
    ├── tools/
    ├── vendor/
    └── docs/

## 📜 Lisensi

MIT — lihat LICENSE.

## 🙏 Credits

Dibuat dengan 👻 oleh GhostWriter Dev Team.

- Marked.js — Markdown parser
- highlight.js — Syntax highlighting
- KaTeX — Math rendering

## ⚠️ Disclaimer

Tool ini untuk arsip pribadi. Gunakan dengan bijak.


## 🙏 Credits

Dibuat dengan 👻 oleh **[@nexterade](https://github.com/nexterade)**.

- [Marked.js](https://marked.js.org/) — Markdown parser
- [highlight.js](https://highlightjs.org/) — Syntax highlighting
- [KaTeX](https://katex.org/) — Math rendering
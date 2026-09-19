================================================================================
BACKLOG.md — GhostWriter+
Checklist PR & Fitur Pending
================================================================================
Versi    : v2.6.9-GW
Update   : 2026-09-20
Author   : @nexterade
Berlaku  : Seluruh komponen proyek GhostWriter+
📎 FILE TERKAIT:
   · CHECKPOINT.md   : aturan baku & filosofi proyek
   · docs/STATE.md   : snapshot status teknis
================================================================================

CARA PAKAI FILE INI:
────────────────────
1. Pilih batch yang mau dikerjain (misal Batch 7A).
2. Baca spec-nya, cek dependency.
3. Eksekusi. Update status [ ] → [x].
4. Kalau ada bug baru, tambahin di section "NEW ISSUES".

FORMAT STATUS:
  [ ]  = Belum dikerjain
  [/]  = In Progress
  [x]  = Selesai
  [-]  = Skip / Cancelled

================================================================================
BATCH 7A — templates/reader.html (TIER 1 + TIER 2)
================================================================================
File        : templates/reader.html
Dependency  : Batch 6 (dist_index.py) — SELESAI
Estimasi    : ~1800 baris
Test        : Manual, buka public/readers/<slug>/index.html
────────────────────────────────────────────────────────────────────────────

[ ] R1  AUTO-BOOKMARK + RESUME NOTIF
        Deskripsi : Simpan halaman terakhir dibaca per ebook/comic
        Status    : PARTIAL — sudah ada STORAGE_KEY_LAST_PAGE, tinggal notif
        Spec      :
          - Saat buka reader, cek localStorage `gw-last-page-<title>`
          - Kalau ada & > 1, tampil toast:
            "📍 Lanjut dari halaman 32? [Ya] [Mulai dari awal]"
          - Ya → scroll ke halaman 32 (smooth)
          - Mulai dari awal → scroll ke 0, hapus bookmark
          - Auto-dismiss setelah 8 detik
        Impact    : User gak perlu scroll manual tiap buka
        File      : templates/reader.html (JS DOMContentLoaded)

[ ] R2  TOGGLE HIDE NAVBAR
        Deskripsi : Sembunyiin header + stats bar biar fokus baca
        Spec      :
          - Tambah tombol "🙈" / "◀" di header (sebelah fullscreen)
          - Klik → body.classList.toggle("immersive")
          - CSS: body.immersive header, body.immersive .stats-bar
                 { display: none; }
          - Bonus: auto-hide on scroll (scroll down = hide, scroll up = show)
        Impact    : Fokus baca, layar lebih lega
        File      : templates/reader.html (HTML + CSS + JS)

[ ] R3  FULLSCREEN EXIT FIX (MOBILE) — 🔴 CRITICAL
        Deskripsi : Pas fullscreen, tombol exit hilang di mobile
        Root Cause: body.fullscreen header { display: none; }
        Spec      :
          - Tambah floating button "✕" di pojok kanan atas saat fullscreen
          - Detect double-tap → exit fullscreen
          - Esc keyboard → exit fullscreen (desktop)
          - Kombinasi: floating + double-tap + Esc
        Impact    : User bisa keluar fullscreen di HP
        File      : templates/reader.html (HTML + CSS + JS)

[ ] R4  ZOOM PINCH / DOUBLE-TAP
        Deskripsi : Zoom gambar (mobile)
        Spec      :
          - Pinch-to-zoom via CSS touch-action
          - Double-tap untuk zoom 2x
          - Pinch out untuk reset
          - Simpan zoom level per halaman (optional)
        Impact    : Baca detail gambar kecil
        File      : templates/reader.html (CSS + JS)

[ ] R5  READING PROGRESS BAR
        Deskripsi : Bar tipis di atas buat nunjukin progress baca
        Spec      :
          - Bar 3px di paling atas (position: fixed)
          - Width = scroll percentage
          - Warna accent, animate smooth
          - Optional: percent text di ujung kanan
        Impact    : User tau udah baca berapa persen
        File      : templates/reader.html (HTML + CSS + JS)

[ ] R6  PAGE SLIDER (SCRUBBER)
        Deskripsi : Slider di bawah buat lompat ke halaman
        Spec      :
          - Input range di footer
          - Value: current page
          - Drag → scroll ke halaman
          - Sync dengan scroll position
        Impact    : Navigasi cepat di comic/ebook tebal
        File      : templates/reader.html (HTML + CSS + JS)

────────────────────────────────────────────────────────────────────────────

[ ] R7  THUMBNAIL GRID NAVIGASI
        Deskripsi : Grid thumbnail di right rail (bukan cuma nomor)
        Spec      :
          - Right rail jadi grid 2-3 kolom
          - Tiap item: thumbnail halaman (image + nomor)
          - Lazy load thumbnail (IntersectionObserver)
          - Klik → goto page
        Impact    : Navigasi visual, bukan buta nomor
        File      : templates/reader.html (HTML + CSS + JS)
        Notes     : Perlu generate thumbnail terpisah ATAU pakai image asli
                    dengan ukuran kecil (CSS aspect-ratio)

[ ] R8  READING STATS
        Deskripsi : Total waktu baca, halaman/hari, streak
        Spec      :
          - Track waktu mulai & selesai baca (localStorage)
          - Tampil di sidebar:
            "Total baca: 2j 34m"
            "Halaman: 145 / 145 (100%)"
            "Streak: 3 hari"
          - Data per-judul, disimpan di localStorage
        Impact    : Gamifikasi baca, motivasi
        File      : templates/reader.html (JS + sidebar HTML)

[ ] R9  NIGHT MODE AUTO
        Deskripsi : Otomatis ganti theme sesuai jam
        Spec      :
          - Jam 18:00-06:00 → dark
          - Jam 06:00-18:00 → light
          - Override manual tetap ada (localStorage)
          - Cek tiap 30 menit (setInterval)
        Impact    : Nyaman baca malam
        File      : templates/reader.html (JS)

[ ] R10 BRIGHTNESS CONTROL
        Deskripsi : Slider buat adjust brightness gambar
        Spec      :
          - Slider di sidebar / floating button
          - Value: 50% - 150%
          - Apply via CSS filter: brightness(X%)
          - Simpan setting di localStorage
        Impact    : Baca nyaman di cahaya berbeda
        File      : templates/reader.html (HTML + CSS + JS)

[ ] R11 FIT MODE TOGGLE
        Deskripsi : Fit width / fit height / original / cover
        Spec      :
          - Tombol di header (icon berubah per mode)
          - Cycle: fit-width → fit-height → original → cover
          - Apply via CSS class di .reader-page img
          - Simpan preferensi di localStorage
        Impact    : Kontrol tampilan gambar
        File      : templates/reader.html (HTML + CSS + JS)

[ ] R12 CONTINUOUS VS PAGED MODE
        Deskripsi : Baca scroll atau per-halaman
        Spec      :
          - Toggle di header
          - Continuous: scroll (default)
          - Paged: tampil 1 halaman, tombol next/prev
          - Keyboard: j/k atau arrow keys
          - Swipe: kiri/kanan untuk pindah halaman
        Impact    : Mode baca berbeda buat tipe konten berbeda
        File      : templates/reader.html (HTML + CSS + JS)
        Notes     : Butuh refactor struktur DOM

[ ] R13 TWO-PAGE VIEW (LANDSCAPE)
        Deskripsi : Tampil 2 halaman berdampingan di landscape
        Spec      :
          - Auto-detect orientation (matchMedia landscape)
          - Kalau landscape & lebar > 768px → 2 halaman side-by-side
          - Grid 2 kolom, gap 8px
          - Keyboard: j/k pindah 2 halaman
        Impact    : Baca landscape lebih efisien
        File      : templates/reader.html (CSS + JS)
        Notes     : Fitur manga/komik klasik

[ ] R14 RTL MODE (MANGA)
        Deskripsi : Baca kanan ke kiri (manga Jepang)
        Spec      :
          - Toggle RTL di header
          - direction: rtl di .reader-container
          - Keyboard: j = prev (RTL), k = next (RTL)
          - Swipe: kanan = next (RTL)
          - Simpan preferensi di localStorage
        Impact    : Pengalaman baca manga authentic
        File      : templates/reader.html (CSS + JS)

[ ] R15 WEBTOON MODE
        Deskripsi : Baca comic vertikal (gap 0, full-width)
        Spec      :
          - Toggle di header
          - CSS: .reader-page { gap: 0; max-width: 100%; border-radius: 0; }
          - Padding container 0
          - Image full-width tanpa border
          - Cocok buat webtoon/manhwa
        Impact    : Baca webtoon seamless
        File      : templates/reader.html (CSS + JS)
        Notes     : Auto-detect: kalau aspect ratio rata-rata > 3:1,
                    suggest webtoon mode


================================================================================
BATCH 7B — templates/viewer.html (TIER 1 + TIER 2)
================================================================================
File        : templates/viewer.html
Dependency  : Batch 6 (dist_index.py) — SELESAI
Estimasi    : ~1500 baris
Test        : Manual, buka public/history/<id>/index.html
────────────────────────────────────────────────────────────────────────────

[ ] V1  AUTO-SCROLL RESUME POLISH
        Deskripsi : Lanjut dari posisi scroll terakhir
        Status    : PARTIAL — sudah ada STORAGE_KEY_SCROLL
        Spec      :
          - Polish: tampil toast "📍 Lanjut dari pesan #42?"
          - Tombol "Mulai dari atas"
          - Auto-dismiss setelah 5 detik
        Impact    : User gak perlu scroll manual
        File      : templates/viewer.html (JS)

[ ] V2  EXPORT CHAT → MARKDOWN
        Deskripsi : Download seluruh chat jadi .md
        Spec      :
          - Tombol di header menu (⋮)
          - Generate markdown dari data-raw semua bubble
          - Format: # Title\n\n## User\n\ncontent\n\n## AI\n\n...
          - Filename: <slug>-<timestamp>.md
          - Download via Blob + anchor
        Impact    : User bisa save chat ke .md
        File      : templates/viewer.html (JS)

[ ] V3  EXPORT CHAT → PDF POLISH
        Deskripsi : Print / Save as PDF (sudah ada via @media print)
        Status    : DONE — polish minor
        Spec      :
          - Tambah margin di print CSS
          - Sembunyiin scrollbar di print
          - Nomor halaman
        Impact    : Print rapi
        File      : templates/viewer.html (CSS @media print)
        Notes     : Sudah ada, cek kualitas

[ ] V4  EXPORT CHAT → JSON
        Deskripsi : Backup chat struktur
        Spec      :
          - Tombol di header menu (⋮)
          - Generate JSON dari data-raw
          - Format: { title, messages: [{ role, content, timestamp }] }
          - Filename: <slug>-<timestamp>.json
        Impact    : User bisa re-import
        File      : templates/viewer.html (JS)

[ ] V5  SEARCH REGEX SUPPORT
        Deskripsi : Support regex di search
        Spec      :
          - Detect kalau query dimulai & diakhiri "/" → regex
          - /pattern/flags
          - Fallback ke plain text kalau regex invalid
          - Warning kalau regex invalid
        Impact    : Power user bisa search pattern
        File      : templates/viewer.html (JS doSearch)

[ ] V6  COPY ALL FROM AI
        Deskripsi : Copy 1 pesan AI langsung
        Status    : DONE — per pesan udah ada
        Notes     : Skip, udah ada copy per pesan

────────────────────────────────────────────────────────────────────────────

[ ] V8  COLLAPSE/EXPAND SEMUA
        Deskripsi : Tombol collapse semua bubble panjang
        Spec      :
          - Tombol di header: "Sembunyikan semua" / "Tampilkan semua"
          - Toggle class .expanded di semua .bubble.collapsible
        Impact    : Navigasi cepat di chat panjang
        File      : templates/viewer.html (HTML + JS)

[ ] V9  FILTER BY ROLE
        Deskripsi : Tampilin cuma user / cuma AI
        Spec      :
          - Tombol filter di header: [Semua] [User] [AI]
          - Filter via data-role
        Impact    : Fokus baca user prompt atau AI response
        File      : templates/viewer.html (HTML + CSS + JS)

[ ] V10 CHAT STATS LENGKAP
        Deskripsi : Total kata, char, token per role
        Spec      :
          - Stats bar tambah:
            "👤 User: 234 kata, 1234 char, ~308 token"
            "🤖 AI: 1234 kata, 5678 char, ~1420 token"
          - Hitung dari data-raw
        Impact    : Insight chat
        File      : templates/viewer.html (JS computeStats)

[ ] V11 READING TIME ESTIMATE
        Deskripsi : Estimasi waktu baca
        Spec      :
          - Total kata / 200 wpm
          - Tampil di stats bar: "⏱️ Estimasi baca: 5 menit"
        Impact    : User tau durasi baca
        File      : templates/viewer.html (JS)

[ ] V12 HIGHLIGHT / BOOKMARK PESAN
        Deskripsi : Tandai pesan penting
        Status    : SKIP — butuh backend (localStorage OK)
        Notes     : Bisa diimplement pakai localStorage key
                    `gw-highlights-<chat_id>` berisi array msg_index

[ ] V13 NOTE PER PESAN
        Deskripsi : Catatan di pesan tertentu
        Status    : SKIP — butuh UI editor + storage
        Notes     : Bisa diimplement pakai localStorage
                    `gw-notes-<chat_id>` berisi { msg_index: "note" }


================================================================================
BATCH 7C — tools/dist_index.py (TIER 1 + TIER 2 GLOBAL)
================================================================================
File        : tools/dist_index.py
Dependency  : Batch 6 — SELESAI
Estimasi    : ~1000 baris
Test        : Manual, buka public/index.html
────────────────────────────────────────────────────────────────────────────

[ ] G2  KEYBOARD NAV DI LANDING
        Deskripsi : j/k buat navigate, Enter buat buka
        Spec      :
          - Detect fokus di search input → skip
          - j = next item (highlight)
          - k = prev item
          - Enter = buka item yang di-highlight
          - Esc = clear highlight
          - Visual: outline accent di item terpilih
        Impact    : Navigasi cepat tanpa mouse
        File      : tools/dist_index.py (JS)

[ ] G3  RECENT ACTIVITY SECTION
        Deskripsi : Section "baru dibaca" / "baru di-import"
        Spec      :
          - localStorage `gw-recent` = [{ id, timestamp }]
          - Update tiap buka item (viewer / reader)
          - Section "Recent" di atas date-group (max 5)
        Impact    : Quick access ke item terakhir
        File      : tools/dist_index.py (HTML + JS)
        Notes     : Butuh update di viewer.html & reader.html
                    buat nulis gw-recent

[ ] G4  FAVORITES / STARRED
        Deskripsi : Tandai item favorit
        Spec      :
          - localStorage `gw-favorites` = [id1, id2, ...]
          - Tombol ⭐ di setiap item
          - Section "Favorit" di atas
          - Filter: tab "⭐ Favorit"
        Impact    : Bookmark manual item favorit
        File      : tools/dist_index.py (HTML + CSS + JS)
        Notes     : Tombol ⭐ muncul di hover

[ ] G5  GRID VS LIST VIEW
        Deskripsi : Toggle tampilan grid atau list
        Spec      :
          - Tombol toggle di controls (icon list/grid)
          - Grid: 2-3 kolom kartu
          - List: 1 kolom (default)
          - Simpan preferensi di localStorage
        Impact    : User bisa pilih tampilan
        File      : tools/dist_index.py (CSS + JS)

[ ] G6  DARK/LIGHT AUTO
        Deskripsi : Theme auto sesuai sistem
        Spec      :
          - Detect prefers-color-scheme
          - Kalau belum ada override manual → pakai sistem
          - Override manual tetap ada
        Impact    : Nyaman sesuai preferensi OS
        File      : tools/dist_index.py + viewer.html + reader.html

[ ] G8  FILTER BY DATE RANGE
        Deskripsi : Filter item by date
        Spec      :
          - Dropdown: [Semua] [Hari Ini] [7 Hari] [30 Hari] [Custom]
          - Filter via data-mtime
        Impact    : Cari konten lama
        File      : tools/dist_index.py (HTML + JS)

[ ] G9  STATS DASHBOARD
        Deskripsi : Total konten, size, dll
        Spec      :
          - Section di atas: "Total: 27 item, 45 MB"
          - Per tipe: chat (24), ebook (2), comic (1)
          - Update tiap sync
        Impact    : Overview konten
        File      : tools/dist_index.py (HTML + JS)

────────────────────────────────────────────────────────────────────────────

[ ] 6.2 OPTIMIZE scan_dist() — 1x BACA HTML
        Deskripsi : Sekarang baca HTML 3x per convo
        Spec      :
          - Baca content 1x, pakai regex multi-group:
            r'<title>([^<]+)</title>.*?id="header-subtitle"[^>]*>([^<]+)<.*?class="meta-time">([^<]+)<'
          - Count message-row via len(re.findall)
        Impact    : 3x lebih cepat
        File      : tools/dist_index.py


================================================================================
BATCH 7D — tools/prompt.py (REFACTOR)
================================================================================
File        : tools/prompt.py (BARU)
Dependency  : Tidak ada
Estimasi    : ~100 baris
Test        : Import dari main.py & importers/*.py
────────────────────────────────────────────────────────────────────────────

[ ] 2.1 REFACTOR _prompt & _prompt_yes_no
        Deskripsi : Pindahin dari main.py ke tools/prompt.py
        Alasan    : Hilangkan circular import main.py ↔ importers
        Spec      :
          - Pindah fungsi `_prompt`, `_prompt_yes_no`, `_is_cancel`
          - Update import di main.py:
            from tools.prompt import prompt, prompt_yes_no
          - Update import di importers/pdf_importer.py:
            from tools.prompt import prompt, prompt_yes_no
          - Update import di importers/comic_importer.py: same
        Impact    : Kode lebih bersih, gak ada circular import
        File      : tools/prompt.py (baru), main.py, importers/*.py


================================================================================
BATCH 7E — main.py (AUTO-SYNC + REFACTOR)
================================================================================
File        : main.py
Dependency  : Batch 7D (tools/prompt.py)
Estimasi    : ~1000 baris
Test        : python3 main.py → test semua menu
────────────────────────────────────────────────────────────────────────────

[ ] G1  AUTO-SYNC SETELAH RENDER
        Deskripsi : Auto-jalanin sync.py setelah render/import
        Status    : PARTIAL — perlu finalisasi
        Spec      :
          - Helper `_auto_sync()` di main.py
          - Pakai subprocess.run([sys.executable, "sync.py"])
          - Capture output, suppress (kecuali GW_DEBUG=1)
          - Timeout 30 detik
          - Panggil di:
            · _do_render() — setelah render chat
            · handle_pdf_import() — setelah import ebook
            · handle_comic_import() — setelah import comic
          - Kalau gagal → warning, handler return tetap True
        Impact    : Landing page selalu up-to-date
        File      : main.py (helper + panggilan)

[ ] 2.2 PINDAHIN _print_post_render_hint()
        Deskripsi : Pindah dari main.py ke tools/loading.py
        Alasan    : Reusable, biar main.py lebih ramping
        Spec      :
          - Pindah fungsi `_print_post_render_hint()` (rename: print_post_render_hint)
          - Update import di main.py
        File      : tools/loading.py, main.py

[ ] 2.3 RAPIHIN import argparse
        Deskripsi : Cek apakah argparse masih dipakai
        Spec      :
          - CLI mode di main.py pakai argparse
          - Kalau masih dipakai → keep
          - Kalau gak dipakai → hapus
        File      : main.py


================================================================================
BATCH 7F — DOKUMENTASI
================================================================================
File        : README.md, CONTRIBUTING.md, CHECKPOINT.md
Dependency  : Batch 7A-7E (biar akurat)
Estimasi    : ~500 baris
Test        : Baca & cek akurasi
────────────────────────────────────────────────────────────────────────────

[ ] 4.1 UPDATE README.md
        Deskripsi : Tambah fitur PDF & Comic
        Spec      :
          - Section "Fitur" — tambah PDF import + Comic import
          - Section "Install" — tambah poppler dependency
          - Section "Cara Pakai" — tambah langkah PDF & Comic
          - Screenshot placeholder
        File      : README.md

[ ] 4.2 UPDATE CONTRIBUTING.md
        Deskripsi : Panduan importers
        Spec      :
          - Section "Struktur Folder" — update
          - Section "Cara Nambah Format" — panduan bikin importer baru
          - Section "Testing" — panduan test PDF & Comic
        File      : CONTRIBUTING.md

[ ] 4.3 UPDATE CHECKPOINT.md
        Deskripsi : Aturan importers & reader
        Spec      :
          - Section "Filosofi" — tambah multi-tipe konten
          - Section "Aturan" — tambah aturan importer
          - Update versi
        File      : CHECKPOINT.md
        Notes     : CHECKPOINT.md tetap di root, bukan docs/


================================================================================
NEW ISSUES (BUG / EDGE CASE)
================================================================================
Update tiap ketemu bug baru. Format:
  [TANGGAL] [SEVERITY] Deskripsi — Status
────────────────────────────────────────────────────────────────────────────

[2026-09-20] [CRITICAL] Fullscreen exit button hilang di mobile
            → Lihat BATCH 7A R3

[2026-09-20] [MEDIUM] Landing page "0 halaman" untuk ebook/comic
            → FIXED — _extract_pages pakai f.read() full

[2026-09-20] [MEDIUM] Duplikat folder `-2` setelah render ulang
            → FIXED — hapus folder lama sebelum render

[2026-09-20] [LOW] scan_dist() baca HTML 3x per convo
            → Lihat BATCH 7C 6.2

[2026-09-20] [LOW] IntersectionObserver reader.html berat kalau 100+ halaman
            → Perlu virtualisasi (BACKLOG, prioritas rendah)


================================================================================
CATATAN PENTING UNTUK AI / CONTRIBUTOR
================================================================================

1. BACA CHECKPOINT.md DULU sebelum eksekusi apapun.

2. IKUTI ATURAN BATCH BY FILE:
   - Kumpulkan task yang nyentuh file sama
   - Eksekusi per batch, jangan bolak-balik

3. FORMAT PENGIRIMAN:
   - File .md: fenced code block tag "text" atau tanpa tag
   - File .py: fenced code block tag "python"
   - File .html: fenced code block tag "html"
   - Multi-file: SATU PER SATU, tunggu konfirmasi user

4. DIFF VS FULL CODE:
   - File kecil (<1500 baris) → FULL CODE
   - File besar (>1500 baris) → BISA DIFF, sesuai permintaan user

5. TESTING:
   - Setiap batch SELESAI harus di-test dulu
   - Baru lanjut ke batch berikutnya
   - Kalau ada bug, catat di "NEW ISSUES"

6. FOKUS & SCOPE:
   - Tier 3 fitur SKIP dulu (PWA, OCR, annotation, multi-user)
   - Fokus ke Tier 1 & Tier 2
   - Setelah stabil, baru pertimbangkan Tier 3

7. KALAU RAGU:
   - Tanya user dulu, JANGAN asumsi
   - Kalau format input belum jelas, minta contoh
   - Kalau ada bug, telusuri log tanpa ngeles


================================================================================
END OF BACKLOG.md — GhostWriter v2.6.9
================================================================================
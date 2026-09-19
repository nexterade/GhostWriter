#!/usr/bin/env python3
"""
GhostWriter — Sync Index

Regenerate public/index.html + public/index.json dari folder yang ada di
public/history/.

Usage:
    python3 sync.py                        # Sync biasa
    python3 sync.py --clean                # Sync + prune folder stale (dengan konfirmasi)
    python3 sync.py --clean --dry-run      # Preview folder yang bakal dihapus
    python3 sync.py --clean --yes          # Prune tanpa konfirmasi (buat script)
    python3 sync.py --clean --keep ID1,ID2 # Manual: keep ID1 & ID2 aja
"""
import sys
import os
import json
import glob
import argparse
import shutil
from typing import Set, List, Dict

from tools.theme import get_theme, C
from tools.dist_index import write_all


PUBLIC_DIR = "public"
HISTORY_SUBDIR = "history"
BACKUP_DIR = "backups"


# ============================================================
# SOURCE OF TRUTH — DETEKSI CONVO YANG MASIH VALID
# ============================================================

def _get_valid_convo_ids_from_backups() -> Set[str]:
    """
    Scan semua file backup di backups/*.json, extract convo ID dari
    field `id` atau `inserted_at` (fallback).

    Return: set of convo ID (string).
    """
    valid_ids: Set[str] = set()

    if not os.path.isdir(BACKUP_DIR):
        return valid_ids

    backup_files = glob.glob(os.path.join(BACKUP_DIR, "*.json"))
    if not backup_files:
        return valid_ids

    for bf in backup_files:
        try:
            with open(bf, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        # Backup bisa berbentuk: 1 dict convo ATAU list of convo
        items = data if isinstance(data, list) else [data]

        for item in items:
            if not isinstance(item, dict):
                continue

            # Priority 1: field "id" langsung
            convo_id = item.get("id")
            if convo_id:
                # Konversi ke string (buat konsistensi)
                valid_ids.add(str(convo_id))
                continue

            # Priority 2: fallback dari inserted_at (sesuai _generate_convo_id di main.py)
            inserted_at = item.get("inserted_at")
            if inserted_at:
                try:
                    ts = int(float(inserted_at))
                    if ts > 0:
                        valid_ids.add(str(ts))
                except (ValueError, TypeError):
                    pass

    return valid_ids


def _get_existing_convo_ids() -> Set[str]:
    """Scan folder di public/history/ — return set of convo ID."""
    history_dir = os.path.join(PUBLIC_DIR, HISTORY_SUBDIR)
    if not os.path.isdir(history_dir):
        return set()

    existing = set()
    try:
        for entry in os.listdir(history_dir):
            entry_path = os.path.join(history_dir, entry)
            if os.path.isdir(entry_path):
                # Cek ada index.html di dalamnya
                if os.path.isfile(os.path.join(entry_path, "index.html")):
                    existing.add(entry)
    except OSError:
        pass

    return existing


# ============================================================
# PR-33: PRUNE STALE
# ============================================================

def _find_stale_folders(valid_ids: Set[str]) -> List[str]:
    """
    Cari folder di public/history/ yang GAK ADA di valid_ids.

    Return: list folder name (convo ID) yang stale.
    """
    existing = _get_existing_convo_ids()
    stale = existing - valid_ids
    return sorted(stale)


def _format_size(size_bytes: int) -> str:
    """Format size human-readable."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _get_folder_size(folder_path: str) -> int:
    """Hitung total size folder (recursive)."""
    total = 0
    try:
        for dirpath, _, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
    except OSError:
        pass
    return total


def _prune_stale(stale_ids: List[str], dry_run: bool = False) -> tuple:
    """
    Hapus folder stale di public/history/.

    Return: (deleted_count, total_freed_bytes)
    """
    history_dir = os.path.join(PUBLIC_DIR, HISTORY_SUBDIR)
    deleted = 0
    freed = 0

    for convo_id in stale_ids:
        folder_path = os.path.join(history_dir, convo_id)
        if not os.path.isdir(folder_path):
            continue

        size = _get_folder_size(folder_path)

        if dry_run:
            deleted += 1
            freed += size
            continue

        try:
            shutil.rmtree(folder_path)
            deleted += 1
            freed += size
        except OSError:
            pass

    return deleted, freed


# ============================================================
# SYNC COMMAND
# ============================================================

def cmd_sync(clean: bool = False, dry_run: bool = False, auto_yes: bool = False,
             manual_keep: str = "") -> int:
    """Jalankan sync + optional prune."""
    t = get_theme()

    # === STEP 1: PRUNE (kalo diminta) ===
    if clean:
        print(t.bold_accent("🧹  Prune Stale — Cek folder yang gak kepake"))
        print()

        # Tentukan valid IDs
        if manual_keep:
            valid_ids = set(x.strip() for x in manual_keep.split(",") if x.strip())
            print(t.gray(f"  Mode manual: keep {len(valid_ids)} ID"))
        else:
            valid_ids = _get_valid_convo_ids_from_backups()
            if valid_ids:
                print(t.gray(f"  Sumber: {BACKUP_DIR}/ — {len(valid_ids)} convo valid"))
            else:
                print(t.yellow(f"  ⚠ Gak ada file backup di {BACKUP_DIR}/"))
                print(t.gray("    Kalo mau prune manual, pake: --keep ID1,ID2"))
                print()
                print(t.gray("  Skip prune (gak ada source of truth)."))
                print()
                valid_ids = None

        if valid_ids is not None:
            stale = _find_stale_folders(valid_ids)

            if not stale:
                print(t.green("  ✓ Gak ada folder stale. Semua bersih."))
                print()
            else:
                # Preview
                total_size = 0
                print(t.gray(f"  Ditemukan {len(stale)} folder stale:"))
                print()

                for convo_id in stale:
                    folder_path = os.path.join(PUBLIC_DIR, HISTORY_SUBDIR, convo_id)
                    size = _get_folder_size(folder_path)
                    total_size += size

                    if t.enabled:
                        print(f"    {C.RED}✗{C.RESET} {C.WHITE}{convo_id}{C.RESET}  {C.GRAY}({_format_size(size)}){C.RESET}")
                    else:
                        print(f"    ✗ {convo_id}  ({_format_size(size)})")

                print()
                print(t.gray(f"  Total: {_format_size(total_size)} bakal di-freed"))
                print()

                # Dry-run mode
                if dry_run:
                    print(t.yellow("  🔍 DRY-RUN — gak ada file yang ke-hapus"))
                    print(t.gray("    Hapus '--dry-run' buat eksekusi."))
                    print()
                else:
                    # Konfirmasi
                    if not auto_yes:
                        try:
                            if t.enabled:
                                raw = input(
                                    f"  {C.YELLOW}Hapus {len(stale)} folder ini?{C.RESET} "
                                    f"{C.GRAY}[y/N]{C.RESET}: "
                                ).strip().lower()
                            else:
                                raw = input(f"  Hapus {len(stale)} folder ini? [y/N]: ").strip().lower()
                        except (KeyboardInterrupt, EOFError):
                            print()
                            print(t.gray("  Dibatalkan."))
                            return 1

                        if raw not in ("y", "yes", "ya"):
                            print(t.gray("  Dibatalkan. Gak ada yang ke-hapus."))
                            print()
                            return 1

                    # Eksekusi
                    deleted, freed = _prune_stale(stale, dry_run=False)
                    print(t.green(f"  ✓ {deleted} folder ke-hapus"))
                    print(t.gray(f"    Freed: {_format_size(freed)}"))
                    print()

    # === STEP 2: SYNC INDEX ===
    print(t.bold_accent("📇  Sync Index — Regenerate index.json + index.html"))
    print()

    try:
        json_path, html_path = write_all()
    except Exception as e:
        print(t.red(f"  ✗ Error: {e}"))
        return 1

    print(t.green(f"  ✓ JSON: {json_path}"))
    print(t.green(f"  ✓ HTML: {html_path}"))
    print()

    # Info URL
    print(t.gray("  Buka: http://localhost:8000/"))
    print()

    return 0


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        prog="sync.py",
        description="GhostWriter — Sync index + optional prune stale folders.",
    )
    parser.add_argument("--clean", action="store_true",
                        help="Prune folder stale di public/history/ yang gak ada di source backup")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview folder yang bakal di-hapus (gak eksekusi)")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Skip konfirmasi (buat script/CI)")
    parser.add_argument("--keep", type=str, default="",
                        help="Manual: comma-separated ID yang mau di-keep (kalo gak ada backup)")
    args = parser.parse_args()

    return cmd_sync(
        clean=args.clean,
        dry_run=args.dry_run,
        auto_yes=args.yes,
        manual_keep=args.keep,
    )


if __name__ == "__main__":
    sys.exit(main())
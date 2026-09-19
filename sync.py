#!/usr/bin/env python3
"""
GhostWriter — Sync Index

Regenerate dist/index.html + dist/index.json dari file yang ada di dist/.
Jalankan setiap habis hapus/tambah folder convo manual.

Usage:
    python3 sync.py
"""
import sys

from tools.theme import get_theme
from tools.dist_index import write_all


def main():
    t = get_theme()
    print(t.bold_accent("👻 GhostWriter — Sync Index"))
    print()

    try:
        json_path, html_path = write_all()
    except Exception as e:
        print(t.red(f"  ✗ Error: {e}"))
        sys.exit(1)

    print(t.green(f"  ✓ JSON: {json_path}"))
    print(t.green(f"  ✓ HTML: {html_path}"))
    print()
    print(t.gray("  Buka: http://localhost:8000/dist/"))


if __name__ == "__main__":
    main()
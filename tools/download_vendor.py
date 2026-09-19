import os
import urllib.request

VENDOR_DIR = "vendor"
ASSETS = {
    "marked.min.js": "https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js",
    "highlight.min.js": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js",
    "highlight-tokyo-night-dark.min.css": "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/tokyo-night-dark.min.css",
    "katex.min.js": "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js",
    "katex.min.css": "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css",
    "katex-auto-render.min.js": "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js",
}


def download_all():
    os.makedirs(VENDOR_DIR, exist_ok=True)
    for filename, url in ASSETS.items():
        target = os.path.join(VENDOR_DIR, filename)
        if os.path.exists(target) and os.path.getsize(target) > 0:
            print(f"  [✓] Sudah ada: {filename}")
            continue
        print(f"  [⬇️] Downloading: {filename}")
        try:
            urllib.request.urlretrieve(url, target)
            size = os.path.getsize(target)
            print(f"      → {size} bytes")
        except Exception as e:
            print(f"  [X] Gagal download {filename}: {e}")


if __name__ == "__main__":
    download_all()
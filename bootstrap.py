"""Unpack the shipped demo data (data.zip) into data/ when it is missing.

A fresh clone contains data.zip but not data/. Entry points call ensure_data()
so that `python server.py` works without a manual unzip step.
"""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / 'data.zip'
MARKER = ROOT / 'data' / 'catalog.json'


def ensure_data():
    """Extract data.zip once. Returns True if data/ is ready, False otherwise."""
    if MARKER.exists():
        return True
    if not ARCHIVE.exists():
        return False
    with zipfile.ZipFile(ARCHIVE) as z:
        for name in z.namelist():
            target = (ROOT / name).resolve()
            if not target.is_relative_to(ROOT):
                raise ValueError('Archive member escapes repository: ' + name)
        z.extractall(ROOT)
    return MARKER.exists()


if __name__ == '__main__':
    print('data/ ready' if ensure_data() else 'data/ unavailable: run python build_demo.py')

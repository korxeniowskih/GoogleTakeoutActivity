"""Szybki podgląd struktury plików Google Takeout."""
import re
import html
from pathlib import Path

TAKEOUT = Path(__file__).parent / "Takeout"

for html_file in sorted((TAKEOUT / "Moja aktywność").glob("*/Moja_aktywność.html")):
    text = html_file.read_text(encoding="utf-8", errors="replace")
    cells = len(re.findall(r'class="content-cell', text))
    size_mb = html_file.stat().st_size / 1_048_576
    print(f"{html_file.parent.name:30} {cells:>8} wpisów  {size_mb:>6.1f} MB")

print("\n--- Przykładowe wpisy (Android) ---")
android = TAKEOUT / "Moja aktywność" / "Android" / "Moja_aktywność.html"
text = android.read_text(encoding="utf-8", errors="replace")
for m in re.finditer(
    r'<div class="content-cell[^"]*">(.*?)</div>\s*<div class="content-cell[^"]*">(.*?)</div>',
    text[:200_000],
    re.DOTALL,
):
    for g in m.groups():
        clean = re.sub(r"<[^>]+>", " ", g)
        clean = html.unescape(re.sub(r"\s+", " ", clean).strip())
        print(clean[:250])
    print("---")
    break

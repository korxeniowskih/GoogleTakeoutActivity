"""Uruchom pełną analizę: parsowanie + wizualizacja."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def run(script: str) -> None:
    print(f"\n{'=' * 60}\n>>> {script}\n{'=' * 60}")
    result = subprocess.run([sys.executable, str(ROOT / script)], check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)


if __name__ == "__main__":
    run("parse_takeout.py")
    run("visualize_takeout.py")
    print("\nGotowe. Otwórz output/raport.html w przeglądarce.")

"""
Wizualizacja danych z parse_takeout.py — wykresy PNG w output/charts/.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

OUTPUT_DIR = Path(__file__).parent / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"

# Polskie etykiety na wykresach
plt.rcParams["font.family"] = "Segoe UI"
plt.rcParams["axes.unicode_minus"] = False


def load_data() -> tuple[pd.DataFrame, dict]:
    csv_path = OUTPUT_DIR / "aktywnosc.csv"
    summary_path = OUTPUT_DIR / "podsumowanie.json"
    if not csv_path.exists():
        raise FileNotFoundError(
            "Brak output/aktywnosc.csv — uruchom najpierw: python parse_takeout.py"
        )
    df = pd.read_csv(csv_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return df, summary


def chart_top_services(df: pd.DataFrame) -> None:
    top = df["service"].value_counts().head(12)
    fig, ax = plt.subplots(figsize=(10, 6))
    top.sort_values().plot(kind="barh", ax=ax, color="#4285F4")
    ax.set_title("Top 12 usług Google — liczba zarejestrowanych zdarzeń")
    ax.set_xlabel("Liczba wpisów")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "01_top_uslugi.png", dpi=150)
    plt.close(fig)


def chart_mobile_vs_desktop(df: pd.DataFrame) -> None:
    mobile = {"Android", "Chrome", "Mapy", "YouTube", "Sklep Google Play", "Asystent"}
    df = df.copy()
    df["kanal"] = df["service"].apply(
        lambda s: "Mobilne / aplikacje" if s in mobile else "Inne usługi Google"
    )
    counts = df["kanal"].value_counts()
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(
        counts.values,
        labels=counts.index,
        autopct="%1.1f%%",
        colors=["#34A853", "#FBBC05"],
        startangle=90,
    )
    ax.set_title("Udział aktywności: mobilne vs pozostałe")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "02_mobilne_vs_inne.png", dpi=150)
    plt.close(fig)


def chart_activity_by_year(summary: dict) -> None:
    years = summary.get("activity_by_year", {})
    if not years:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    xs = list(years.keys())
    ys = list(years.values())
    ax.bar(xs, ys, color="#EA4335")
    ax.set_title("Aktywność w czasie (wg roku)")
    ax.set_xlabel("Rok")
    ax.set_ylabel("Liczba zdarzeń")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "03_aktywnosc_rok.png", dpi=150)
    plt.close(fig)


def chart_activity_by_hour(summary: dict) -> None:
    hours = summary.get("activity_by_hour", {})
    if not hours:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    xs = [int(k) for k in hours]
    ys = [hours[str(k)] for k in xs]
    ax.plot(xs, ys, marker="o", color="#4285F4")
    ax.set_xticks(range(0, 24, 2))
    ax.set_title("Rozkład aktywności wg godziny dnia")
    ax.set_xlabel("Godzina")
    ax.set_ylabel("Liczba zdarzeń")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "04_godziny_dnia.png", dpi=150)
    plt.close(fig)


def chart_top_actions(df: pd.DataFrame) -> None:
    top = df["action"].value_counts().head(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    top.sort_values().plot(kind="barh", ax=ax, color="#9334E6")
    ax.set_title("Najczęstsze typy zarejestrowanych czynności")
    ax.set_xlabel("Liczba wpisów")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "05_typy_czynnosci.png", dpi=150)
    plt.close(fig)


def chart_android_timeline(df: pd.DataFrame) -> None:
    android = df[df["service"] == "Android"].copy()
    android = android.dropna(subset=["datetime_iso"])
    if android.empty:
        return
    android["date"] = pd.to_datetime(android["datetime_iso"]).dt.date
    daily = android.groupby("date").size()
    fig, ax = plt.subplots(figsize=(12, 4))
    daily.plot(ax=ax, color="#34A853", linewidth=1)
    ax.set_title("Aktywność na urządzeniu Android (dzienna)")
    ax.set_xlabel("Data")
    ax.set_ylabel("Zdarzenia")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "06_android_timeline.png", dpi=150)
    plt.close(fig)


def generate_report_html(summary: dict) -> None:
    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <title>Raport — analiza Google Takeout</title>
  <style>
    body {{ font-family: Segoe UI, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }}
    h1 {{ color: #202124; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #dadce0; padding: 0.5rem; text-align: left; }}
    th {{ background: #f8f9fa; }}
    img {{ max-width: 100%; margin: 1rem 0; border: 1px solid #dadce0; }}
    .note {{ background: #e8f0fe; padding: 1rem; border-radius: 8px; }}
  </style>
</head>
<body>
  <h1>Analiza danych Google (Takeout)</h1>
  <p class="note">
    Raport wygenerowany automatycznie na podstawie eksportu RODO (Google Takeout).
    Prezentacja skupia się na śladzie cyfrowym użytkownika mobilnego.
  </p>

  <h2>Podsumowanie</h2>
  <table>
    <tr><th>Metryka</th><th>Wartość</th></tr>
    <tr><td>Łączna liczba zdarzeń</td><td>{summary['total_entries']:,}</td></tr>
    <tr><td>Zdarzenia z datą</td><td>{summary['entries_with_timestamp']:,}</td></tr>
    <tr><td>Liczba usług</td><td>{summary['unique_services']}</td></tr>
    <tr><td>Zapisane miejsca (Mapy)</td><td>{summary['saved_places_count']}</td></tr>
  </table>

  <h2>Wykresy</h2>
  <img src="charts/01_top_uslugi.png" alt="Top usługi">
  <img src="charts/02_mobilne_vs_inne.png" alt="Mobilne vs inne">
  <img src="charts/03_aktywnosc_rok.png" alt="Aktywność wg roku">
  <img src="charts/04_godziny_dnia.png" alt="Godziny dnia">
  <img src="charts/05_typy_czynnosci.png" alt="Typy czynności">
  <img src="charts/06_android_timeline.png" alt="Android timeline">

  <h2>Top usługi</h2>
  <table>
    <tr><th>Usługa</th><th>Liczba wpisów</th></tr>
    {"".join(f"<tr><td>{s}</td><td>{c:,}</td></tr>" for s, c in summary['top_services'][:10])}
  </table>

  <h2>Kontekst RODO</h2>
  <ul>
    <li>Art. 15 RODO — prawo dostępu do danych (Google udostępnia Takeout)</li>
    <li>Art. 20 RODO — przenoszenie danych (format HTML/JSON/CSV)</li>
    <li>Google rejestruje m.in.: wyszukiwania, historię Chrome, lokalizację, aplikacje Android</li>
  </ul>
</body>
</html>"""
    (OUTPUT_DIR / "raport.html").write_text(html, encoding="utf-8")


def main() -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    df, summary = load_data()

    chart_top_services(df)
    chart_mobile_vs_desktop(df)
    chart_activity_by_year(summary)
    chart_activity_by_hour(summary)
    chart_top_actions(df)
    chart_android_timeline(df)
    generate_report_html(summary)

    print(f"Wykresy zapisane w: {CHARTS_DIR}")
    print(f"Raport HTML:        {OUTPUT_DIR / 'raport.html'}")


if __name__ == "__main__":
    main()

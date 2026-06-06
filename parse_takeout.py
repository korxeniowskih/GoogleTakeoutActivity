"""
Parser danych Google Takeout (Moja aktywność + Mapy).
Wynik: pliki CSV i podsumowanie JSON w katalogu output/.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

TAKEOUT_DIR = Path(__file__).parent / "Takeout"
OUTPUT_DIR = Path(__file__).parent / "output"

# Polskie nazwy miesięcy w eksporcie Google
MONTHS_PL = {
    "sty": 1,
    "lut": 2,
    "mar": 3,
    "kwi": 4,
    "maj": 5,
    "cze": 6,
    "lip": 7,
    "sie": 8,
    "wrz": 9,
    "paź": 10,
    "lis": 11,
    "gru": 12,
}

OUTER_CELL_RE = re.compile(
    r'<div class="outer-cell[^"]*">(.*?)</div>\s*</div>\s*</div>',
    re.DOTALL,
)
CONTENT_CELL_RE = re.compile(
    r'<div class="content-cell[^"]*">(.*?)</div>', re.DOTALL
)
TAG_RE = re.compile(r"<[^>]+>")
HREF_RE = re.compile(r'href="([^"]+)"')
DATE_RE = re.compile(
    r"(\d{1,2})\s+"
    r"(sty|lut|mar|kwi|maj|cze|lip|sie|wrz|paź|lis|gru)\s+"
    r"(\d{4}),\s+"
    r"(\d{1,2}):(\d{2}):(\d{2})\s+"
    r"(CET|CEST|UTC)",
    re.IGNORECASE,
)


@dataclass
class ActivityEntry:
    service: str
    action: str
    detail: str
    url: str | None
    timestamp: str | None
    datetime_iso: str | None
    source_file: str


def strip_html(text: str) -> str:
    text = TAG_RE.sub(" ", text)
    return unescape(re.sub(r"\s+", " ", text).strip())


def extract_url(html_fragment: str) -> str | None:
    match = HREF_RE.search(html_fragment)
    return unescape(match.group(1)) if match else None


def parse_polish_timestamp(raw: str) -> tuple[str | None, str | None]:
    match = DATE_RE.search(raw)
    if not match:
        return None, None
    day, mon, year, hour, minute, second, tz = match.groups()
    month = MONTHS_PL.get(mon.lower())
    if not month:
        return raw.strip(), None
    dt = datetime(
        int(year), month, int(day), int(hour), int(minute), int(second)
    )
    iso = dt.isoformat()
    return f"{day} {mon} {year}, {hour}:{minute}:{second} {tz}", iso


def split_action_detail(text: str) -> tuple[str, str]:
    for prefix in (
        "Odwiedzono:",
        "Wyszukano:",
        "Obejrzano:",
        "Użyto",
        "Otwarto",
        "Zadzwoniono",
        "Wysłano",
        "Kupiono",
        "Dodano",
        "Usunięto",
        "Zaktualizowano",
        "Wyświetlono",
        "Kliknięto",
    ):
        if text.startswith(prefix):
            action = prefix.rstrip(":")
            detail = text[len(prefix) :].strip()
            return action, detail
    parts = text.split(" ", 2)
    if len(parts) >= 2:
        return parts[0], text[len(parts[0]) :].strip()
    return "inne", text


def is_metadata_cell(html_fragment: str, plain: str) -> bool:
    if "Produkty:" in html_fragment or plain.startswith("Produkty:"):
        return True
    if "Dlaczego się tutaj wyświetla" in plain:
        return True
    return not plain and "Produkty:" in html_fragment


def iter_activity_entries(html_path: Path, service: str) -> Iterator[ActivityEntry]:
    text = html_path.read_text(encoding="utf-8", errors="replace")
    for block_html in OUTER_CELL_RE.findall(text):
        for cell_html in CONTENT_CELL_RE.findall(block_html):
            plain = strip_html(cell_html)
            if not plain or is_metadata_cell(cell_html, plain):
                continue

            timestamp_raw, dt_iso = parse_polish_timestamp(plain)
            activity_text = DATE_RE.sub("", plain).strip()
            action, detail = split_action_detail(activity_text)

            yield ActivityEntry(
                service=service,
                action=action,
                detail=detail[:500],
                url=extract_url(cell_html),
                timestamp=timestamp_raw,
                datetime_iso=dt_iso,
                source_file=str(html_path.relative_to(TAKEOUT_DIR)),
            )


def parse_all_activities(takeout_dir: Path = TAKEOUT_DIR) -> list[ActivityEntry]:
    activity_root = takeout_dir / "Moja aktywność"
    entries: list[ActivityEntry] = []
    if not activity_root.exists():
        return entries

    for html_file in sorted(activity_root.glob("*/Moja_aktywność.html")):
        service = html_file.parent.name
        entries.extend(iter_activity_entries(html_file, service))
    return entries


def load_saved_places(takeout_dir: Path = TAKEOUT_DIR) -> list[dict]:
    path = takeout_dir / "Mapy (Twoje miejsca)" / "Zapisane miejsca.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    places = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        coords = geom.get("coordinates", [0, 0])
        loc = props.get("location", {})
        places.append(
            {
                "name": loc.get("name"),
                "address": loc.get("address"),
                "country": loc.get("country_code"),
                "date": props.get("date"),
                "lon": coords[0] if len(coords) > 0 else None,
                "lat": coords[1] if len(coords) > 1 else None,
                "maps_url": props.get("google_maps_url"),
            }
        )
    return places


def domain_from_url(url: str | None) -> str | None:
    if not url:
        return None
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return None


def build_summary(entries: list[ActivityEntry], places: list[dict]) -> dict:
    from collections import Counter

    services = Counter(e.service for e in entries)
    actions = Counter(e.action for e in entries)
    domains: Counter[str] = Counter()
    years: Counter[str] = Counter()
    hours: Counter[int] = Counter()
    dated = 0

    for e in entries:
        if e.url:
            d = domain_from_url(e.url)
            if d:
                domains[d] += 1
        if e.datetime_iso:
            dated += 1
            years[e.datetime_iso[:4]] += 1
            hours[int(e.datetime_iso[11:13])] += 1

    mobile_services = {
        "Android",
        "Chrome",
        "Mapy",
        "YouTube",
        "Sklep Google Play",
        "Asystent",
        "Obiektyw Google",
    }

    return {
        "total_entries": len(entries),
        "entries_with_timestamp": dated,
        "unique_services": len(services),
        "top_services": services.most_common(15),
        "top_actions": actions.most_common(10),
        "top_domains": domains.most_common(20),
        "activity_by_year": dict(sorted(years.items())),
        "activity_by_hour": {str(k): hours[k] for k in sorted(hours)},
        "mobile_focus": {
            svc: services[svc] for svc in mobile_services if svc in services
        },
        "saved_places_count": len(places),
        "saved_places_with_coords": sum(
            1 for p in places if p.get("lat") and p.get("lon") and p["lat"] != 0
        ),
    }


def save_csv(entries: list[ActivityEntry], path: Path) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(asdict(entries[0]).keys()) if entries else []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for e in entries:
            writer.writerow(asdict(e))


def main() -> None:
    print("Parsowanie Google Takeout...")
    entries = parse_all_activities()
    places = load_saved_places()
    summary = build_summary(entries, places)

    OUTPUT_DIR.mkdir(exist_ok=True)
    save_csv(entries, OUTPUT_DIR / "aktywnosc.csv")
    save_csv(
        [ActivityEntry(**{  # type: ignore[arg-type]
            "service": "Mapy",
            "action": "zapisane_miejsce",
            "detail": p.get("name") or p.get("address") or "",
            "url": p.get("maps_url"),
            "timestamp": p.get("date"),
            "datetime_iso": p.get("date"),
            "source_file": "Mapy (Twoje miejsca)/Zapisane miejsca.json",
        }) for p in places],
        OUTPUT_DIR / "miejsca.csv",
    )
    (OUTPUT_DIR / "podsumowanie.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"  Wpisów aktywności: {summary['total_entries']}")
    print(f"  Z datą:            {summary['entries_with_timestamp']}")
    print(f"  Usług:             {summary['unique_services']}")
    print(f"  Zapisanych miejsc: {summary['saved_places_count']}")
    print(f"Zapisano: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

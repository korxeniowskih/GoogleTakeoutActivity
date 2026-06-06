# Google Takeout Activity

Narzędzie do parsowania i wizualizacji danych z eksportu **Google Takeout** (Moja aktywność + zapisane miejsca z Map). Projekt przekształca surowe pliki HTML/JSON w czytelne pliki CSV, podsumowanie statystyczne oraz raport HTML z wykresami.

## Wymagania

- Python 3.10+
- Eksport Google Takeout umieszczony w katalogu `Takeout/`

## Instalacja

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

pip install -r requirements.txt
```

## Pobranie danych z Google

1. Wejdź na [Google Takeout](https://takeout.google.com/).
2. Wybierz co najmniej:
   - **Moja aktywność** (wszystkie lub wybrane usługi)
   - **Mapy (Twoje miejsca)** — opcjonalnie, dla zapisanych miejsc
3. Pobierz archiwum i rozpakuj je tak, aby struktura wyglądała tak:

```
Takeout/
├── Moja aktywność/
│   ├── Android/
│   │   └── Moja_aktywność.html
│   ├── Chrome/
│   │   └── Moja_aktywność.html
│   └── ...
└── Mapy (Twoje miejsca)/
    └── Zapisane miejsca.json
```

Katalog `Takeout/` nie jest śledzony w repozytorium — zawiera dane osobowe.

## Użycie

### Pełna analiza (zalecane)

```bash
python run_analysis.py
```

Uruchamia parsowanie i wizualizację. Wynik otwórz w przeglądarce: `output/raport.html`.

### Krok po kroku

```bash
# 1. Parsowanie HTML/JSON → CSV + JSON
python parse_takeout.py

# 2. Wykresy PNG + raport HTML
python visualize_takeout.py

# 3. (opcjonalnie) Podgląd struktury plików Takeout
python probe_takeout.py
```

## Wyniki

Po uruchomieniu w katalogu `output/` pojawią się:

| Plik | Opis |
|------|------|
| `aktywnosc.csv` | Wszystkie zdarzenia z Moja aktywność |
| `miejsca.csv` | Zapisane miejsca z Google Maps |
| `podsumowanie.json` | Statystyki: usługi, domeny, lata, godziny |
| `charts/*.png` | Wykresy (usługi, mobilne vs inne, rok, godziny, miesięczna aktywność) |
| `raport.html` | Raport z wykresami i podsumowaniem |

### Pola w `aktywnosc.csv`

- `service` — usługa Google (np. Android, Chrome, Mapy)
- `action` — typ czynności (np. Wyszukano, Odwiedzono)
- `detail` — szczegóły zdarzenia
- `url` — powiązany adres URL (jeśli występuje)
- `timestamp` — surowa data z eksportu (format polski)
- `datetime_iso` — data w formacie ISO 8601
- `source_file` — źródłowy plik w `Takeout/`

## Struktura projektu

```
├── parse_takeout.py      # Parser HTML (Moja aktywność) i JSON (Mapy)
├── visualize_takeout.py  # Wykresy matplotlib + raport HTML
├── run_analysis.py       # Uruchamia parser i wizualizację
├── probe_takeout.py      # Szybki podgląd plików Takeout
├── requirements.txt
├── Takeout/              # Dane wejściowe (gitignore)
└── output/               # Wyniki analizy (gitignore)
```

## Kontekst RODO

Eksport Google Takeout realizuje m.in.:

- **Art. 15 RODO** — prawo dostępu do danych
- **Art. 20 RODO** — przenoszenie danych w ustrukturyzowanym formacie

Google rejestruje m.in. wyszukiwania, historię przeglądarki, aktywność aplikacji Android i lokalizację — w zależności od wybranych usług w eksporcie.

## Uwagi

- Parser obsługuje polskie nazwy miesięcy w datach z eksportu (`sty`, `lut`, `mar`, …).
- Duże pliki HTML (np. Android) mogą wymagać kilku sekund na przetworzenie.
- Nie udostępniaj katalogów `Takeout/` ani `output/` — zawierają dane osobowe.

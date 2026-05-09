"""
Dotace Scraper — sleduje dotace přijaté školami
Zdroj: Monitor státní pokladny (MF ČR) — veřejné API
https://monitor.statnipokladna.cz
"""

import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MONITOR_API_URL

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Monitor API — transfery ze státního rozpočtu dle IČO příjemce
MONITOR_TRANSFERS_URL = "https://monitor.statnipokladna.cz/api/opendata/transfers"
DOTACEEU_SEARCH_URL   = "https://www.dotaceeu.cz/cs/statistiky-a-analyzy/mapa-projektu"

# Typy dotací relevantní pro školní vybavení
RELEVANT_DOTACE_KEYWORDS = [
    "vybavení", "nábytek", "rekonstrukce", "modernizace",
    "učebna", "interiér", "škola", "vzdělávání",
    "inovace výuky", "rozvoj školy",
]

# IROP, OP VVV, NPO — programy financující školní vybavení
RELEVANT_OP_PROGRAMS = [
    "IROP",        # Integrovaný regionální operační program
    "OP VVV",      # Věda, výzkum, vzdělávání
    "NPO",         # Národní plán obnovy
    "OP JAK",      # Jan Amos Komenský (nástupce OP VVV)
]


def get_dotace_for_school(ico: str, years_back: int = 4) -> dict:
    """
    Zjistí, zda škola (dle IČO) dostala dotaci v posledních N letech.
    Vrací dict s: had_dotace (bool), last_dotace_year, total_amount, programs.
    """
    if not ico or str(ico).strip() == "":
        return {"had_dotace": False, "last_year": None, "total_czk": 0, "programs": []}

    # Monitor státní pokladny — transfery
    try:
        result = _query_monitor_api(ico, years_back)
        if result:
            return result
    except Exception as e:
        pass  # tiché selhání, zkusíme jiný zdroj

    return {"had_dotace": False, "last_year": None, "total_czk": 0, "programs": []}


def _query_monitor_api(ico: str, years_back: int) -> object:
    """Dotaz na Monitor státní pokladny API."""
    year_from = datetime.now().year - years_back
    url = f"https://monitor.statnipokladna.cz/api/v1/table/transfers"
    params = {
        "ico": ico.zfill(8),
        "rok": f"{year_from}-{datetime.now().year}",
        "per_page": 50,
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return None

        data = r.json()
        if not data or "data" not in data:
            return None

        transfers = data["data"]
        if not transfers:
            return {"had_dotace": False, "last_year": None, "total_czk": 0, "programs": []}

        # Filtruj relevantní transfery
        relevant = []
        for t in transfers:
            nazev = str(t.get("nazev_polozky", "")).lower()
            if any(kw in nazev for kw in RELEVANT_DOTACE_KEYWORDS):
                relevant.append(t)

        if not relevant:
            relevant = transfers  # Vezmi vše pokud nic nefiltruje

        years = [t.get("rok", 0) for t in relevant]
        amounts = [float(t.get("castka", 0) or 0) for t in relevant]

        return {
            "had_dotace": len(relevant) > 0,
            "last_year": max(years) if years else None,
            "total_czk": sum(amounts),
            "programs": list(set(t.get("program", "") for t in relevant if t.get("program"))),
        }
    except Exception:
        return None


def batch_get_dotace(df: pd.DataFrame, delay_sec: float = 0.3) -> pd.DataFrame:
    """
    Doplní dotační informace pro celý DataFrame škol.
    Používá IČO sloupec. Cachuje výsledky.
    """
    cache_path = DATA_DIR / "dotace_cache.csv"

    # Načti cache
    cache = {}
    if cache_path.exists():
        cache_df = pd.read_csv(cache_path, dtype={"ico": str})
        cache = dict(zip(cache_df["ico"], cache_df.to_dict("records")))
        print(f"[Dotace] Cache: {len(cache)} IČO")

    results = []
    ico_list = df["ico"].fillna("").astype(str).tolist()
    total = len(ico_list)

    for i, ico in enumerate(ico_list):
        ico = ico.strip().zfill(8) if ico.strip() else ""

        if ico in cache:
            results.append(cache[ico])
            continue

        print(f"[Dotace] {i+1}/{total} — IČO {ico}", end="\r")
        info = get_dotace_for_school(ico)
        row = {"ico": ico, **info}
        results.append(row)
        cache[ico] = row

        time.sleep(delay_sec)  # rate limiting

    # Ulož cache
    cache_df = pd.DataFrame(list(cache.values()))
    cache_df.to_csv(cache_path, index=False)
    print(f"\n[Dotace] Hotovo. Uloženo do {cache_path}")

    result_df = pd.DataFrame(results)
    # Přejmenuj sloupce aby nekolidovaly
    result_df = result_df.rename(columns={
        "had_dotace": "dotace_had",
        "last_year":  "dotace_last_year",
        "total_czk":  "dotace_total_czk",
        "programs":   "dotace_programs",
    })

    return df.merge(result_df[["ico", "dotace_had", "dotace_last_year",
                                "dotace_total_czk", "dotace_programs"]],
                    on="ico", how="left")


def calculate_dotace_score(row: pd.Series, current_year: int = None) -> float:
    """
    Scoring komponent pro dotace (0-1).
    Logika: dotace 1-2 roky zpět = ideální (mají peníze nyní)
            dotace 3 roky zpět = dobrý signal
            bez dotace = 0
    """
    if current_year is None:
        current_year = datetime.now().year

    if not row.get("dotace_had", False):
        return 0.0

    last_year = row.get("dotace_last_year")
    if not last_year:
        return 0.2  # Měli dotaci ale nevíme kdy

    years_ago = current_year - int(last_year)

    if years_ago == 1:
        return 1.0   # Dostali loni — nakupují právě teď
    elif years_ago == 2:
        return 0.9   # Dostali předloni — stále aktivní
    elif years_ago == 3:
        return 0.6   # 3 roky zpět — možná ještě nakupují
    elif years_ago == 4:
        return 0.3   # 4 roky zpět — slabší signal
    else:
        return 0.1   # Starší dotace


if __name__ == "__main__":
    # Test na konkrétní škole
    test_ico = "00638013"  # ZŠ Náměstí Jiřího z Poděbrad (Praha)
    result = get_dotace_for_school(test_ico)
    print(f"Test IČO {test_ico}: {result}")

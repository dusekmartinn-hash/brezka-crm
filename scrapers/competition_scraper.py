"""
Competition Scraper — heatmapa truhlářství v ČR dle ARES
Zdroj: ARES (Administrativní registr ekonomických subjektů)
API: https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/
"""

import time
import requests
import pandas as pd
from pathlib import Path
from collections import Counter

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ARES_API_URL, ARES_NACE_TRUHLARSTVI

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# NACE kódy pro truhlářství a výrobu nábytku
NACE_CODES = {
    "16230": "Výroba ostatních výrobků z dřeva",
    "16290": "Výroba ostatních dřevěných výrobků",
    "31010": "Výroba kancelářského nábytku",
    "31020": "Výroba kuchyňského nábytku",
    "31090": "Výroba ostatního nábytku",
    "16100": "Pilařská a hoblovna dřeva",
}


ARES_VYHLEDAT_URL = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat"


def fetch_competitors_from_ares(
    nace: str = ARES_NACE_TRUHLARSTVI,
    max_results: int = 1000
) -> pd.DataFrame:
    """
    Stáhne seznam truhlářství/výrobců nábytku z ARES (nové POST API).
    Vrací DataFrame s názvem, IČO, obcí, krajem.
    """
    cache_path = DATA_DIR / f"competitors_nace_{nace}.csv"
    if cache_path.exists():
        print(f"[ARES] Načítám konkurenci z cache ({nace})...")
        return pd.read_csv(cache_path, dtype={"ico": str})

    print(f"[ARES] Stahuji (NACE {nace}) z ARES...")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    all_subjects = []
    start = 0
    page_size = 100

    while start < max_results:
        payload = {
            "czNace": [nace],
            "pocet": page_size,
            "start": start,
            "razeni": [{"sloupec": "ICO", "smer": "ASC"}],
        }
        try:
            r = requests.post(ARES_VYHLEDAT_URL, json=payload, headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[ARES] Chyba na offset {start}: {e}")
            break

        subjects = data.get("ekonomickeSubjekty", [])
        if not subjects:
            break

        all_subjects.extend(subjects)
        print(f"[ARES] Staženo: {len(all_subjects)} firem", end="\r")

        pocet_celkem = data.get("pocetCelkem", 0)
        if len(all_subjects) >= pocet_celkem or len(subjects) < page_size:
            break
        start += page_size
        time.sleep(0.3)

    if not all_subjects:
        print(f"[ARES] Žádné subjekty pro NACE {nace}.")
        return pd.DataFrame()

    rows = []
    for s in all_subjects:
        sidlo = s.get("sidlo", {}) or {}
        rows.append({
            "ico":   str(s.get("ico", "")),
            "nazev": s.get("obchodniJmeno", ""),
            "obec":  sidlo.get("nazevObce", ""),
            "okres": sidlo.get("nazevOkresu", ""),
            "kraj":  sidlo.get("nazevKraje", ""),
            "psc":   str(sidlo.get("psc", "")),
            "lat":   sidlo.get("lat"),
            "lon":   sidlo.get("lon"),
            "nace":  nace,
        })

    df = pd.DataFrame(rows)
    df.to_csv(cache_path, index=False)
    print(f"\n[ARES] Uloženo {len(df)} konkurentů (NACE {nace})")
    return df


def get_all_competitors() -> pd.DataFrame:
    """Stáhne všechna relevantní truhlářství a výrobce nábytku."""
    all_dfs = []
    for nace, popis in NACE_CODES.items():
        print(f"[ARES] NACE {nace}: {popis}")
        df = fetch_competitors_from_ares(nace, max_results=1000)
        if not df.empty:
            all_dfs.append(df)
        time.sleep(1)

    if not all_dfs:
        return pd.DataFrame()

    combined = pd.concat(all_dfs).drop_duplicates(subset=["ico"])
    combined.to_csv(DATA_DIR / "all_competitors.csv", index=False)
    print(f"[ARES] Celkem unikátních firem: {len(combined)}")
    return combined


def calculate_competition_density(
    competitors_df: pd.DataFrame,
    schools_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Pro každou školu spočítá hustotu konkurence v jejím okrese.
    Přidá sloupec 'competition_density' (0-1, kde 1 = nejvíce konkurentů).
    """
    if competitors_df.empty:
        schools_df["competition_count"] = 0
        schools_df["competition_density"] = 0.5  # neutrální pokud data chybí
        return schools_df

    # Počet konkurentů dle okresu
    okres_counts = Counter(competitors_df["okres"].dropna())
    max_count = max(okres_counts.values()) if okres_counts else 1

    def density_for_school(row):
        okres = row.get("okres", "")
        count = okres_counts.get(okres, 0)
        return count, count / max_count if max_count > 0 else 0

    schools_df[["competition_count", "competition_density"]] = pd.DataFrame(
        schools_df.apply(density_for_school, axis=1).tolist(),
        index=schools_df.index
    )
    return schools_df


def competition_score(density: float) -> float:
    """
    Scoring komponent konkurence (0-1).
    Inverzní k hustotě — méně konkurentů = vyšší skóre.
    """
    return 1.0 - float(density)


if __name__ == "__main__":
    comp_df = get_all_competitors()
    print(f"\nTop kraje dle počtu truhlářství:")
    print(comp_df["kraj"].value_counts().head(14).to_string())

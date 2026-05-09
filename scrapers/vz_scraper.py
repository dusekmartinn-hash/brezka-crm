"""
Smlouvy / VZ Scraper — sleduje nákupy nábytku školami
Zdroj: Hlídač státu API — Registr smluv (hlidacstatu.cz)

Proč smlouvy, ne VZ?
  - VZ (veřejné zakázky) search vyžaduje komerční licenci Hlídače státu.
  - Registr smluv (smlouvy) je dostupný na free tokenu a obsahuje VŠE:
      → poptávková řízení (přímé nákupy do 500k) — pro Brezku NEJDŮLEŽITĚJŠÍ
      → i velké tendry (po uzavření smlouvy)
  - Zákon č. 340/2015 Sb.: každá smlouva ≥ 50 000 Kč musí být zveřejněna.
  - Výsledek: vidíme reálné nákupy nábytku školami, ne jen vyhlášené tendry.

Nastavení (jednorázové):
  1. Registruj se na https://www.hlidacstatu.cz/api
  2. Zkopíruj API token
  3. Ulož do souboru 'hlidac_token.txt' ve složce projektu
     NEBO nastav env proměnnou: HLIDAC_TOKEN=tvůj_token
"""

import os
import time
import hashlib
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import VZ_MIN_VALUE_CZK, SHEETS

DATA_DIR   = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
TOKEN_FILE = Path(__file__).parent.parent / "hlidac_token.txt"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

HLIDAC_API = "https://api.hlidacstatu.cz/Api/v2"

# Dotazy pro smlouvy — kombinace klíčových slov pro nábytek
SMLOUVY_QUERIES = [
    "nábytek škola",
    "školní nábytek",
    "lavice škola",
    "vybavení tříd",
    "žákovský nábytek",
    "nábytek učebna",
]

# Klíčová slova která musí být v předmětu smlouvy (post-filter)
NABYTEK_KEYWORDS = [
    "nábytek", "lavice", "stůl", "stoly", "skříň", "skříně",
    "žákovský", "vybavení tříd", "vybavení učeb", "sedací",
    "regál", "police", "šatní", "interiér", "koberec",
]

# Klíčová slova škol (pro identifikaci školního zadavatele)
SCHOOL_KEYWORDS = [
    "základní škola", "střední škola", "gymnázium", "škola",
    "školní", "zš ", "sš ", " zš", " sš", "dětský domov",
    "mateřská škola", "obchodní akademie", "učiliště", "lyceum",
]


def get_token() -> str:
    """Načte Hlídač státu API token ze souboru nebo env proměnné."""
    token = os.environ.get("HLIDAC_TOKEN", "").strip()
    if token:
        return token
    if TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text().strip()
        if token:
            return token
    return ""


def _headers() -> dict:
    return {
        "Authorization": f"Token {get_token()}",
        "Accept": "application/json",
    }


# ─────────────────────────────────────────────────────────────
#  Smlouvy API (Registr smluv)
# ─────────────────────────────────────────────────────────────

def search_smlouvy(query: str, days_back: int = 90, page: int = 1) -> dict:
    """
    Vyhledá smlouvy na Hlídači státu dle klíčového slova.
    Stránkování: 25 výsledků/strana (fixní v API), max 250 stran.
    """
    token = get_token()
    if not token:
        raise ValueError("Chybí API token")

    date_from = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    params = {
        "dotaz":  f"{query} datumUzavreni:>{date_from}",
        "strana": page,
        "razeni": 1,   # nejnovější první
    }

    r = requests.get(
        f"{HLIDAC_API}/smlouvy/hledat",
        params=params,
        headers=_headers(),
        timeout=20,
    )
    if r.status_code == 401:
        raise ValueError("Neplatný API token")
    r.raise_for_status()
    return r.json()


def parse_smlouvy_results(data: dict) -> list:
    """Parsuje výsledky z Hlídač státu smlouvy API do seznamu diktů."""
    results = []
    items = data.get("results", [])

    for item in items:
        # Hodnota
        hodnota = (
            item.get("hodnotaBezDph")
            or item.get("hodnotaVcetneDph")
            or item.get("calculatedPriceWithVATinCZK")
            or 0
        )
        try:
            hodnota = float(hodnota)
        except (TypeError, ValueError):
            hodnota = 0

        # Filtr minimální hodnoty
        if hodnota > 0 and hodnota < VZ_MIN_VALUE_CZK:
            continue

        # Plátce (zadavatel)
        platce = item.get("platce", {}) or {}
        platce_nazev = platce.get("nazev", "") or ""
        platce_ico   = str(platce.get("ico", "") or "")

        # Příjemce (dodavatel — kdo dostal zakázku)
        prijemci = item.get("prijemce", []) or []
        dodavatel = prijemci[0].get("nazev", "") if prijemci else ""

        # Datum uzavření
        datum_str = str(item.get("datumUzavreni", "") or "")[:10]

        # Předmět smlouvy
        predmet = str(item.get("predmet", "") or "")

        # ID pro deduplikaci
        smlouva_id = str(item.get("id", "") or item.get("cisloSmlouvy", ""))
        if not smlouva_id:
            smlouva_id = hashlib.md5(predmet.encode()).hexdigest()[:12]

        results.append({
            "id":            smlouva_id,
            "predmet":       predmet[:120],
            "platce":        platce_nazev,
            "platce_ico":    platce_ico,
            "dodavatel":     dodavatel[:80],
            "hodnota_czk":   hodnota,
            "datum":         datum_str,
            "odkaz":         item.get("odkaz", f"https://smlouvy.gov.cz/smlouva/{smlouva_id}"),
            "zdroj":         "RegistrSmluv",
            "stazeno":       datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

    return results


def search_smlouvy_paginated(query: str, days_back: int = 90, max_pages: int = 6) -> list:
    """Stáhne všechny stránky výsledků pro daný dotaz (max 6 × 25 = 150 výsledků)."""
    all_results = []
    page = 1

    while page <= max_pages:
        try:
            data = search_smlouvy(query, days_back=days_back, page=page)
        except Exception as e:
            print(f"  [strana {page}] chyba: {e}")
            break

        results = parse_smlouvy_results(data)
        if not results:
            break

        all_results.extend(results)

        total = data.get("total", 0) or 0
        fetched = (page - 1) * 25 + len(results)
        if fetched >= total or len(results) < 25:
            break

        page += 1
        time.sleep(0.3)

    return all_results


def is_school_platce(platce_nazev: str) -> bool:
    """Vrátí True pokud je plátce (zadavatel) škola."""
    text = platce_nazev.lower()
    return any(kw in text for kw in SCHOOL_KEYWORDS)


def is_nabytek_predmet(predmet: str) -> bool:
    """Vrátí True pokud se předmět smlouvy týká nábytku/vybavení."""
    text = predmet.lower()
    return any(kw in text for kw in NABYTEK_KEYWORDS)


def match_smlouva_to_school(platce_ico: str, schools_df: pd.DataFrame) -> dict:
    """Spáruje smlouvu se školou z DB dle IČO plátce."""
    if schools_df is None or schools_df.empty or not platce_ico:
        return {}

    ico_str = str(platce_ico).strip().lstrip("0")
    matches = schools_df[
        schools_df["ico"].astype(str).str.lstrip("0") == ico_str
    ]

    if matches.empty:
        return {}

    row = matches.iloc[0]
    return {
        "skola_nazev":    row.get("nazev", ""),
        "skola_izo":      row.get("izo", ""),
        "skola_kraj":     row.get("kraj", ""),
        "skola_priorita": row.get("priorita", ""),
        "skola_score":    row.get("score_total", ""),
    }


# ─────────────────────────────────────────────────────────────
#  Hlavní monitor funkce
# ─────────────────────────────────────────────────────────────

def run_vz_monitor(
    days_back: int = 90,
    save: bool = True,
    schools_df: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    Spustí monitoring nových nákupů nábytku školami (via Registr smluv).
    Prohledá všechny SMLOUVY_QUERIES se stránkováním.

    Args:
        days_back:   Jak daleko do minulosti hledat (dní, default 90).
        save:        Uloží výsledek do output/vz_alert_YYYYMMDD.csv.
        schools_df:  DataFrame škol pro párování smlouvy → škola.
    """
    token = get_token()
    if not token:
        print("[VZ] ⚠️  Chybí API token pro Hlídač státu.")
        print("[VZ]    Zaregistruj se na: https://www.hlidacstatu.cz/api")
        print("[VZ]    Ulož token do souboru: hlidac_token.txt")
        return pd.DataFrame()

    print(f"[Monitor] Hledám nákupy nábytku školami za posledních {days_back} dní...")
    all_results = []

    for query in SMLOUVY_QUERIES:
        print(f"[Monitor]  Dotaz: '{query}'", end=" ", flush=True)
        try:
            results = search_smlouvy_paginated(query, days_back=days_back)
            print(f"→ {len(results)} smluv")
            all_results.extend(results)
        except ValueError as e:
            print(f"\n[Monitor] Chyba: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"→ chyba: {e}")
        time.sleep(0.5)

    if not all_results:
        print("[Monitor] Žádné výsledky.")
        return pd.DataFrame()

    df = pd.DataFrame(all_results)

    # Deduplikace dle ID
    df = df.drop_duplicates(subset=["id"])

    # Označ zakázky kde plátce je škola
    df["je_skola"] = df["platce"].apply(is_school_platce)

    # Označ jestli předmět odpovídá nábytku
    df["je_nabytek"] = df["predmet"].apply(is_nabytek_predmet)

    # Párování se školou z DB
    if schools_df is not None and not schools_df.empty:
        matched = df["platce_ico"].apply(lambda ico: match_smlouva_to_school(ico, schools_df))
        match_df = pd.DataFrame(matched.tolist(), index=df.index)
        df = pd.concat([df, match_df], axis=1)
        matched_count = (match_df.get("skola_nazev", pd.Series()).notna() &
                         (match_df.get("skola_nazev", pd.Series()) != "")).sum()
        print(f"[Monitor] Spárováno se školami v DB: {matched_count}")
    else:
        df["skola_nazev"]    = ""
        df["skola_priorita"] = ""
        df["skola_score"]    = ""

    # Seřaď: nejdříve školy+nábytek, pak dle hodnoty
    df["_sort"] = (~df["je_skola"]).astype(int) * 2 + (~df["je_nabytek"]).astype(int)
    df = df.sort_values(["_sort", "hodnota_czk"], ascending=[True, False])
    df = df.drop(columns=["_sort"]).reset_index(drop=True)

    skoly_count    = int(df["je_skola"].sum())
    nabytek_count  = int(df["je_nabytek"].sum())
    print(f"[Monitor] Celkem: {len(df)} unikátních smluv")
    print(f"[Monitor]   z toho školy: {skoly_count}")
    print(f"[Monitor]   z toho nábytek v předmětu: {nabytek_count}")

    if save:
        out_path = OUTPUT_DIR / f"vz_alert_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"[Monitor] Uloženo: {out_path}")

    return df


# ─────────────────────────────────────────────────────────────
#  Historický lookup pro obohacení DB škol
# ─────────────────────────────────────────────────────────────

def get_school_vz_history(ico: str, years_back: int = 7) -> dict:
    """
    Zjistí historii nákupů nábytku pro konkrétní školu (dle IČO).
    Používá Registr smluv — zachytí i přímé nákupy (poptávková řízení ≥ 50k).
    """
    token = get_token()
    empty = {"had_vz_nabytek": False, "last_vz_year": None, "last_vz_value": 0, "vz_count": 0}

    if not token or not ico:
        return empty

    date_from = (datetime.now() - timedelta(days=years_back * 365)).strftime("%Y-%m-%d")
    # Hledej smlouvy kde je škola plátcem a předmět = nábytek
    query = f"ico:{ico} (nábytek OR lavice OR vybavení OR interiér) datumUzavreni:>{date_from}"

    try:
        r = requests.get(
            f"{HLIDAC_API}/smlouvy/hledat",
            params={"dotaz": query, "strana": 1, "razeni": 1},
            headers=_headers(),
            timeout=15,
        )
        if r.status_code != 200:
            return empty

        data = r.json()
        results = parse_smlouvy_results(data)

        # Filtruj skutečně relevantní (jen nábytek v předmětu)
        results = [r for r in results if is_nabytek_predmet(r.get("predmet", ""))]

        if not results:
            return empty

        years  = [int(r["datum"][:4]) for r in results if r.get("datum") and len(r["datum"]) >= 4]
        values = [r["hodnota_czk"] for r in results if r.get("hodnota_czk")]

        return {
            "had_vz_nabytek": True,
            "last_vz_year":   max(years)  if years  else None,
            "last_vz_value":  max(values) if values else 0,
            "vz_count":       len(results),
        }
    except Exception:
        return empty


if __name__ == "__main__":
    print("=== Test Monitor (Registr smluv) ===")
    df = run_vz_monitor(days_back=90)
    if not df.empty:
        print()
        skoly = df[df["je_skola"] & df["je_nabytek"]]
        print(f"Školy s nábytkem v předmětu: {len(skoly)}")
        print()
        print(skoly[["platce", "predmet", "hodnota_czk", "datum"]].head(10).to_string(index=False))

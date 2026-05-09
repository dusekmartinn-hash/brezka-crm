"""
MŠMT Scraper — stahuje data o školách z otevřených dat MŠMT
Zdroj: https://rejstriky.msmt.cz/opendata/
"""

import os
import io
import zipfile
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path

# Přidat root do path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MSMT_OPENDATA_URL, TARGET_SCHOOL_TYPES

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


MSMT_JSONLD_URL = "https://lkod-ftp.msmt.gov.cz/00022985/88a7c12b-6084-4e47-8b50-46097c6e683f/RSSZ-cela-CR.jsonld"


def download_msmt_registry(force_refresh: bool = False) -> Path:
    """Stáhne JSON-LD rejstřík škol z MŠMT (nový formát od 2024). Cachuje lokálně."""
    jsonld_path = DATA_DIR / "msmt_rejstrik.jsonld"

    if not force_refresh and jsonld_path.exists():
        print(f"[MŠMT] Používám cache: {jsonld_path}")
        return jsonld_path

    print(f"[MŠMT] Stahuji rejstřík škol (JSON-LD) z MŠMT FTP...")
    try:
        r = requests.get(MSMT_JSONLD_URL, timeout=120)
        r.raise_for_status()
        with open(jsonld_path, "wb") as f:
            f.write(r.content)
        print(f"[MŠMT] Uloženo: {jsonld_path} ({len(r.content)//1024} KB)")
    except Exception as e:
        print(f"[MŠMT] Chyba při stahování: {e}")
        raise RuntimeError(
            "Nepodařilo se stáhnout data MŠMT.\n"
            f"Zkus ručně stáhnout: {MSMT_JSONLD_URL}\n"
            "a uložit jako data/msmt_rejstrik.jsonld"
        )
    return jsonld_path


TARGET_DRUH_CODES = {"B00", "C00"}  # B00=ZŠ, C00=SŠ


def parse_msmt_jsonld(jsonld_path: Path) -> pd.DataFrame:
    """
    Parsuje JSON-LD rejstřík MŠMT → DataFrame.
    Struktura: data['list'] = právnické osoby, každá má skolyAZarizeni[].
    Filtrujeme B00 (ZŠ) a C00 (SŠ).
    """
    import json
    print(f"[MŠMT] Parsuju JSON-LD: {jsonld_path} ...")

    with open(jsonld_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entities = data.get("list", [])
    skoly = []

    for entity in entities:
        ico          = str(entity.get("ico", "")).strip()
        kraj         = str(entity.get("kraj", "")).strip()
        entity_nazev = str(entity.get("uplnyNazev", "") or "").strip()
        entity_zkrac = str(entity.get("zkracenyNazev", "") or "").strip()
        emaily = entity.get("emaily", [])
        email  = emaily[0] if emaily else ""

        adresa = entity.get("adresa", {}) or {}
        ulice  = str(adresa.get("ulice", "")).strip()
        obec   = str(adresa.get("obec", "")).strip()
        psc    = str(adresa.get("psc", "")).strip()
        okres  = str(adresa.get("okres", "")).strip()

        reditel = entity.get("reditel") or {}
        kontakt = str(reditel.get("nazevOsoby", "")).strip()

        for skola in entity.get("skolyAZarizeni", []):
            druh = str(skola.get("druh", "")).strip()
            if druh not in TARGET_DRUH_CODES:
                continue

            # Kapacita — v poli kapacity[].nejvyssiPovolenyPocet
            kapacita = None
            for kap in (skola.get("kapacity") or []):
                val = kap.get("nejvyssiPovolenyPocet")
                if val:
                    kapacita = int(val) if kapacita is None else kapacita + int(val)

            # Adresa — z mistaVyuky[0].adresa (přesnější než adresa entity)
            mista = skola.get("mistaVyuky") or []
            skola_adresa = mista[0].get("adresa", {}) if mista else {}
            s_obec  = str(skola_adresa.get("obec", obec)).strip()
            s_psc   = str(skola_adresa.get("psc", psc)).strip().replace(" ", "")
            s_ulice = str(skola_adresa.get("ulice", ulice)).strip()
            s_okres = str(skola_adresa.get("okres") or skola_adresa.get("uzemiDleORP") or okres).strip()
            s_cp    = skola_adresa.get("cisloDomovni", "")
            s_ulice_full = f"{s_ulice} {s_cp}".strip() if s_cp else s_ulice
            rúian   = skola_adresa.get("kodRUIAN")  # pro budoucí geokódování přes RÚIAN API

            # Název: entity.uplnyNazev je správný plný název (obsahuje město/IČ)
            # skola.uplnyNazev je jen generický typ ("Základní škola")
            nazev_full = entity_nazev or str(skola.get("uplnyNazev", "")).strip()
            nazev_zkrac = entity_zkrac or nazev_full

            skoly.append({
                "nazev":          nazev_full,
                "nazev_zkrac":    nazev_zkrac,
                "izo":            str(skola.get("izo", "")).strip(),
                "ico":            ico,
                "druh":           druh,
                "druh_nazev":     "Základní škola" if druh == "B00" else "Střední škola",
                "kraj":           kraj,
                "okres":          s_okres,
                "obec":           s_obec,
                "ulice":          s_ulice_full,
                "psc":            s_psc,
                "kapacita":       kapacita,
                "pocet_zaku":     int(kapacita * 0.72) if kapacita else 0,
                "email":          email,
                "telefon":        "",
                "web":            "",
                "zrizovatel":     str((entity.get("zrizovatele") or [{}])[0].get("nazevOsoby", "")).strip(),
                "zrizovatel_typ": str(entity.get("typZrizovatele", "")).strip(),
                "reditel":        kontakt,
                "datum_vzniku":   str(skola.get("datumZapisu", "")).strip(),
                "rúian":          rúian,
            })

    df = pd.DataFrame(skoly)
    print(f"[MŠMT] Načteno {len(df)} škol (ZŠ+SŠ) z {len(entities)} právnických osob.")
    return df


def filter_target_schools(df: pd.DataFrame) -> pd.DataFrame:
    """Filtruje pouze cílové typy škol (ZŠ=B00, SŠ=C00)."""
    if df.empty:
        return df
    # JSON-LD parser už filtruje dle druh kódů — jen ověříme
    if "druh" in df.columns:
        filtered = df[df["druh"].isin(TARGET_DRUH_CODES)].copy()
        print(f"[MŠMT] Cílové školy (ZŠ+SŠ): {len(filtered)} (z {len(df)})")
        return filtered
    return df


def load_student_counts() -> pd.DataFrame:
    """
    Stáhne počty žáků ze statistik MŠMT (výkazy škol).
    MŠMT publikuje roční výkazy na: https://toiler.uiv.cz/rocenka/
    Pro v0.1 použijeme dostupný CSV export.
    """
    counts_path = DATA_DIR / "zaci_counts.csv"
    if counts_path.exists():
        print(f"[MŠMT] Načítám počty žáků z cache...")
        return pd.read_csv(counts_path, dtype={"izo": str})

    # Zkusíme stáhnout výkaz R13 (základní výkaz o škole)
    # MŠMT UIV publikuje na: https://toiler.uiv.cz
    stats_url = "https://toiler.uiv.cz/rocenka/tab2.asp"
    try:
        print(f"[MŠMT] Stahuji počty žáků...")
        tables = pd.read_html(stats_url)
        if tables:
            df = tables[0]
            df.to_csv(counts_path, index=False)
            return df
    except Exception as e:
        print(f"[MŠMT] Výkazy nedostupné online: {e}")
        print("[MŠMT] Počty žáků budou odhadnuty z kapacity.")

    return pd.DataFrame()


def get_all_schools(force_refresh: bool = False) -> pd.DataFrame:
    """
    Hlavní funkce — vrátí DataFrame všech cílových škol ČR.
    """
    cache_path = DATA_DIR / "skoly_raw.csv"

    if not force_refresh and cache_path.exists():
        print(f"[MŠMT] Načítám z cache: {cache_path}")
        df = pd.read_csv(cache_path, dtype={"ico": str, "izo": str, "psc": str})
        print(f"[MŠMT] Cache: {len(df)} škol")
        return df

    jsonld_path = download_msmt_registry(force_refresh)
    df = parse_msmt_jsonld(jsonld_path)
    df = filter_target_schools(df)

    # Přidej počty žáků pokud dostupné
    counts_df = load_student_counts()
    if not counts_df.empty and "izo" in counts_df.columns:
        df = df.merge(counts_df[["izo", "pocet_zaku"]], on="izo", how="left")
    elif "kapacita" in df.columns:
        # Odhadni počty žáků z kapacity (typicky škola je na ~70% kapacity)
        df["pocet_zaku"] = pd.to_numeric(df["kapacita"], errors="coerce").fillna(0) * 0.7
        df["pocet_zaku"] = df["pocet_zaku"].astype(int)

    df.to_csv(cache_path, index=False)
    print(f"[MŠMT] Uloženo {len(df)} škol do {cache_path}")
    return df


if __name__ == "__main__":
    df = get_all_schools(force_refresh=True)
    print(df.head(10).to_string())
    print(f"\nCelkem škol: {len(df)}")
    print(f"Kraje: {df['kraj'].value_counts().to_string()}")

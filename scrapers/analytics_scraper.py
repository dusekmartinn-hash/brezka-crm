"""
Analytics Scraper — analýza trhu školního nábytku
Kdo dostává zakázky? Jaké jsou ceny? Které regiony jsou aktivní?
Zdroj: Hlídač státu — Registr smluv
"""

import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

DATA_DIR   = Path(__file__).parent.parent / "data"
TOKEN_FILE = Path(__file__).parent.parent / "hlidac_token.txt"
DATA_DIR.mkdir(exist_ok=True)

HLIDAC_API = "https://api.hlidacstatu.cz/Api/v2"

MARKET_QUERIES = [
    "školní nábytek",
    "nábytek škola",
    "lavice škola",
    "žákovský nábytek",
    "vybavení tříd nábytek",
]

SCHOOL_KEYWORDS = [
    "základní škola", "střední škola", "gymnázium", "škola",
    "učiliště", "akademie", "lyceum", "školní",
]


def get_token() -> str:
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    import os
    return os.environ.get("HLIDAC_TOKEN", "").strip()


def fetch_market_smlouvy(years_back: int = 3, max_per_query: int = 200) -> pd.DataFrame:
    """
    Stáhne smlouvy na školní nábytek za posledních N let.
    Cachuje výsledky do data/market_smlouvy.csv.
    Vrací DataFrame se sloupci: platce, platce_ico, dodavatel, hodnota_czk, datum, kraj_platce.
    """
    cache_path = DATA_DIR / "market_smlouvy.csv"
    cache_age_days = 7  # obnovit cache každých 7 dní

    if cache_path.exists():
        age = (datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)).days
        if age < cache_age_days:
            print(f"[Analytics] Načítám z cache ({cache_path.name}, stáří {age}d)...")
            return pd.read_csv(cache_path, dtype={"platce_ico": str})

    token = get_token()
    if not token:
        print("[Analytics] Chybí API token")
        return pd.DataFrame()

    headers = {"Authorization": f"Token {token}", "Accept": "application/json"}
    date_from = (datetime.now() - timedelta(days=years_back * 365)).strftime("%Y-%m-%d")

    all_rows = []
    seen_ids = set()

    for query in MARKET_QUERIES:
        print(f"[Analytics] Stahuji: '{query}'...", end=" ", flush=True)
        pages_fetched = 0
        max_pages = max_per_query // 25 + 1

        for page in range(1, max_pages + 1):
            try:
                r = requests.get(
                    f"{HLIDAC_API}/smlouvy/hledat",
                    params={
                        "dotaz":  f"{query} datumUzavreni:>{date_from}",
                        "strana": page,
                        "razeni": 1,
                    },
                    headers=headers,
                    timeout=20,
                )
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f"chyba: {e}")
                break

            items = data.get("results", [])
            if not items:
                break

            for item in items:
                item_id = str(item.get("id", "") or item.get("cisloSmlouvy", ""))
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)

                platce = item.get("platce", {}) or {}
                platce_nazev = platce.get("nazev", "") or ""
                platce_ico   = str(platce.get("ico", "") or "")

                prijemci = item.get("prijemce", []) or []
                dodavatel = prijemci[0].get("nazev", "") if prijemci else ""
                dodavatel_ico = str(prijemci[0].get("ico", "") if prijemci else "")

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

                if hodnota < 50_000:
                    continue

                datum_str = str(item.get("datumUzavreni", "") or "")[:10]
                predmet   = str(item.get("predmet", "") or "")

                is_skola = any(kw in platce_nazev.lower() for kw in SCHOOL_KEYWORDS)

                all_rows.append({
                    "id":             item_id,
                    "platce":         platce_nazev,
                    "platce_ico":     platce_ico,
                    "dodavatel":      dodavatel[:80],
                    "dodavatel_ico":  dodavatel_ico,
                    "hodnota_czk":    hodnota,
                    "datum":          datum_str,
                    "rok":            int(datum_str[:4]) if datum_str and len(datum_str) >= 4 else None,
                    "predmet":        predmet[:120],
                    "je_skola":       is_skola,
                })

            pages_fetched += 1
            total = data.get("total", 0) or 0
            if len(items) < 25 or pages_fetched * 25 >= min(total, max_per_query):
                break
            time.sleep(0.3)

        print(f"→ {pages_fetched} stran")
        time.sleep(0.5)

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows).drop_duplicates(subset=["id"])
    df.to_csv(cache_path, index=False, encoding="utf-8-sig")
    print(f"[Analytics] Celkem smluv: {len(df)} | Uloženo: {cache_path.name}")
    return df


def analyze_suppliers(df: pd.DataFrame) -> dict:
    """
    Analyzuje dodavatele školního nábytku.
    Vrací dict s různými analytickými pohledy.
    """
    if df.empty:
        return {}

    # Filtruj jen školy jako plátce
    skoly_df = df[df["je_skola"]].copy() if "je_skola" in df.columns else df.copy()

    if skoly_df.empty:
        skoly_df = df.copy()

    # ── Top dodavatelé dle počtu zakázek ──────────────────────
    supplier_counts = (
        skoly_df.groupby("dodavatel")
        .agg(
            pocet_zakazek=("id", "count"),
            celkova_hodnota=("hodnota_czk", "sum"),
            prumerna_hodnota=("hodnota_czk", "mean"),
            prvni_zakazka=("datum", "min"),
            posledni_zakazka=("datum", "max"),
        )
        .reset_index()
        .sort_values("pocet_zakazek", ascending=False)
    )

    # Filtruj prázdné názvy
    supplier_counts = supplier_counts[supplier_counts["dodavatel"].str.len() > 2]

    # ── Tržní podíl (% z celkové hodnoty) ────────────────────
    total_value = supplier_counts["celkova_hodnota"].sum()
    supplier_counts["trzni_podil_pct"] = (
        supplier_counts["celkova_hodnota"] / total_value * 100
    ).round(1) if total_value > 0 else 0

    # ── Trend po letech ───────────────────────────────────────
    yearly_trend = (
        skoly_df.groupby("rok")
        .agg(
            pocet=("id", "count"),
            hodnota=("hodnota_czk", "sum"),
        )
        .reset_index()
        .dropna(subset=["rok"])
        .sort_values("rok")
    )
    yearly_trend["rok"] = yearly_trend["rok"].astype(int)

    # ── Aktivní školy (počet různých platců) ─────────────────
    active_schools = skoly_df["platce"].nunique()

    # ── Průměrná hodnota smlouvy ──────────────────────────────
    avg_value = skoly_df["hodnota_czk"].mean()
    median_value = skoly_df["hodnota_czk"].median()

    # ── Brezka vs. trh (hypoteticky) ─────────────────────────
    # Hledej Brezku nebo Matyas v dodavatelích
    brezka_mask = skoly_df["dodavatel"].str.lower().str.contains(
        "brezka|matyas|olmr|nupaky", na=False
    )
    brezka_df = skoly_df[brezka_mask]

    return {
        "top_suppliers":   supplier_counts.head(20),
        "yearly_trend":    yearly_trend,
        "active_schools":  active_schools,
        "total_contracts": len(skoly_df),
        "total_value_czk": skoly_df["hodnota_czk"].sum(),
        "avg_value_czk":   avg_value,
        "median_value_czk": median_value,
        "brezka_contracts": len(brezka_df),
        "raw_df":          skoly_df,
    }


def get_recent_opportunities(df: pd.DataFrame, days: int = 90) -> pd.DataFrame:
    """
    Vrátí nedávné smlouvy škol jako příležitosti pro follow-up.
    Škola co koupila X měsíců zpět = vhodný čas pro oslovení (budují vztahy,
    nebo potřebují opravy/doplnění).
    """
    if df.empty:
        return pd.DataFrame()

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    recent = df[
        (df["je_skola"]) &
        (df["datum"] >= cutoff)
    ].copy()

    recent = recent.sort_values("hodnota_czk", ascending=False)
    return recent


if __name__ == "__main__":
    print("=== Analýza trhu školního nábytku ===")
    df = fetch_market_smlouvy(years_back=3)
    if df.empty:
        print("Žádná data.")
    else:
        analysis = analyze_suppliers(df)
        top = analysis["top_suppliers"]
        print(f"\nCelkem smluv (školy): {analysis['total_contracts']}")
        print(f"Celková hodnota:       {analysis['total_value_czk']:,.0f} Kč")
        print(f"Průměrná smlouva:      {analysis['avg_value_czk']:,.0f} Kč")
        print(f"\nTop 10 dodavatelů:")
        print(top[["dodavatel", "pocet_zakazek", "celkova_hodnota", "trzni_podil_pct"]].head(10).to_string(index=False))

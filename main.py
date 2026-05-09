"""
Brezka CRM — Hlavní orchestrátor
Spuštění: python main.py [--fresh] [--skip-dotace] [--skip-vz] [--skip-sheets]

Příznaky:
  --fresh        Smaže cache a stáhne vše znovu
  --skip-dotace  Přeskočí dotace scraping (pomalé, API rate limiting)
  --skip-vz      Přeskočí VZ historii škol
  --skip-sheets  Nepropíše do Google Sheets (jen lokální CSV + mapa)
  --top N        Exportuje jen top N škol (default: vše)
  --map-only     Jen vygeneruje mapu z existujících dat
"""

import sys
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

# Moduly projektu
from scrapers.msmt_scraper       import get_all_schools
from scrapers.competition_scraper import get_all_competitors, calculate_competition_density
from scrapers.dotace_scraper      import batch_get_dotace
from scrapers.vz_scraper          import run_vz_monitor
from scoring.school_scorer        import score_all_schools, export_visit_list
from maps.heatmap                 import build_school_map

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def parse_args():
    p = argparse.ArgumentParser(description="Brezka CRM — school scoring pipeline")
    p.add_argument("--fresh",        action="store_true", help="Ignoruj cache")
    p.add_argument("--skip-dotace",  action="store_true", help="Přeskoč dotace API")
    p.add_argument("--skip-vz",      action="store_true", help="Přeskoč VZ historii škol")
    p.add_argument("--skip-sheets",  action="store_true", help="Nepropíše do Google Sheets")
    p.add_argument("--skip-geo",     action="store_true", help="Přeskoč geokódování (pomalé)")
    p.add_argument("--top",          type=int, default=None, help="Export top N škol")
    p.add_argument("--map-only",     action="store_true", help="Jen vygeneruj mapu")
    p.add_argument("--vz-monitor",   action="store_true", help="Jen spusť VZ monitor")
    return p.parse_args()


def run_geocoding(df: pd.DataFrame) -> pd.DataFrame:
    """Geokóduje školy (adresa → lat/lon). Cachuje výsledky."""
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter
    import time

    geo_cache_path = Path("data/geocoding_cache.csv")

    # Načti cache
    geo_cache = {}
    if geo_cache_path.exists():
        cache_df = pd.read_csv(geo_cache_path, dtype={"izo": str})
        for _, row in cache_df.iterrows():
            geo_cache[str(row.get("izo", ""))] = (row.get("lat"), row.get("lon"))

    geolocator = Nominatim(user_agent="brezka-crm/1.0")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)

    lats, lons = [], []
    total = len(df)

    for i, (_, row) in enumerate(df.iterrows()):
        izo = str(row.get("izo", ""))

        if izo in geo_cache:
            lat, lon = geo_cache[izo]
            lats.append(lat)
            lons.append(lon)
            continue

        # Sestavení adresy pro geokódování
        parts = [
            row.get("ulice", ""),
            row.get("obec", ""),
            row.get("psc", ""),
            "Česká republika"
        ]
        address = ", ".join(str(p) for p in parts if p)

        print(f"[Geo] {i+1}/{total}: {row.get('nazev', '')}", end="\r")

        try:
            location = geocode(address)
            if location:
                lat, lon = location.latitude, location.longitude
            else:
                # Fallback: jen obec
                loc2 = geocode(f"{row.get('obec', '')}, Česká republika")
                lat = loc2.latitude if loc2 else None
                lon = loc2.longitude if loc2 else None
        except Exception:
            lat, lon = None, None

        lats.append(lat)
        lons.append(lon)
        geo_cache[izo] = (lat, lon)

    # Ulož cache
    pd.DataFrame([
        {"izo": k, "lat": v[0], "lon": v[1]} for k, v in geo_cache.items()
    ]).to_csv(geo_cache_path, index=False)

    df["lat"] = lats
    df["lon"] = lons
    geo_success = sum(1 for l in lats if l is not None)
    print(f"\n[Geo] Geokódováno: {geo_success}/{total} škol")
    return df


def main():
    args = parse_args()
    start_time = datetime.now()
    print(f"\n{'='*60}")
    print(f"  BREZKA CRM — Spuštěno {start_time.strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}\n")

    # ── REŽIM: Jen VZ monitor ──────────────────────────────────
    if args.vz_monitor:
        print("[VZ Monitor] Spouštím standalone monitoring...")
        # Pokud existuje scored CSV, předáme ho pro párování VZ → škola
        scored_path = Path("output/skoly_scored.csv")
        db_df = None
        if scored_path.exists():
            db_df = pd.read_csv(scored_path, dtype={"ico": str, "izo": str})
            print(f"[VZ Monitor] Načtena DB škol: {len(db_df)} škol pro párování")
        vz_df = run_vz_monitor(schools_df=db_df)
        if not args.skip_sheets and not vz_df.empty:
            from sheets.sheets_sync import sync_vz_monitor, sync_dashboard
            sync_vz_monitor(vz_df)
            if db_df is not None:
                sync_dashboard(db_df, vz_df)
        return

    # ── KROK 1: Databáze škol (MŠMT) ──────────────────────────
    print("[ 1/6 ] Načítám databázi škol (MŠMT)...")
    schools_df = get_all_schools(force_refresh=args.fresh)
    print(f"        ✅ {len(schools_df)} škol načteno\n")

    # ── KROK 2: Geokódování ────────────────────────────────────
    if not args.skip_geo:
        if "lat" not in schools_df.columns or schools_df["lat"].isna().sum() > len(schools_df) * 0.5:
            print("[ 2/6 ] Geokóduji školy (může trvat 20-40 min pro celou ČR)...")
            schools_df = run_geocoding(schools_df)
        else:
            print(f"[ 2/6 ] Geokódování — z cache ({schools_df['lat'].notna().sum()} škol)\n")
    else:
        print("[ 2/6 ] Geokódování přeskočeno (--skip-geo)\n")

    # ── REŽIM: Jen mapa ────────────────────────────────────────
    if args.map_only:
        scored_path = Path("output/skoly_scored.csv")
        if scored_path.exists():
            schools_df = pd.read_csv(scored_path)
            build_school_map(schools_df)
        else:
            print("Soubor output/skoly_scored.csv nenalezen. Spusť nejdříve bez --map-only.")
        return

    # ── KROK 3: Konkurence (truhlářství) ──────────────────────
    print("[ 3/6 ] Načítám data o konkurenci (ARES — truhlářství)...")
    competitors_df = get_all_competitors()
    schools_df = calculate_competition_density(competitors_df, schools_df)
    print(f"        ✅ {len(competitors_df)} konkurentů, hustota vypočítána\n")

    # ── KROK 4: Dotace ────────────────────────────────────────
    if not args.skip_dotace:
        print("[ 4/6 ] Stahuji historii dotací (Monitor MF — může trvat)...")
        schools_df = batch_get_dotace(schools_df)
        print(f"        ✅ Dotace doplněny\n")
    else:
        print("[ 4/6 ] Dotace přeskočeny (--skip-dotace)\n")
        schools_df["dotace_had"] = False
        schools_df["dotace_last_year"] = None
        schools_df["dotace_total_czk"] = 0

    # ── KROK 5: Scoring ───────────────────────────────────────
    print("[ 5/6 ] Počítám skóre a priority...")
    schools_df = score_all_schools(schools_df)

    # Ulož scored CSV
    scored_path = OUTPUT_DIR / "skoly_scored.csv"
    schools_df.to_csv(scored_path, index=False, encoding="utf-8-sig")
    print(f"        ✅ Uloženo: {scored_path}\n")

    # Export visit listu (priorita A)
    visit_path = OUTPUT_DIR / "visit_list_priorita_A.csv"
    visit_df = export_visit_list(schools_df, visit_path)
    print(f"        ✅ Visit list (priorita A): {len(visit_df)} škol → {visit_path}\n")

    # ── KROK 6: Mapa + VZ + Sheets ────────────────────────────
    print("[ 6/6 ] Generuji mapu a synchronizuji...")

    # Mapa
    map_path = build_school_map(schools_df, competitors_df)
    print(f"        ✅ Mapa: {map_path}")

    # VZ Monitor
    if not args.skip_vz:
        print("        VZ Monitor...")
        vz_df = run_vz_monitor(schools_df=schools_df)
    else:
        vz_df = pd.DataFrame()

    # Google Sheets
    if not args.skip_sheets:
        print("        Synchronizace Google Sheets...")
        try:
            from sheets.sheets_sync import sync_schools_db, sync_vz_monitor, init_crm_sheet, sync_dashboard
            sync_schools_db(schools_df)
            init_crm_sheet()
            if not vz_df.empty:
                sync_vz_monitor(vz_df)
            sync_dashboard(schools_df, vz_df if not vz_df.empty else None)
        except FileNotFoundError as e:
            print(f"        ⚠️  Sheets přeskočeny: {e}")
        except Exception as e:
            print(f"        ⚠️  Sheets chyba: {e}")
    else:
        print("        Sheets přeskočeny (--skip-sheets)")

    # ── Shrnutí ───────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).seconds
    priority_counts = schools_df["priorita"].value_counts()
    print(f"\n{'='*60}")
    print(f"  HOTOVO za {elapsed}s")
    print(f"  Celkem škol:     {len(schools_df)}")
    print(f"  Priorita A:      {priority_counts.get('A', 0)} škol (osobní návštěvy)")
    print(f"  Priorita B:      {priority_counts.get('B', 0)} škol (email outreach)")
    print(f"  Mapa:            {map_path}")
    print(f"  Visit list:      {visit_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

"""
School Scorer — vypočítá prioritní skóre pro každou školu.
Skóre 0-100. Priorita A (68+), B (42-67), C (<42).

Logika vychází z reálného trhu:
  - Dotace 2-3 roky zpět = škola právě PŘIPRAVUJE velký tendr → nejvyšší signál
  - Bez VZ = nakupuje poptávkovým řízením (osloví 3 firmy, do 250-500k) → rychlá příležitost
  - Dva obchodní přístupy: PM (poptávka, rychlé) vs VZ (tendr, budujeme vztah)
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    WEIGHTS, REGION_SCORES,
    PRIORITY_A_MIN, PRIORITY_B_MIN,
)


# ─────────────────────────────────────────────
#  Jednotlivé komponenty skóre
# ─────────────────────────────────────────────

def score_dotace(row: pd.Series, current_year: int = None) -> float:
    """
    Dotace komponent (0–1).

    Klíčová logika (dle reálné praxe):
      Velký tendr se připravuje 1-2 roky dopředu.
      → Dotace přijatá 2-3 roky zpět = TEPRVE TEĎ se chystají nakupovat. MAX signál.
      → Dotace loni = možná ještě ani neví co kupovat (příliš brzy).
      → Dotace 4-5 let = možná ještě stihnou, ale slabší.
      → Bez dotace = žádný signál (ale neznamená že nenakoupí přes poptávku).
    """
    if current_year is None:
        current_year = datetime.now().year

    if not row.get("dotace_had", False):
        return 0.0

    last_year = row.get("dotace_last_year")
    if not last_year or pd.isna(last_year):
        return 0.25   # Víme že dotace byla, nevíme kdy

    years_ago = current_year - int(last_year)

    # Optimum je 2-3 roky zpět (připravují tendr právě teď)
    if years_ago == 2:
        return 1.0    # IDEÁLNÍ — připravují tendr tento rok
    elif years_ago == 3:
        return 0.95   # Těsně vedle ideálu — stále aktivní příprava
    elif years_ago == 1:
        return 0.6    # Čerstvá dotace — teprve začínají plánovat
    elif years_ago == 4:
        return 0.5    # Možná ještě v realizaci
    elif years_ago == 5:
        return 0.3    # Spíše dokončeno, ale vztah stojí za to
    else:
        return 0.1    # Starší — slabý signál


def score_size(pocet_zaku) -> float:
    """
    Velikost školy → 0–1.
    Poznámka: malé školy (50-150 žáků) nejsou bezcenné —
    poptávkové řízení do 250k je pro ně normální způsob nákupu.
    """
    n = float(pocet_zaku) if pocet_zaku else 0

    if n < 50:
        return 0.0
    elif n < 150:
        return 0.3    # malá — poptávkové řízení (rychlá příležitost)
    elif n < 300:
        return 0.55   # střední
    elif n < 500:
        return 0.75   # velká
    elif n < 700:
        return 0.90   # velmi velká
    else:
        return 1.0    # mega škola


def score_vz_gap(row: pd.Series, current_year: int = None) -> float:
    """
    VZ gap + poptávkový potenciál (0–1).

    Logika přepracována:
      - Bez VZ VŮBEC = velmi pravděpodobně nakupuje přes poptávkové řízení
        (přímý nákup, oslovení 3 firem) → PŘÍLEŽITOST, ne problém.
      - VZ gap 5+ let = přezrálá, chystá se na velký tendr.
      - VZ gap 2-3 roky = právě nakoupila, nezajímá nás teď.
      - VZ nedávno (< 2 roky) = nejspíše neobnovuje.
    """
    if current_year is None:
        current_year = datetime.now().year

    had_vz = row.get("had_vz_nabytek", False)

    if not had_vz:
        # Bez VZ = nakupuje přes poptávku = CHCEME BÝT V TÉ TROJCE
        # Vyšší skóre než "právě nakoupila přes VZ"
        return 0.75

    last_year = row.get("last_vz_year")
    if not last_year or pd.isna(last_year):
        return 0.55   # Má VZ historii ale nevíme kdy — neutrální

    years_ago = current_year - int(last_year)

    if years_ago >= 8:
        return 1.0    # Extrémně přezrálá — maximální priorita
    elif years_ago >= 6:
        return 0.85   # Velmi přezrálá
    elif years_ago >= 4:
        return 0.65   # Přezrálá — brzy obnoví
    elif years_ago >= 2:
        return 0.35   # Relativně čerstvé
    else:
        return 0.1    # Nakoupila nedávno — nezajímá nás teď


def score_region(kraj: str) -> float:
    """
    Krajový bonus (0–1).
    Praha + Středočeský + Jihočeský = prioritní kraje.
    """
    if not kraj or pd.isna(kraj):
        return 0.3
    # Normalizace: hledáme substring match (různé formáty v datech)
    kraj_norm = str(kraj).strip()
    for key, val in REGION_SCORES.items():
        if key.lower() in kraj_norm.lower() or kraj_norm.lower() in key.lower():
            return val
    return 0.3  # Neznámý kraj — neutrální


def score_competition(competition_density: float) -> float:
    """
    Konkurence komponent (0–1) — inverzní hustota truhlářství v okrese.
    Menší váha (10b) — vztah > konkurence (malá zakázka → spokojený → velká zakázka).
    """
    density = float(competition_density) if competition_density and not pd.isna(competition_density) else 0.5
    return max(0.0, 1.0 - density)


# ─────────────────────────────────────────────
#  Klasifikace obchodního přístupu
# ─────────────────────────────────────────────

def classify_approach(row: pd.Series) -> str:
    """
    Určí doporučený obchodní přístup:
      PM  = Poptávkové řízení (rychlé, oslovit ASAP, do 250-500k)
      VZ  = Velký tendr (budovat vztah, připravovat nabídku 1-2 roky)
      OBA = Škola má potenciál pro oba přístupy
    """
    had_vz   = row.get("had_vz_nabytek", False)
    dotace   = row.get("dotace_had", False)
    zaci     = float(row.get("pocet_zaku", 0) or 0)
    current  = datetime.now().year
    last_vz_year = row.get("last_vz_year")
    dotace_year  = row.get("dotace_last_year")

    # Signál pro velký tendr
    vz_signal = False
    if dotace and dotace_year and not pd.isna(dotace_year):
        years_since_dotace = current - int(dotace_year)
        if 1 <= years_since_dotace <= 4:
            vz_signal = True

    if had_vz and last_vz_year and not pd.isna(last_vz_year):
        if (current - int(last_vz_year)) >= 5:
            vz_signal = True

    # Signál pro poptávkové řízení
    pm_signal = not had_vz or zaci < 400

    if vz_signal and pm_signal:
        return "OBA"
    elif vz_signal:
        return "VZ"
    elif pm_signal:
        return "PM"
    else:
        return "PM"   # Default — kontaktovat a zjistit


def approach_label(approach: str) -> str:
    labels = {
        "PM":  "🟢 Poptávkové řízení — oslovit ASAP",
        "VZ":  "🔵 Tendr — budovat vztah",
        "OBA": "⭐ Obojí — prioritní cíl",
    }
    return labels.get(approach, approach)


# ─────────────────────────────────────────────
#  Hlavní scoring funkce
# ─────────────────────────────────────────────

def compute_school_score(row: pd.Series) -> dict:
    """
    Vypočítá celkové skóre školy a klasifikuje přístup.
    Vrací dict se všemi komponentami.
    """
    current_year = datetime.now().year

    s_dotace      = score_dotace(row, current_year)
    s_size        = score_size(row.get("pocet_zaku", 0))
    s_vz          = score_vz_gap(row, current_year)
    s_region      = score_region(row.get("kraj", ""))
    s_competition = score_competition(row.get("competition_density", 0.5))

    total = (
        WEIGHTS["dotace"]      * s_dotace +
        WEIGHTS["size"]        * s_size +
        WEIGHTS["vz_gap"]      * s_vz +
        WEIGHTS["region"]      * s_region +
        WEIGHTS["competition"] * s_competition
    )

    approach = classify_approach(row)

    return {
        "score_total":       round(total, 1),
        "score_dotace":      round(s_dotace      * WEIGHTS["dotace"], 1),
        "score_size":        round(s_size         * WEIGHTS["size"], 1),
        "score_vz_gap":      round(s_vz           * WEIGHTS["vz_gap"], 1),
        "score_region":      round(s_region        * WEIGHTS["region"], 1),
        "score_competition": round(s_competition   * WEIGHTS["competition"], 1),
        "pristup":           approach,
        "pristup_label":     approach_label(approach),
    }


def assign_priority(score: float) -> str:
    if score >= PRIORITY_A_MIN:
        return "A"
    elif score >= PRIORITY_B_MIN:
        return "B"
    else:
        return "C"


def score_all_schools(df: pd.DataFrame) -> pd.DataFrame:
    """Aplikuje scoring na celý DataFrame škol."""
    print(f"[Scoring] Počítám skóre pro {len(df)} škol...")

    score_rows = df.apply(compute_school_score, axis=1)
    score_df   = pd.DataFrame(score_rows.tolist(), index=df.index)

    df = pd.concat([df, score_df], axis=1)
    df["priorita"] = df["score_total"].apply(assign_priority)
    df = df.sort_values("score_total", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    counts   = df["priorita"].value_counts()
    approach = df["pristup"].value_counts()

    print(f"[Scoring] Hotovo!")
    print(f"  Priorita A (osobní návštěva):  {counts.get('A', 0):4d} škol")
    print(f"  Priorita B (email outreach):   {counts.get('B', 0):4d} škol")
    print(f"  Priorita C (archiv):           {counts.get('C', 0):4d} škol")
    print(f"  Přístup PM (poptávka):         {approach.get('PM', 0):4d} škol")
    print(f"  Přístup VZ (tendr):            {approach.get('VZ', 0):4d} škol")
    print(f"  Přístup OBA (hvězdy):          {approach.get('OBA', 0):4d} škol")

    return df


def export_visit_list(df: pd.DataFrame, output_path: Path = None) -> pd.DataFrame:
    """Exportuje priorita-A školy seřazené pro efektivní objíždění."""
    a_schools = df[df["priorita"] == "A"].copy()

    # Nejdřív "OBA" (hvězdy), pak "PM" (rychlé příležitosti), pak "VZ"
    order = {"OBA": 0, "PM": 1, "VZ": 2}
    a_schools["_sort"] = a_schools["pristup"].map(order).fillna(3)
    a_schools = a_schools.sort_values(["_sort", "score_total"], ascending=[True, False])
    a_schools = a_schools.drop(columns=["_sort"])

    cols = [
        "rank", "nazev", "obec", "okres", "kraj",
        "pocet_zaku", "email", "telefon", "web",
        "score_total", "priorita", "pristup", "pristup_label",
        "dotace_had", "dotace_last_year",
        "had_vz_nabytek", "last_vz_year",
        "score_dotace", "score_size", "score_vz_gap",
        "score_region", "score_competition",
    ]
    cols_available = [c for c in cols if c in a_schools.columns]
    result = a_schools[cols_available]

    if output_path:
        result.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"[Scoring] Visit list: {len(result)} škol → {output_path}")

    return result


if __name__ == "__main__":
    # Testovací scénáře pokrývající různé situace
    test_df = pd.DataFrame([
        # Hvězda — velká škola, dotace 2 roky zpět, přezrálá VZ, prioritní kraj
        {"nazev": "ZŠ Kolín — hvězda", "pocet_zaku": 480, "kraj": "Středočeský kraj",
         "dotace_had": True, "dotace_last_year": 2024,
         "had_vz_nabytek": True, "last_vz_year": 2017, "competition_density": 0.3},

        # PM cíl — střední škola, bez VZ (nakupuje přes poptávku), Praha
        {"nazev": "ZŠ Praha — poptávka", "pocet_zaku": 220, "kraj": "Praha",
         "dotace_had": False,
         "had_vz_nabytek": False, "competition_density": 0.8},

        # VZ cíl — velká škola, dotace 3 roky zpět, připravuje tendr
        {"nazev": "SŠ České Budějovice — tendr", "pocet_zaku": 550, "kraj": "Jihočeský kraj",
         "dotace_had": True, "dotace_last_year": 2023,
         "had_vz_nabytek": True, "last_vz_year": 2015, "competition_density": 0.2},

        # Slabý cíl — malá vesnická škola, Morava, bez signálů
        {"nazev": "ZŠ Vesnická — Morava", "pocet_zaku": 75, "kraj": "Jihomoravský kraj",
         "dotace_had": False,
         "had_vz_nabytek": False, "competition_density": 0.1},

        # Zajímavá bez dotace — velká škola, Praha, přezrálá VZ
        {"nazev": "ZŠ Praha Velká — přezrálá", "pocet_zaku": 680, "kraj": "Praha",
         "dotace_had": False,
         "had_vz_nabytek": True, "last_vz_year": 2016, "competition_density": 0.7},
    ])

    result = score_all_schools(test_df)
    print()
    print(result[[
        "nazev", "pocet_zaku", "score_total", "priorita", "pristup",
        "score_dotace", "score_size", "score_vz_gap", "score_region"
    ]].to_string(index=False))

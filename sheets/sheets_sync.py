"""
Google Sheets Sync — propíše data ze DataFrames do Google Sheets
Používá OAuth 2.0 (Desktop app) — nevyžaduje Service Account.

Nastavení (jednorázové):
  1. console.cloud.google.com → projekt brezka-crm
  2. APIs & Services → Enable: Google Sheets API + Google Drive API
  3. Credentials → Create → OAuth 2.0 Client ID → Desktop app → Download JSON
  4. Ulož jako 'oauth_credentials.json' do složky projektu
  5. První spuštění otevře prohlížeč → přihlas se → token se uloží lokálně
"""

import os
import json
import pandas as pd
import gspread
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound
from gspread_dataframe import set_with_dataframe
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pathlib import Path
import pickle

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SPREADSHEET_NAME, SHEETS

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

OAUTH_CREDENTIALS_PATH = Path(__file__).parent.parent / "oauth_credentials.json"
TOKEN_PATH             = Path(__file__).parent.parent / "token.pickle"


def get_client() -> gspread.Client:
    """
    Vytvoří autentizovaného gspread klienta přes OAuth 2.0.
    První spuštění: otevře prohlížeč pro přihlášení (jednorázové).
    Další spuštění: použije uložený token automaticky.
    """
    if not OAUTH_CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            f"OAuth credentials nenalezeny: {OAUTH_CREDENTIALS_PATH}\n"
            "Stáhni OAuth 2.0 Client ID JSON z Google Cloud Console\n"
            "(Credentials → Create → OAuth 2.0 Client IDs → Desktop app → Download JSON)\n"
            "a ulož jako 'oauth_credentials.json' do složky projektu."
        )

    creds = None

    # Načti uložený token pokud existuje
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)

    # Obnov nebo získej nový token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[Sheets] Obnovuji přístupový token...")
            creds.refresh(Request())
        else:
            print("[Sheets] První přihlášení — otevírám prohlížeč...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(OAUTH_CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Ulož token pro příští spuštění
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
        print("[Sheets] Token uložen — příště se prohlížeč neotevře.")

    return gspread.authorize(creds)


def get_or_create_spreadsheet(client: gspread.Client) -> gspread.Spreadsheet:
    """Otevře nebo vytvoří Google Sheets soubor."""
    try:
        ss = client.open(SPREADSHEET_NAME)
        print(f"[Sheets] Otevřen: {SPREADSHEET_NAME}")
    except SpreadsheetNotFound:
        ss = client.create(SPREADSHEET_NAME)
        print(f"[Sheets] Vytvořen nový: {SPREADSHEET_NAME}")
        # Sdílej s editorem (přidej email ručně nebo nastav sharing)
    return ss


def get_or_create_worksheet(ss: gspread.Spreadsheet, name: str, rows: int = 5000) -> gspread.Worksheet:
    """Otevře nebo vytvoří záložku v Sheets."""
    try:
        ws = ss.worksheet(name)
    except WorksheetNotFound:
        ws = ss.add_worksheet(title=name, rows=rows, cols=50)
        print(f"[Sheets] Vytvořena záložka: {name}")
    return ws


def sync_schools_db(df: pd.DataFrame) -> None:
    """Nahraje databázi škol do záložky Školy_DB."""
    print(f"[Sheets] Nahrávám {len(df)} škol do {SHEETS['db']}...")

    client = get_client()
    ss = get_or_create_spreadsheet(client)
    ws = get_or_create_worksheet(ss, SHEETS["db"], rows=max(5000, len(df) + 10))

    # Vyber a uspořádej sloupce pro přehledné zobrazení
    display_cols = [
        "rank", "priorita", "score_total",
        "nazev", "obec", "okres", "kraj",
        "pocet_zaku",
        "email", "telefon", "web",
        "zrizovatel", "izo", "ico",
        "dotace_had", "dotace_last_year", "dotace_total_czk",
        "had_vz_nabytek", "last_vz_year",
        "competition_count",
        "score_size", "score_dotace", "score_vz_gap",
        "score_competition", "score_distance",
        "lat", "lon",
    ]
    cols = [c for c in display_cols if c in df.columns]
    export_df = df[cols].copy()

    # Konverze bool → string pro Sheets
    for col in export_df.select_dtypes(include="bool").columns:
        export_df[col] = export_df[col].map({True: "ANO", False: "NE"})

    # Konverze listů → string
    for col in export_df.columns:
        if export_df[col].apply(lambda x: isinstance(x, list)).any():
            export_df[col] = export_df[col].apply(
                lambda x: ", ".join(x) if isinstance(x, list) else x
            )

    ws.clear()
    set_with_dataframe(ws, export_df, include_index=False)
    _format_header(ws)
    _apply_priority_colors(ws, export_df)

    print(f"[Sheets] Hotovo! URL: {ss.url}")


def sync_vz_monitor(vz_df: pd.DataFrame) -> None:
    """Nahraje nové VZ do záložky VZ_Monitor s deduplikací a formátováním."""
    if vz_df.empty:
        print("[Sheets] Žádné nové VZ k nahrání.")
        return

    client = get_client()
    ss = get_or_create_spreadsheet(client)
    ws = get_or_create_worksheet(ss, SHEETS["vz"], rows=2000)

    # Načti existující VZ (aby nedošlo k duplicitám)
    existing_data = ws.get_all_records()
    existing_ids = set(r.get("id", "") for r in existing_data)

    new_vz = vz_df[~vz_df["id"].isin(existing_ids)] if "id" in vz_df.columns else vz_df

    if new_vz.empty:
        print("[Sheets] Žádné nové (deduplicated) VZ.")
        return

    # Přidej na konec (append)
    existing_df = pd.DataFrame(existing_data)
    combined = pd.concat([existing_df, new_vz], ignore_index=True)

    # Konverze bool sloupců
    for col in combined.select_dtypes(include="bool").columns:
        combined[col] = combined[col].map({True: "ANO", False: "NE"})

    ws.clear()
    set_with_dataframe(ws, combined, include_index=False)
    _format_header(ws)
    _apply_vz_colors(ws, combined)
    print(f"[Sheets] Přidáno {len(new_vz)} nových VZ (celkem {len(combined)}).")


def init_crm_sheet() -> None:
    """Inicializuje prázdnou CRM záložku se správnými sloupci."""
    client = get_client()
    ss = get_or_create_spreadsheet(client)
    ws = get_or_create_worksheet(ss, SHEETS["crm"], rows=3000)

    # Zkontroluj jestli je prázdná
    if ws.row_count > 1 and ws.cell(1, 1).value:
        print(f"[Sheets] CRM záložka již existuje, přeskakuji init.")
        return

    headers = [
        "ID_školy", "Název školy", "Obec", "Kraj",
        "Kontaktní osoba", "Email", "Telefon",
        "Stav pipeline",       # Nový / Osloveno / Reakce / Nabídka / Vyhráno / Prohráno / Odloženo
        "Datum prvního kontaktu",
        "Způsob kontaktu",     # Email / Telefon / Osobní návštěva
        "Datum posledního kontaktu",
        "Výsledek posledního kontaktu",
        "Datum následujícího kroku",
        "Popis následujícího kroku",
        "Odhadovaná hodnota zakázky (Kč)",
        "Poznámky",
        "Přiřazeno komu",
        "Skóre priority",
        "Odkaz na VZ",
        "Stav VZ",
    ]

    ws.append_row(headers)
    _format_header(ws)
    print(f"[Sheets] CRM záložka inicializována s {len(headers)} sloupci.")


def sync_dashboard(schools_df: pd.DataFrame, vz_df: pd.DataFrame = None) -> None:
    """
    Vytvoří/aktualizuje záložku Dashboard s klíčovými metrikami a top školami.
    """
    from datetime import datetime as dt

    client = get_client()
    ss = get_or_create_spreadsheet(client)
    ws = get_or_create_worksheet(ss, SHEETS["dashboard"], rows=200)
    ws.clear()

    now_str = dt.now().strftime("%d.%m.%Y %H:%M")

    # ── Základní statistiky ────────────────────────────────────
    total = len(schools_df)
    a_count = int((schools_df.get("priorita", pd.Series()) == "A").sum()) if "priorita" in schools_df.columns else 0
    b_count = int((schools_df.get("priorita", pd.Series()) == "B").sum()) if "priorita" in schools_df.columns else 0
    c_count = int((schools_df.get("priorita", pd.Series()) == "C").sum()) if "priorita" in schools_df.columns else 0
    avg_score = round(schools_df["score_total"].mean(), 1) if "score_total" in schools_df.columns else 0
    geo_count = int(schools_df["lat"].notna().sum()) if "lat" in schools_df.columns else 0

    pm_count = int((schools_df.get("pristup", pd.Series()) == "PM").sum()) if "pristup" in schools_df.columns else 0
    vz_count_db = int((schools_df.get("pristup", pd.Series()) == "VZ").sum()) if "pristup" in schools_df.columns else 0
    oba_count = int((schools_df.get("pristup", pd.Series()) == "OBA").sum()) if "pristup" in schools_df.columns else 0

    vz_alert_count = len(vz_df) if vz_df is not None and not vz_df.empty else 0
    vz_skoly_count = int(vz_df["je_skola"].sum()) if vz_df is not None and not vz_df.empty and "je_skola" in vz_df.columns else 0

    rows = [
        ["🔨 BREZKA CRM — Dashboard", ""],
        [f"Aktualizováno: {now_str}", ""],
        ["", ""],
        ["📊 DATABÁZE ŠKOL", ""],
        ["Celkem škol (ZŠ+SŠ):", total],
        ["Geokódováno:", f"{geo_count}/{total}"],
        ["Průměrné skóre:", avg_score],
        ["", ""],
        ["🎯 PRIORITY", ""],
        ["Priorita A — osobní návštěva:", a_count],
        ["Priorita B — email outreach:", b_count],
        ["Priorita C — archiv:", c_count],
        ["", ""],
        ["💼 DOPORUČENÝ PŘÍSTUP", ""],
        ["🟢 PM (poptávkové řízení — oslovit ASAP):", pm_count],
        ["⭐ OBA (velký potenciál — tendr i poptávka):", oba_count],
        ["🔵 VZ (tendr — budovat vztah):", vz_count_db],
        ["", ""],
        ["📋 VZ MONITOR (aktuální alert)", ""],
        ["Zakázek v alertu:", vz_alert_count],
        ["z toho školy:", vz_skoly_count],
        ["", ""],
    ]

    ws.append_rows(rows)

    # ── Top 10 škol Priority A ─────────────────────────────────
    if "priorita" in schools_df.columns and "score_total" in schools_df.columns:
        top_a = schools_df[schools_df["priorita"] == "A"].head(10)
        ws.append_row(["🏆 TOP 10 ŠKOL — PRIORITA A", ""])
        header = ["#", "Škola", "Obec", "Kraj", "Skóre", "Přístup", "Žáků", "Email"]
        ws.append_row(header)

        for i, (_, row) in enumerate(top_a.iterrows(), 1):
            ws.append_row([
                i,
                str(row.get("nazev", "")),
                str(row.get("obec", "")),
                str(row.get("kraj", "")),
                row.get("score_total", ""),
                str(row.get("pristup", "")),
                int(row.get("pocet_zaku", 0)) if row.get("pocet_zaku") else "",
                str(row.get("email", "")),
            ])

    # ── Top 5 VZ alertů ze škol ───────────────────────────────
    if vz_df is not None and not vz_df.empty:
        ws.append_row(["", ""])
        ws.append_row(["📌 NEJNOVĚJŠÍ VZ ZE ŠKOL", ""])
        vz_header = ["Název zakázky", "Zadavatel", "Hodnota Kč", "Datum", "Odkaz"]
        ws.append_row(vz_header)

        skola_vz = vz_df[vz_df.get("je_skola", False) == True] if "je_skola" in vz_df.columns else vz_df
        skola_vz = skola_vz.head(10)

        for _, row in skola_vz.iterrows():
            ws.append_row([
                str(row.get("nazev", ""))[:80],
                str(row.get("zadavatel", ""))[:50],
                row.get("hodnota_czk", ""),
                str(row.get("datum", "")),
                str(row.get("odkaz", "")),
            ])

    # Formátování hlavičky (řádek 1)
    _format_header(ws)

    # Tučné sekce
    try:
        ws.format("A4", {"textFormat": {"bold": True}})
        ws.format("A9", {"textFormat": {"bold": True}})
        ws.format("A14", {"textFormat": {"bold": True}})
        ws.format("A19", {"textFormat": {"bold": True}})
    except Exception:
        pass

    print(f"[Sheets] Dashboard aktualizován — {a_count} škol priority A, {vz_alert_count} VZ v alertu.")


def get_crm_data() -> pd.DataFrame:
    """Stáhne aktuální CRM data ze Sheets."""
    client = get_client()
    ss = get_or_create_spreadsheet(client)
    ws = get_or_create_worksheet(ss, SHEETS["crm"])
    records = ws.get_all_records()
    return pd.DataFrame(records)


def upsert_crm_contact(school_row: pd.Series, stav: str = "Osloveno", poznamka: str = "") -> str:
    """
    Přidá nebo aktualizuje školu v CRM záložce.
    Vrací 'added' nebo 'updated'.
    """
    from datetime import datetime as dt
    client = get_client()
    ss = get_or_create_spreadsheet(client)
    ws = get_or_create_worksheet(ss, SHEETS["crm"])

    izo = str(school_row.get("izo", ""))
    nazev = str(school_row.get("nazev", ""))
    today = dt.now().strftime("%Y-%m-%d")

    # Hledej existující záznam dle IZO
    existing = ws.get_all_records()
    for i, rec in enumerate(existing, start=2):  # start=2 (řádek 1 = header)
        if str(rec.get("ID_školy", "")) == izo or str(rec.get("Název školy", "")) == nazev:
            # Aktualizuj existující řádek — sloupce dle init_crm_sheet
            ws.update_cell(i, 8,  stav)   # Stav pipeline
            ws.update_cell(i, 11, today)  # Datum posledního kontaktu
            if poznamka:
                ws.update_cell(i, 16, poznamka)  # Poznámky
            return "updated"

    # Přidej nový řádek
    new_row = [
        izo,
        nazev,
        str(school_row.get("obec", "")),
        str(school_row.get("kraj", "")),
        str(school_row.get("reditel", "")),
        str(school_row.get("email", "")),
        str(school_row.get("telefon", "")),
        stav,
        today,   # datum prvního kontaktu
        "Email",
        today,   # datum posledního kontaktu
        "",
        "",
        "",
        "",
        poznamka,
        "",
        str(school_row.get("score_total", "")),
        "",
        "",
    ]
    ws.append_row(new_row)
    return "added"


def get_contacted_izo_set() -> set:
    """Vrátí set IZO škol, které jsou v CRM (byly osloveny)."""
    try:
        crm = get_crm_data()
        if crm.empty or "ID_školy" not in crm.columns:
            return set()
        return set(crm["ID_školy"].astype(str).tolist())
    except Exception:
        return set()


def add_school_to_crm(school_row: pd.Series) -> None:
    """Přidá školu do CRM pipeline (pokud tam ještě není)."""
    client = get_client()
    ss = get_or_create_spreadsheet(client)
    ws = get_or_create_worksheet(ss, SHEETS["crm"])

    # Zkontroluj duplicitu dle IZO nebo názvu
    existing = ws.findall(str(school_row.get("nazev", "")))
    if existing:
        print(f"[Sheets] Škola '{school_row.get('nazev')}' je již v CRM.")
        return

    new_row = [
        str(school_row.get("izo", "")),
        str(school_row.get("nazev", "")),
        str(school_row.get("obec", "")),
        str(school_row.get("kraj", "")),
        "",   # kontaktní osoba
        str(school_row.get("email", "")),
        str(school_row.get("telefon", "")),
        "Nový",   # stav pipeline
        "",   # datum kontaktu
        "",   # způsob
        "", "", "", "",
        "",   # odhadovaná hodnota
        "",   # poznámky
        "",   # přiřazeno
        str(school_row.get("score_total", "")),
        "", "",
    ]
    ws.append_row(new_row)


# ─── Formátování ─────────────────────────────────────────────

def _format_header(ws: gspread.Worksheet) -> None:
    """Tučný header, zmrazený první řádek."""
    try:
        ws.format("1:1", {
            "textFormat": {"bold": True, "fontSize": 11},
            "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.7},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
        })
        ws.freeze(rows=1)
    except Exception:
        pass  # formátování není kritické


def _apply_vz_colors(ws: gspread.Worksheet, df: pd.DataFrame) -> None:
    """Obarví řádky VZ monitoru — zeleně školy, šedě ostatní."""
    if "je_skola" not in df.columns:
        return
    try:
        batch = []
        for i, je_skola in enumerate(df["je_skola"], start=2):
            je_skola_bool = str(je_skola).upper() in ("TRUE", "1", "ANO")
            color = (
                {"red": 0.85, "green": 1.0, "blue": 0.85}   # světle zelená — škola
                if je_skola_bool else
                {"red": 0.98, "green": 0.98, "blue": 0.98}  # světle šedá
            )
            batch.append({
                "range": f"{i}:{i}",
                "format": {"backgroundColor": color}
            })
        if batch:
            ws.batch_format(batch[:500])
    except Exception:
        pass


def _apply_priority_colors(ws: gspread.Worksheet, df: pd.DataFrame) -> None:
    """Obarví řádky dle priority (A=červená, B=oranžová, C=šedá)."""
    if "priorita" not in df.columns:
        return
    try:
        color_map = {
            "A": {"red": 1.0, "green": 0.85, "blue": 0.85},
            "B": {"red": 1.0, "green": 0.95, "blue": 0.8},
            "C": {"red": 0.95, "green": 0.95, "blue": 0.95},
        }
        batch = []
        for i, priority in enumerate(df["priorita"], start=2):
            color = color_map.get(str(priority), color_map["C"])
            batch.append({
                "range": f"{i}:{i}",
                "format": {"backgroundColor": color}
            })
        if batch:
            ws.batch_format(batch[:500])  # limit API calls
    except Exception:
        pass


if __name__ == "__main__":
    print("Google Sheets Sync — test připojení")
    try:
        client = get_client()
        print("✅ Připojení OK")
        ss = get_or_create_spreadsheet(client)
        print(f"✅ Spreadsheet: {ss.url}")
    except FileNotFoundError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Chyba: {e}")

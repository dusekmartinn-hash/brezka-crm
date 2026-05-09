# =============================================================
#  Brezka CRM — Konfigurace
# =============================================================

# --- Dílna ---
WORKSHOP = {
    "name": "Nupaky",
    "lat": 49.983,
    "lon": 14.617,
    "kraj": "Středočeský kraj",
}

# --- Filtrování ---
MIN_CONTRACT_VALUE_CZK = 100_000   # min. velikost zakázky

# --- Scoring váhy (součet = 100) ---
# Logika přizpůsobena realitě trhu:
#   - Dotace 2-3 roky zpět = TEPRVE SE PŘIPRAVUJE TENDR (nejsilnější signál)
#   - Bez VZ = nakupuje poptávkovým řízením (do 250-500k, osloví 3 firmy) → pro nás IDEÁLNÍ
#   - Vzdálenost nahrazena krajovým bonusem (Praha/Stč/Jihočeský = prioritní kraje)
WEIGHTS = {
    "dotace":      30,   # Dotace 2-3 roky zpět = příprava tendru (nejvyšší signal)
    "size":        25,   # Počet žáků — větší škola = větší zakázka
    "vz_gap":      20,   # VZ gap / poptávkový potenciál
    "region":      15,   # Krajový bonus (Praha/Stč/Jihočeský = prioritní)
    "competition": 10,   # Nízká konkurence v okrese (menší váha — vztah > konkurence)
}

# --- Krajový bonus (region scoring) ---
# Primární kraje = kde Matyas nejvíce obsluhuje
REGION_SCORES = {
    "Praha":              1.0,
    "Středočeský kraj":   1.0,
    "Jihočeský kraj":     0.9,
    "Plzeňský kraj":      0.6,
    "Ústecký kraj":       0.6,
    "Liberecký kraj":     0.5,
    "Královéhradecký kraj": 0.5,
    "Pardubický kraj":    0.5,
    "Kraj Vysočina":      0.4,
    "Jihomoravský kraj":  0.3,
    "Olomoucký kraj":     0.2,
    "Zlínský kraj":       0.2,
    "Moravskoslezský kraj": 0.2,
    "Karlovarský kraj":   0.4,
}

# --- Poptávkové řízení thresholds ---
# Školy nakupují přímo (bez VZ) do těchto hodnot
PRIMY_NAKUP_MAX_CZK    = 500_000   # některé školy/zřizovatelé až 500k
PRIMY_NAKUP_TYPICAL_CZK = 250_000  # typicky do 250k

# --- Typ obchodního přístupu (přiřazen automaticky) ---
# "PM" = Poptávkové řízení (rychlé, 100-500k, oslovit ASAP)
# "VZ" = Velký tendr (připravovat 1-2 roky dopředu, budovat vztah)
# "OBA" = Škola může být oběma způsoby

# --- Priority thresholds ---
# Pozn.: bez dotačních dat max score = 60. S dotacemi školy dosáhnou 80-95.
# Pro v0.1 (bez dotací): A=55+, B=38+
# Pro full run (s dotacemi): A=68+, B=42+
PRIORITY_A_MIN = 55   # Osobní návštěva (sníženo pro v0.1 bez dotací)
PRIORITY_B_MIN = 38   # Email outreach

# --- Typy škol k zahrnutí ---
TARGET_SCHOOL_TYPES = [
    "Základní škola",
    "Gymnázium",
    "Střední škola",
    "Střední odborná škola",
    "Střední odborné učiliště",
    "Střední průmyslová škola",
    "Obchodní akademie",
    "Střední zdravotnická škola",
]

# --- Klíčová slova pro VZ monitoring ---
VZ_KEYWORDS = [
    "nábytek", "školní nábytek", "lavice", "stoly", "skříně",
    "žákovský nábytek", "vybavení tříd", "interiér", "sedací nábytek",
    "pracovní stoly", "knihovny", "regály", "šatní skříňky",
    "vybavení učebny", "vybavení školy",
]

VZ_MIN_VALUE_CZK = 100_000

# --- CPV kódy (veřejné zakázky — kategorie nábytku) ---
CPV_CODES = [
    "39100000",  # Nábytek
    "39160000",  # Školní nábytek
    "39130000",  # Kancelářský nábytek
    "39150000",  # Různý nábytek a zařízení
    "39120000",  # Stoly, skříně, pracovní stoly a knihovny
]

# --- Google Sheets ---
SPREADSHEET_NAME = "Brezka CRM — Školy"
SHEETS = {
    "db":        "Školy_DB",
    "crm":       "CRM",
    "vz":        "VZ_Monitor",
    "dashboard": "Dashboard",
}

# --- MŠMT Open Data ---
MSMT_OPENDATA_URL = "https://rejstriky.msmt.cz/opendata/vrejstriky.xml.zip"
MSMT_STATS_URL    = "https://toiler.uiv.cz/rocenka/rocenka.asp"  # výkazy žáků

# --- NEN/NIPEZ VZ ---
NEN_RSS_URL = "https://nen.nipez.cz/rss/zakazky"
NEN_SEARCH_URL = "https://nen.nipez.cz/profily"

# --- Monitor státní pokladny (dotace) ---
MONITOR_API_URL = "https://monitor.statnipokladna.cz/api/opendata"

# --- ARES (konkurence — truhlářství) ---
ARES_API_URL = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty"
ARES_NACE_TRUHLARSTVI = "16230"  # NACE: Výroba ostatních výrobků ze dřeva

# --- Geokódování ---
GEOCODING_PROVIDER = "nominatim"  # zdarma, Openstreetmap
GEOCODING_USER_AGENT = "brezka-crm/1.0"

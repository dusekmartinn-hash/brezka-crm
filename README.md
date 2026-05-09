# Brezka CRM — Školní nábytek

CRM a scoring systém pro oslovování ZŠ a SŠ v ČR.

## Rychlý start

```bash
# 1. Nainstaluj závislosti
pip install -r requirements.txt

# 2. První spuštění (bez Google Sheets — jen lokální výstup)
python main.py --skip-sheets

# 3. S Google Sheets (vyžaduje credentials.json)
python main.py

# 4. Jen vygenerovat mapu z existujících dat
python main.py --map-only

# 5. VZ Monitor (spouštět denně)
python main.py --vz-monitor
```

## Google Sheets nastavení (jednorázové)

1. Jdi na [console.cloud.google.com](https://console.cloud.google.com)
2. Vytvoř projekt → **APIs & Services** → zapni **Google Sheets API** + **Google Drive API**
3. **IAM → Service Accounts** → Create → stáhni JSON klíč → ulož jako `credentials.json`
4. V Google Sheets → Share → přidej email service accountu jako Editor

## Výstupy

| Soubor | Popis |
|---|---|
| `output/skoly_scored.csv` | Všechny školy se skóre |
| `output/visit_list_priorita_A.csv` | TOP školy pro osobní návštěvy |
| `output/brezka_mapa_skol.html` | Interaktivní mapa (otevři v prohlížeči) |
| `output/vz_alert_YYYYMMDD.csv` | Nové relevantní VZ |

## Scoring model

| Faktor | Váha | Popis |
|---|---|---|
| Velikost školy | 30 bodů | Počet žáků |
| Historie dotací | 25 bodů | Dotace 1-3 roky zpět |
| VZ gap | 20 bodů | Dlouho nenakoupili nábytek |
| Nízká konkurence | 15 bodů | Málo truhlářství v okrese |
| Vzdálenost | 10 bodů | Blízkost Nupaků |

**Priorita A (70+):** Osobní návštěva  
**Priorita B (45-69):** Email outreach  
**Priorita C (<45):** Archiv

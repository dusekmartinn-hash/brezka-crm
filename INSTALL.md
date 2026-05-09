# Brezka CRM — instalace

## Rychlý start (3 kroky)

```bash
# 1. Rozbal ZIP a vstup do složky
cd BrezkaCRM

# 2. Nainstaluj závislosti
pip install -r requirements.txt

# 3. Spusť
streamlit run app.py --server.headless true
```

Otevře se v prohlížeči na http://localhost:8501

## Poznamky
- Python 3.9+
- Google Sheets sync vyžaduje oauth_credentials.json (bez něj CRM pipeline nefunguje, ale app se zobrazí)

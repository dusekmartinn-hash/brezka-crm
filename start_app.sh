#!/bin/bash
# Brezka CRM — spuštění Streamlit aplikace
# Použití: bash start_app.sh

cd "$(dirname "$0")"

echo "🔨 Brezka CRM — spouštím aplikaci..."
echo "   Otevři v prohlížeči: http://localhost:8501"
echo "   Ukončení: Ctrl+C"
echo ""

python3 -m streamlit run app.py \
  --server.port 8501 \
  --server.headless true \
  --browser.gatherUsageStats false \
  --theme.primaryColor "#e74c3c" \
  --theme.backgroundColor "#ffffff" \
  --theme.secondaryBackgroundColor "#f8f9fa"

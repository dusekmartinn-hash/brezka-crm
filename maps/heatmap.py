"""
Heatmap — interaktivní mapa škol + heatmapa truhlářství (konkurence)
Výstup: HTML soubor otevíratelný v prohlížeči (Folium, zdarma)
"""

import folium
import pandas as pd
from folium.plugins import HeatMap, MarkerCluster, Search
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import WORKSHOP

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Barvy priorit
PRIORITY_COLORS = {
    "A": "#e74c3c",    # červená — osobní návštěva
    "B": "#f39c12",    # oranžová — email
    "C": "#95a5a6",    # šedá — archiv
}

PRIORITY_ICONS = {
    "A": "star",
    "B": "info-sign",
    "C": "minus",
}


def build_school_map(
    schools_df: pd.DataFrame,
    competitors_df: pd.DataFrame = None,
    output_name: str = "brezka_mapa_skol.html",
) -> Path:
    """
    Vytvoří interaktivní HTML mapu:
      - Školy označené dle priority (A/B/C)
      - Heatmapa truhlářství (konkurence)
      - Dílna Matyas v Nupakách
      - Filtry dle kraje a priority
    """
    # Centrum mapy = Nupaky / střed ČR
    center = [WORKSHOP["lat"], WORKSHOP["lon"]]

    m = folium.Map(
        location=center,
        zoom_start=8,
        tiles="CartoDB positron",
        control_scale=True,
    )

    # ── 1. Vrstva: dílna ────────────────────────────────────────
    folium.Marker(
        location=[WORKSHOP["lat"], WORKSHOP["lon"]],
        popup=folium.Popup(
            f"<b>🔨 Dílna: {WORKSHOP['name']}</b><br>Výchozí bod tras",
            max_width=200
        ),
        icon=folium.Icon(color="darkblue", icon="home", prefix="fa"),
        tooltip="Dílna Nupaky",
    ).add_to(m)

    # ── 2. Vrstva: školy (dle priority) ─────────────────────────
    priority_layers = {}
    for p, color in PRIORITY_COLORS.items():
        layer = folium.FeatureGroup(name=f"Priorita {p} ({_priority_label(p)})")
        priority_layers[p] = layer

    if "lat" not in schools_df.columns:
        schools_df["lat"] = None
        schools_df["lon"] = None
    schools_with_coords = schools_df.dropna(subset=["lat", "lon"]).copy()

    for _, row in schools_with_coords.iterrows():
        priority = row.get("priorita", "C")
        color = PRIORITY_COLORS.get(priority, "#95a5a6")
        icon_name = PRIORITY_ICONS.get(priority, "minus")

        popup_html = _build_school_popup(row)
        tooltip = f"{row.get('nazev', '')} ({row.get('pocet_zaku', '?')} žáků)"

        marker = folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=_radius_from_size(row.get("pocet_zaku", 100)),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=tooltip,
        )
        marker.add_to(priority_layers.get(priority, priority_layers["C"]))

    for layer in priority_layers.values():
        layer.add_to(m)

    # ── 3. Vrstva: heatmapa konkurence (truhlářství) ─────────────
    if competitors_df is not None and not competitors_df.empty:
        comp_with_coords = competitors_df.dropna(subset=["lat", "lon"])
        heat_data = comp_with_coords[["lat", "lon"]].values.tolist()

        if heat_data:
            heat_layer = folium.FeatureGroup(name="Hustota truhlářství (konkurence)")
            HeatMap(
                heat_data,
                min_opacity=0.2,
                max_zoom=12,
                radius=25,
                blur=20,
                gradient={0.2: "blue", 0.5: "lime", 0.8: "yellow", 1.0: "red"},
            ).add_to(heat_layer)
            heat_layer.add_to(m)

    # ── 4. Legenda ───────────────────────────────────────────────
    legend_html = _build_legend(schools_df)
    m.get_root().html.add_child(folium.Element(legend_html))

    # ── 5. Layer control — collapsed aby nepřekrýval ─────────────
    folium.LayerControl(collapsed=True).add_to(m)

    # ── 6. Statistiky — pod layer controlem ──────────────────────
    stats_html = _build_stats_overlay(schools_df)
    m.get_root().html.add_child(folium.Element(stats_html))

    # Ulož
    output_path = OUTPUT_DIR / output_name
    m.save(str(output_path))
    print(f"[Mapa] Uložena: {output_path}")
    return output_path


def _build_school_popup(row: pd.Series) -> str:
    """HTML popup pro školu."""
    score = row.get("score_total", 0)
    priorita = row.get("priorita", "?")
    dotace = "✅ Ano" if row.get("dotace_had") else "❌ Ne"
    dotace_year = row.get("dotace_last_year", "")
    vz = "✅ Ano" if row.get("had_vz_nabytek") else "Neznámá"
    vz_year = row.get("last_vz_year", "")
    email = row.get("email", "")
    telefon = row.get("telefon", "")

    html = f"""
    <div style="font-family: Arial; min-width: 250px;">
        <h4 style="margin:0 0 8px 0; color:#2c3e50;">{row.get('nazev', '')}</h4>
        <p style="margin:2px 0;"><b>Obec:</b> {row.get('obec', '')} ({row.get('kraj', '')})</p>
        <p style="margin:2px 0;"><b>Žáků:</b> {int(row.get('pocet_zaku', 0))}</p>
        <hr style="margin:6px 0;">
        <p style="margin:2px 0;"><b>Skóre:</b>
            <span style="color:{'#e74c3c' if priorita=='A' else '#f39c12' if priorita=='B' else '#7f8c8d'}; font-weight:bold;">
                {score} / 100 — Priorita {priorita}
            </span>
        </p>
        <p style="margin:2px 0;"><b>Dotace (1-3 roky):</b> {dotace} {f'({dotace_year})' if dotace_year else ''}</p>
        <p style="margin:2px 0;"><b>Poslední VZ nábytek:</b> {vz} {f'({vz_year})' if vz_year else ''}</p>
        <hr style="margin:6px 0;">
        {'<p style="margin:2px 0;"><b>Email:</b> <a href="mailto:' + str(email) + '">' + str(email) + '</a></p>' if email and str(email) not in ('nan','') else ''}
        {'<p style="margin:2px 0;"><b>Tel:</b> ' + str(telefon) + '</p>' if telefon and str(telefon) not in ('nan','') else ''}
        <p style="margin:6px 0 0 0;">
            <a href="https://www.google.com/maps/dir/{WORKSHOP['lat']},{WORKSHOP['lon']}/{row.get('lat', '')},{row.get('lon', '')}"
               target="_blank" style="color:#3498db;">🗺️ Trasa z dílny</a>
        </p>
    </div>
    """
    return html


def _build_legend(schools_df: pd.DataFrame) -> str:
    """HTML legenda pro mapu."""
    counts = schools_df["priorita"].value_counts() if "priorita" in schools_df.columns else {}
    return f"""
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: white; padding: 15px; border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3); font-family: Arial; font-size: 13px;">
        <b style="font-size:14px;">📊 Brezka CRM — Školy</b><br><br>
        <span style="color:#e74c3c;">●</span> <b>Priorita A</b> — osobní návštěva
            <span style="color:#666;">({counts.get('A', 0)} škol)</span><br>
        <span style="color:#f39c12;">●</span> <b>Priorita B</b> — email outreach
            <span style="color:#666;">({counts.get('B', 0)} škol)</span><br>
        <span style="color:#95a5a6;">●</span> <b>Priorita C</b> — archiv
            <span style="color:#666;">({counts.get('C', 0)} škol)</span><br><br>
        <span style="color:#3498db;">■</span> Heatmapa = hustota truhlářství<br>
        <span style="font-size:11px; color:#999;">Větší kruh = více žáků</span>
    </div>
    """


def _build_stats_overlay(schools_df: pd.DataFrame) -> str:
    """Statistický overlay — vlevo nahoře vedle zoom buttonů."""
    total = len(schools_df)
    a_count = (schools_df["priorita"] == "A").sum() if "priorita" in schools_df.columns else 0
    b_count = (schools_df["priorita"] == "B").sum() if "priorita" in schools_df.columns else 0
    avg_score = round(schools_df["score_total"].mean(), 1) if "score_total" in schools_df.columns else 0
    geo_count = schools_df["lat"].notna().sum() if "lat" in schools_df.columns else 0

    return f"""
    <div style="position: fixed; bottom: 30px; right: 15px; z-index: 1000;
                background: rgba(255,255,255,0.97); padding: 14px 16px; border-radius: 10px;
                box-shadow: 0 2px 12px rgba(0,0,0,0.25); font-family: Arial; font-size: 12px;
                min-width: 175px; border-left: 4px solid #2c3e50;">
        <div style="font-size:13px; font-weight:bold; margin-bottom:8px; color:#2c3e50;">
            📊 Brezka CRM
        </div>
        <table style="border-collapse:collapse; width:100%;">
            <tr><td style="color:#555;">Celkem škol:</td><td style="text-align:right; font-weight:bold;">{total}</td></tr>
            <tr><td style="color:#e74c3c;">● Priorita A:</td><td style="text-align:right; font-weight:bold;">{a_count}</td></tr>
            <tr><td style="color:#f39c12;">● Priorita B:</td><td style="text-align:right; font-weight:bold;">{b_count}</td></tr>
            <tr><td style="color:#555;">Prům. skóre:</td><td style="text-align:right;">{avg_score}</td></tr>
            <tr><td style="color:#555;">Geokód.:</td><td style="text-align:right;">{geo_count}/{total}</td></tr>
        </table>
        <hr style="margin:8px 0; border:none; border-top:1px solid #eee;">
        <span style="color:#7f8c8d; font-size:11px;">🔨 Dílna: Nupaky</span>
        {"<br><span style='color:#e67e22; font-size:10px;'>⚠️ Body se zobrazí po geokódování</span>" if geo_count == 0 else ""}
    </div>
    """


def _radius_from_size(pocet_zaku: float) -> int:
    """Poloměr markeru dle počtu žáků."""
    n = float(pocet_zaku) if pocet_zaku else 0
    if n < 100:
        return 5
    elif n < 300:
        return 7
    elif n < 600:
        return 10
    else:
        return 14


def _priority_label(priority: str) -> str:
    labels = {"A": "osobní návštěva", "B": "email", "C": "archiv"}
    return labels.get(priority, "")


if __name__ == "__main__":
    # Test s ukázkovými daty
    test_schools = pd.DataFrame([
        {"nazev": "ZŠ Praha 2", "lat": 50.074, "lon": 14.432, "pocet_zaku": 650,
         "priorita": "A", "score_total": 82, "kraj": "Praha", "dotace_had": True,
         "dotace_last_year": 2024, "had_vz_nabytek": False, "email": "info@zs.cz"},
        {"nazev": "ZŠ Kolín", "lat": 50.03, "lon": 15.2, "pocet_zaku": 320,
         "priorita": "B", "score_total": 56, "kraj": "Středočeský kraj",
         "dotace_had": True, "dotace_last_year": 2023, "had_vz_nabytek": True,
         "last_vz_year": 2018, "email": ""},
        {"nazev": "ZŠ Beroun", "lat": 49.96, "lon": 14.07, "pocet_zaku": 180,
         "priorita": "B", "score_total": 51, "kraj": "Středočeský kraj",
         "dotace_had": False, "had_vz_nabytek": False, "email": ""},
    ])

    output = build_school_map(test_schools)
    print(f"Otevři v prohlížeči: {output}")

"""Tablero de marketing en Streamlit.

Ejecute primero `python src/main.py` desde la carpeta de la actividad y luego:

    streamlit run src/app.py
"""

from pathlib import Path

import pandas as pd

SUBMISSION_DIR = Path(__file__).resolve().parents[1] / "submission"


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(SUBMISSION_DIR / name)


def main():
    import plotly.express as px
    import streamlit as st

    st.set_page_config(page_title="Marketing dashboard", layout="wide")
    st.title("Desempeño de campañas de marketing")

    kpis = load("kpis.csv").iloc[0]
    daily = load("daily_summary.csv")
    campaigns = load("campaign_summary.csv")
    sources = load("source_summary.csv")

    st.caption(f"Periodo: {kpis['start_date']} a {kpis['end_date']}")

    cols = st.columns(5)
    cols[0].metric("Ingresos", f"${kpis['revenue']:,.0f}")
    cols[1].metric("Inversión", f"${kpis['ad_spend']:,.0f}")
    cols[2].metric("Utilidad bruta", f"${kpis['gross_profit']:,.0f}")
    cols[3].metric("ROAS", f"{kpis['roas']:.2f}")
    cols[4].metric("CTR", f"{kpis['ctr']:.1%}")

    daily["utc_date"] = pd.to_datetime(daily["utc_date"])
    monthly = (
        daily.set_index("utc_date")[["revenue", "ad_spend", "gross_profit"]]
        .resample("MS")
        .sum()
        .reset_index()
    )
    st.subheader("Evolución mensual")
    st.plotly_chart(
        px.line(
            monthly,
            x="utc_date",
            y=["revenue", "ad_spend", "gross_profit"],
            labels={"utc_date": "Mes", "value": "USD", "variable": "Métrica"},
        ),
        use_container_width=True,
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Utilidad por fuente de tráfico")
        st.plotly_chart(
            px.bar(sources, x="traffic_source", y="gross_profit"),
            use_container_width=True,
        )
    with right:
        st.subheader("ROAS por campaña")
        st.plotly_chart(
            px.bar(campaigns, x="campaign", y="roas"), use_container_width=True
        )

    st.subheader("Detalle por fuente")
    st.dataframe(sources, use_container_width=True)


if __name__ == "__main__":
    main()

"""Prepara los datos del tablero de marketing.

Lee `data/campaign_data.csv` y genera en `submission/`:

- `kpis.csv`: indicadores globales de la operación de pauta.
- `daily_summary.csv`: indicadores por día.
- `campaign_summary.csv`: indicadores por campaña (plantilla).
- `source_summary.csv`: indicadores por fuente de tráfico.

Los indicadores derivados (ROAS, CTR, CPC, RPC, CPA y margen) se recalculan a
partir de los totales de cada grupo, no como promedio de las tasas diarias.
"""

from pathlib import Path

import pandas as pd

DATA_FILE = Path("data/campaign_data.csv")
SUBMISSION_DIR = Path("submission")

SUM_COLUMNS = [
    "impressions",
    "page_clicks",
    "paid_clicks",
    "blocked_clicks",
    "ad_spend",
    "revenue",
    "gross_profit",
]


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_FILE, parse_dates=["utc_date"])
    df["campaign"] = df["template_name"]
    return df


def add_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega las métricas derivadas calculadas sobre los totales."""
    df = df.copy()
    df["ctr"] = df["page_clicks"] / df["impressions"]
    df["paid_click_rate"] = df["paid_clicks"] / df["page_clicks"]
    df["cpc"] = df["ad_spend"] / df["paid_clicks"]
    df["rpc"] = df["revenue"] / df["page_clicks"]
    df["roas"] = df["revenue"] / df["ad_spend"]
    df["profit_margin"] = df["gross_profit"] / df["revenue"]
    return df.round(4)


def summarize(df: pd.DataFrame, by: str) -> pd.DataFrame:
    grouped = df.groupby(by).agg(
        days=("utc_date", "nunique"),
        **{column: (column, "sum") for column in SUM_COLUMNS},
    )
    return add_ratios(grouped.reset_index())


def build_kpis(df: pd.DataFrame) -> pd.DataFrame:
    totals = df[SUM_COLUMNS].sum()
    kpis = add_ratios(totals.to_frame().T)
    kpis.insert(0, "start_date", df["utc_date"].min().date().isoformat())
    kpis.insert(1, "end_date", df["utc_date"].max().date().isoformat())
    kpis.insert(2, "days", df["utc_date"].nunique())
    kpis["loss_days"] = int((df["gross_profit"] < 0).sum())
    kpis["loss_day_rate"] = round(float((df["gross_profit"] < 0).mean()), 4)
    return kpis


def main():
    df = load_data()
    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)

    kpis = build_kpis(df)

    daily = summarize(df, "utc_date").drop(columns="days")
    daily["utc_date"] = daily["utc_date"].dt.date

    campaigns = summarize(df, "campaign").sort_values("gross_profit", ascending=False)
    sources = summarize(df, "traffic_source").sort_values(
        "gross_profit", ascending=False
    )

    kpis.to_csv(SUBMISSION_DIR / "kpis.csv", index=False)
    daily.to_csv(SUBMISSION_DIR / "daily_summary.csv", index=False)
    campaigns.to_csv(SUBMISSION_DIR / "campaign_summary.csv", index=False)
    sources.to_csv(SUBMISSION_DIR / "source_summary.csv", index=False)

    return kpis, daily, campaigns, sources


if __name__ == "__main__":
    main()

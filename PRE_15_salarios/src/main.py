"""Diagnóstico salarial por trayectoria (técnica vs. directiva).

Lee `data/salarios.csv` y genera en `submission/`:

- `department_pay_gap.csv`: brecha salarial entre trayectorias por
  departamento, en bruto y ajustada por categoría.
- `high_salary_by_career.csv`: proporción de salarios altos (cuartil superior
  de la empresa) por trayectoria y categoría.
- `compensation_recommendations.csv`: recomendaciones por categoría.
- `analysis_conclusions.csv`: conclusiones del análisis con su evidencia.

Idea central: comparar medianas de trayectorias sin controlar por categoría
mezcla dos efectos (diferencia de pago y diferencia de composición), porque la
trayectoria directiva se concentra en categorías altas. La brecha ajustada
compara dentro de cada categoría y pondera por la planta técnica.
"""

from pathlib import Path

import pandas as pd

DATA_FILE = Path("data/salarios.csv")
SUBMISSION_DIR = Path("submission")

SALARY = "salario_mensual_cop"
TECH = "Técnica"
MGMT = "Directiva"
CATEGORY_ORDER = ["Analista", "Profesional", "Especialista", "Senior", "Principal"]
HIGH_GAP_THRESHOLD = 0.10


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_FILE, encoding="utf-8")
    df["categoria"] = pd.Categorical(
        df["categoria"], categories=CATEGORY_ORDER, ordered=True
    )
    return df


def adjusted_gap(group: pd.DataFrame) -> float:
    """Brecha directiva/técnica dentro de cada categoría, ponderada por técnicos."""
    medians = group.pivot_table(
        index="categoria", columns="trayectoria", values=SALARY,
        aggfunc="median", observed=True,
    )
    weights = group[group["trayectoria"] == TECH].groupby(
        "categoria", observed=True
    ).size()
    if MGMT not in medians or TECH not in medians:
        return float("nan")
    gaps = (medians[MGMT] / medians[TECH] - 1).dropna()
    weights = weights.reindex(gaps.index).fillna(0)
    if weights.sum() == 0:
        return float("nan")
    return float((gaps * weights).sum() / weights.sum())


def department_pay_gap(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (gerencia, departamento), group in df.groupby(["gerencia", "departamento"]):
        tech = group[group["trayectoria"] == TECH]
        mgmt = group[group["trayectoria"] == MGMT]
        raw_gap = mgmt[SALARY].median() / tech[SALARY].median() - 1
        adj_gap = adjusted_gap(group)
        rows.append(
            {
                "gerencia": gerencia,
                "departamento": departamento,
                "employees": len(group),
                "technical_employees": len(tech),
                "management_employees": len(mgmt),
                "management_share": round(len(mgmt) / len(group), 4),
                "median_salary_technical": tech[SALARY].median(),
                "median_salary_management": mgmt[SALARY].median(),
                "raw_gap_pct": round(raw_gap, 4),
                "adjusted_gap_pct": round(adj_gap, 4),
                "composition_effect_pct": round(raw_gap - adj_gap, 4),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values("adjusted_gap_pct", ascending=False)
        .reset_index(drop=True)
    )


def high_salary_by_career(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    df = df.assign(high_salary=df[SALARY] >= threshold)
    by_category = (
        df.groupby(["trayectoria", "categoria"], observed=True)
        .agg(
            employees=(SALARY, "size"),
            high_salary_employees=("high_salary", "sum"),
            median_salary=(SALARY, "median"),
            median_experience_years=("experiencia_tecnica_anios", "median"),
        )
        .reset_index()
    )
    total = (
        df.groupby("trayectoria")
        .agg(
            employees=(SALARY, "size"),
            high_salary_employees=("high_salary", "sum"),
            median_salary=(SALARY, "median"),
            median_experience_years=("experiencia_tecnica_anios", "median"),
        )
        .reset_index()
        .assign(categoria="Total")
    )
    result = pd.concat([by_category, total], ignore_index=True)
    result["categoria"] = result["categoria"].astype(str)
    result["high_salary_rate"] = (
        result["high_salary_employees"] / result["employees"]
    ).round(4)
    result["high_salary_threshold"] = threshold
    return result


def compensation_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    medians = df.pivot_table(
        index="categoria", columns="trayectoria", values=SALARY,
        aggfunc="median", observed=True,
    )
    counts = df.pivot_table(
        index="categoria", columns="trayectoria", values=SALARY,
        aggfunc="size", observed=True,
    ).fillna(0)

    rows = []
    for categoria in medians.index:
        tech_median = medians.loc[categoria].get(TECH)
        mgmt_median = medians.loc[categoria].get(MGMT)
        tech_count = int(counts.loc[categoria].get(TECH, 0))
        if pd.isna(mgmt_median):
            gap = float("nan")
            action = "Sin referencia directiva: mantener bandas y revisar contra mercado."
            priority = "Baja"
            uplift = 0.0
        else:
            gap = mgmt_median / tech_median - 1
            if gap > HIGH_GAP_THRESHOLD:
                action = (
                    "Ajustar la banda técnica para cerrar la brecha con la "
                    "trayectoria directiva de la misma categoría."
                )
                priority = "Alta" if gap > 2 * HIGH_GAP_THRESHOLD else "Media"
                uplift = tech_count * (mgmt_median - tech_median)
            else:
                action = "Brecha dentro de tolerancia: mantener."
                priority = "Baja"
                uplift = 0.0
        rows.append(
            {
                "categoria": categoria,
                "technical_employees": tech_count,
                "median_salary_technical": tech_median,
                "median_salary_management": mgmt_median,
                "gap_pct": round(gap, 4) if pd.notna(gap) else gap,
                "priority": priority,
                "recommendation": action,
                "estimated_monthly_cost_cop": round(uplift, 0),
            }
        )
    return pd.DataFrame(rows)


def analysis_conclusions(
    df: pd.DataFrame,
    gaps: pd.DataFrame,
    high: pd.DataFrame,
    recommendations: pd.DataFrame,
) -> pd.DataFrame:
    tech = df[df["trayectoria"] == TECH][SALARY].median()
    mgmt = df[df["trayectoria"] == MGMT][SALARY].median()
    corr = df["experiencia_tecnica_anios"].corr(df[SALARY])
    totals = high[high["categoria"] == "Total"].set_index("trayectoria")
    top_gap = gaps.iloc[0]
    priority = recommendations[recommendations["priority"] != "Baja"]

    conclusions = [
        (
            "Brecha global",
            f"La mediana directiva supera a la técnica en {mgmt / tech - 1:.1%}.",
            round(mgmt / tech - 1, 4),
        ),
        (
            "Efecto de composición",
            "La mayor parte de la brecha bruta por departamento se explica porque "
            "la trayectoria directiva se concentra en categorías altas; la brecha "
            "ajustada por categoría es mucho menor.",
            round(float(gaps["composition_effect_pct"].mean()), 4),
        ),
        (
            "Brecha ajustada",
            "Dentro de la misma categoría, la trayectoria directiva gana en promedio "
            f"{gaps['adjusted_gap_pct'].mean():.1%} más que la técnica.",
            round(float(gaps["adjusted_gap_pct"].mean()), 4),
        ),
        (
            "Departamento con mayor brecha ajustada",
            f"{top_gap['departamento']} ({top_gap['gerencia']}) presenta la mayor "
            f"brecha ajustada: {top_gap['adjusted_gap_pct']:.1%}.",
            float(top_gap["adjusted_gap_pct"]),
        ),
        (
            "Acceso a salarios altos",
            "Proporción en el cuartil superior: "
            f"técnica {totals.loc[TECH, 'high_salary_rate']:.1%}, "
            f"directiva {totals.loc[MGMT, 'high_salary_rate']:.1%}.",
            float(totals.loc[MGMT, "high_salary_rate"] - totals.loc[TECH, "high_salary_rate"]),
        ),
        (
            "Experiencia",
            f"La experiencia técnica explica buena parte del salario (r = {corr:.2f}).",
            round(float(corr), 4),
        ),
        (
            "Recomendación",
            f"Priorizar ajustes en {len(priority)} categorías técnicas con brecha "
            f"mayor a {HIGH_GAP_THRESHOLD:.0%}; costo mensual estimado "
            f"{priority['estimated_monthly_cost_cop'].sum():,.0f} COP.",
            float(priority["estimated_monthly_cost_cop"].sum()),
        ),
    ]
    return pd.DataFrame(conclusions, columns=["topic", "conclusion", "evidence_value"])


def main():
    df = load_data()
    threshold = float(df[SALARY].quantile(0.75))

    gaps = department_pay_gap(df)
    high = high_salary_by_career(df, threshold)
    recommendations = compensation_recommendations(df)
    conclusions = analysis_conclusions(df, gaps, high, recommendations)

    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    gaps.to_csv(SUBMISSION_DIR / "department_pay_gap.csv", index=False)
    high.to_csv(SUBMISSION_DIR / "high_salary_by_career.csv", index=False)
    recommendations.to_csv(
        SUBMISSION_DIR / "compensation_recommendations.csv", index=False
    )
    conclusions.to_csv(SUBMISSION_DIR / "analysis_conclusions.csv", index=False)

    return gaps, high, recommendations, conclusions


if __name__ == "__main__":
    main()

import pandas as pd


def build_cohort_analysis() -> pd.DataFrame:
    """
    Una tienda quiere saber si sus clientes vuelven a comprar después de su
    primera compra. Para responder, agrupe a los clientes en cohortes según
    el mes de su primera compra y mida, mes a mes, qué proporción de cada
    cohorte vuelve a comprar. Use `data/sales.csv.gz`, que tiene una fila por
    orden con su cliente (`CustomerID`) y su fecha (`OrderDate`).

    Use estas definiciones:

    - `cohort_month`: el mes de la primera compra del cliente, escrito como
      `AAAA-MM`.
    - `period_index`: los meses transcurridos desde `cohort_month`; es 0 en el
      mes de la primera compra, 1 en el mes siguiente, y así sucesivamente.
    - `active_customers`: la cantidad de clientes distintos de la cohorte que
      compraron en ese período.
    - `cohort_size`: la cantidad de clientes de la cohorte, es decir, sus
      clientes activos en el período 0.
    - `retention_rate`: `active_customers` sobre `cohort_size`.

    Genere dos archivos en `submission/`:

    1. `cohort_retention.csv`, sin el índice de Pandas, con las columnas
       `cohort_month`, `period_index`, `active_customers`, `cohort_size` y
       `retention_rate`, y una fila por cada combinación cohorte–período
       observada, ordenadas por cohorte y período.

    2. `cohort_retention_heatmap.png`, un mapa de calor de `retention_rate`
       con una fila por cohorte (eje vertical) y una columna por período
       (eje horizontal). Muestre los valores como porcentajes. Los períodos
       que todavía no se pueden observar para una cohorte no significan
       retención cero: déjelos vacíos en el mapa.

    La función también debe retornar la tabla de retención.

    Ejemplo del formato de `cohort_retention.csv`:

        cohort_month,period_index,active_customers,cohort_size,retention_rate
        2022-01,0,100,100,1.0
        2022-01,1,26,100,0.26
        ...
    """

    import os

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    sales = pd.read_csv("data/sales.csv.gz", parse_dates=["OrderDate"])
    sales["order_month"] = sales["OrderDate"].dt.to_period("M")
    sales["cohort"] = sales.groupby("CustomerID")["order_month"].transform("min")
    sales["period_index"] = (
        (sales["order_month"].dt.year - sales["cohort"].dt.year) * 12
        + (sales["order_month"].dt.month - sales["cohort"].dt.month)
    ).astype(int)

    retention = (
        sales.groupby(["cohort", "period_index"])["CustomerID"]
        .nunique()
        .rename("active_customers")
        .reset_index()
    )
    cohort_sizes = retention.loc[retention["period_index"] == 0].set_index("cohort")[
        "active_customers"
    ]
    retention["cohort_size"] = retention["cohort"].map(cohort_sizes)
    retention["retention_rate"] = (
        retention["active_customers"] / retention["cohort_size"]
    )
    retention["cohort_month"] = retention["cohort"].dt.strftime("%Y-%m")
    retention = (
        retention.sort_values(["cohort_month", "period_index"])
        .reset_index(drop=True)[
            [
                "cohort_month",
                "period_index",
                "active_customers",
                "cohort_size",
                "retention_rate",
            ]
        ]
    )

    os.makedirs("submission", exist_ok=True)
    retention.to_csv("submission/cohort_retention.csv", index=False)

    # Mapa de calor: los períodos no observados quedan como NaN (celdas vacías).
    matrix = retention.pivot(
        index="cohort_month", columns="period_index", values="retention_rate"
    )
    masked = np.ma.masked_invalid(matrix.values)

    fig, ax = plt.subplots(figsize=(10, 6))
    cmap = plt.get_cmap("Blues").copy()
    cmap.set_bad(color="white")
    image = ax.imshow(masked, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix.values[i, j]
            if not np.isnan(value):
                ax.text(
                    j,
                    i,
                    f"{value:.0%}",
                    ha="center",
                    va="center",
                    color="white" if value > 0.6 else "black",
                    fontsize=9,
                )
    ax.set_xticks(range(matrix.shape[1]))
    ax.set_xticklabels(matrix.columns)
    ax.set_yticks(range(matrix.shape[0]))
    ax.set_yticklabels(matrix.index)
    ax.set_xlabel("Meses desde la primera compra (period_index)")
    ax.set_ylabel("Cohorte (mes de la primera compra)")
    ax.set_title("Retención de clientes por cohorte")
    colorbar = fig.colorbar(image, ax=ax)
    colorbar.ax.yaxis.set_major_formatter(
        matplotlib.ticker.PercentFormatter(xmax=1)
    )
    fig.tight_layout()
    fig.savefig("submission/cohort_retention_heatmap.png", dpi=120)
    plt.close(fig)

    return retention

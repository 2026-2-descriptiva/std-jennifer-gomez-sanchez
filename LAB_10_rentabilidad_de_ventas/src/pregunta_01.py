import pandas as pd


def pregunta_01() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Una cadena de suministros de oficina vende mucho, pero la gerencia
    sospecha que parte de esas ventas no deja utilidad. El archivo
    `data/superstore_orders.csv.gz` tiene una fila por línea de pedido, con
    el número de pedido (`Order ID`), las ventas (`Sales`), la utilidad
    (`Profit`), el descuento aplicado (`Discount`, como proporción), el
    segmento del cliente (`Customer Segment`) y la categoría del producto
    (`Product Category`). Una utilidad negativa significa que la línea se
    vendió con pérdida.

    Use estas definiciones:

    - Margen (`profit_margin`): utilidad sobre ventas.
    - Línea con pérdida: una línea cuya utilidad es negativa.
    - `loss_line_rate`: la proporción de líneas con pérdida.
    - `lost_profit`: la suma de las pérdidas de las líneas con pérdida,
      escrita como número positivo.
    - Rango de descuento (`discount_band`): `0%` si no hubo descuento,
      `1%-5%` si fue mayor que 0 y hasta 5 %, `6%-10%` si fue mayor que 5 % y
      hasta 10 %, y `más de 10%` en otro caso.

    Genere tres archivos en `submission/`, sin el índice de Pandas y con las
    columnas en el orden indicado:

    1. `profitability_summary.csv`, con una sola fila: `lines` (cantidad de
       líneas), `orders` (pedidos distintos), `sales`, `profit`,
       `profit_margin`, `loss_lines` (cantidad de líneas con pérdida),
       `loss_line_rate` y `lost_profit`.

    2. `discount_summary.csv`, con una fila por rango de descuento, en el
       orden en que se definieron arriba: `discount_band`, `lines`, `sales`,
       `profit`, `profit_margin`, `loss_line_rate` y `lost_profit`.

    3. `priority_segments.csv`, con los cinco segmentos segmento–categoría
       que más utilidad pierden: `Customer Segment`, `Product Category`,
       `lines`, `sales`, `profit`, `profit_margin` y `lost_profit`. Considere
       solamente segmentos con al menos 100 líneas y ordénelos por
       `lost_profit` de mayor a menor.

    La función también debe retornar las tres tablas, en el mismo orden.

    Ejemplo del formato de `discount_summary.csv`:

        discount_band,lines,sales,profit,profit_margin,loss_line_rate,...
        0%,166,170539.05,29472.3789,0.1728,0.488,...
        ...
    """

    import os

    # El archivo usa `;` como separador y `,` como separador decimal.
    df = pd.read_csv(
        "data/superstore_orders.csv.gz",
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
    )
    df["is_loss"] = df["Profit"] < 0
    df["loss_amount"] = -df["Profit"].where(df["is_loss"], 0.0)

    def summarize(group: pd.DataFrame) -> pd.Series:
        sales = group["Sales"].sum()
        profit = group["Profit"].sum()
        return pd.Series(
            {
                "lines": len(group),
                "sales": round(sales, 4),
                "profit": round(profit, 4),
                "profit_margin": round(profit / sales, 4),
                "loss_line_rate": round(group["is_loss"].mean(), 4),
                "lost_profit": round(group["loss_amount"].sum(), 4),
            }
        )

    # 1. Resumen general
    overall = summarize(df)
    profitability_summary = pd.DataFrame(
        [
            {
                "lines": int(overall["lines"]),
                "orders": int(df["Order ID"].nunique()),
                "sales": overall["sales"],
                "profit": overall["profit"],
                "profit_margin": overall["profit_margin"],
                "loss_lines": int(df["is_loss"].sum()),
                "loss_line_rate": overall["loss_line_rate"],
                "lost_profit": overall["lost_profit"],
            }
        ]
    )

    # 2. Resumen por rango de descuento
    bands = ["0%", "1%-5%", "6%-10%", "más de 10%"]
    discount = df["Discount"].round(6)
    df["discount_band"] = pd.Series(bands[3], index=df.index)
    df.loc[discount <= 0.10, "discount_band"] = bands[2]
    df.loc[discount <= 0.05, "discount_band"] = bands[1]
    df.loc[discount == 0, "discount_band"] = bands[0]

    discount_summary = (
        df.groupby("discount_band")
        .apply(summarize, include_groups=False)
        .reindex(bands)
        .reset_index()
    )
    discount_summary["lines"] = discount_summary["lines"].astype(int)

    # 3. Segmentos prioritarios
    keys = ["Customer Segment", "Product Category"]
    segments = df.groupby(keys).apply(summarize, include_groups=False).reset_index()
    segments["lines"] = segments["lines"].astype(int)
    priority_segments = (
        segments[segments["lines"] >= 100]
        .sort_values("lost_profit", ascending=False)
        .head(5)[keys + ["lines", "sales", "profit", "profit_margin", "lost_profit"]]
        .reset_index(drop=True)
    )

    os.makedirs("submission", exist_ok=True)
    profitability_summary.to_csv("submission/profitability_summary.csv", index=False)
    discount_summary.to_csv("submission/discount_summary.csv", index=False)
    priority_segments.to_csv("submission/priority_segments.csv", index=False)

    return profitability_summary, discount_summary, priority_segments

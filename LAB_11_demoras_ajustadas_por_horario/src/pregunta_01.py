import pandas as pd


def pregunta_01() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Una autoridad aeronáutica publica cada año un ranking de aerolíneas según
    su tasa de demora, y algunas aerolíneas se quejan de que es injusto: las
    demoras se acumulan a lo largo del día, de modo que una aerolínea con
    muchos vuelos en la tarde y la noche parece peor aunque opere igual de
    bien que las demás. Su tarea es construir un ranking que tenga en cuenta
    la mezcla de horarios de cada aerolínea.

    El archivo `data/flights_by_carrier_day_hour.csv.gz` tiene los vuelos
    nacionales entre 2006 y 2008, agregados por año, mes, día de la semana,
    hora programada de salida (`scheduled_departure_hour`) y aerolínea
    (`reporting_airline`). Use las columnas `operated_flights` (vuelos
    operados) y `delayed_departure_15_flights` (vuelos que salieron con 15
    minutos o más de demora).

    Siga estos pasos:

    1. Calcule la tasa nacional de demora de cada hora programada de salida:
       vuelos demorados sobre vuelos operados, con todas las aerolíneas
       juntas.
    2. Para cada aerolínea, calcule las demoras esperadas: en cada hora,
       multiplique sus vuelos operados por la tasa nacional de esa hora, y
       sume sobre todas las horas. Son las demoras que tendría si en cada hora
       se comportara como el promedio nacional.
    3. Divida las demoras observadas entre las esperadas. Un valor mayor que 1
       significa que la aerolínea se demora más de lo que explican sus
       horarios.

    Genere dos archivos en `submission/`, sin el índice de Pandas y con las
    columnas en el orden indicado:

    1. `hourly_delay_rates.csv`, con una fila por hora, de 0 a 23:
       `scheduled_departure_hour`, `operated_flights`,
       `delayed_departure_15_flights` y `delay_rate`.

    2. `carrier_adjusted_delays.csv`, con una fila por aerolínea:
       `reporting_airline`, `operated_flights`,
       `delayed_departure_15_flights`, `delay_rate` (la tasa sin ajustar),
       `expected_delayed_flights`, `observed_to_expected_ratio`, `crude_rank`
       y `adjusted_rank`. Incluya solamente aerolíneas con al menos 100 000
       vuelos operados. `crude_rank` es la posición según `delay_rate` y
       `adjusted_rank` la posición según `observed_to_expected_ratio`; en
       ambos, 1 es la peor aerolínea. Ordene la tabla por `adjusted_rank`.

    Compare los dos rankings: las aerolíneas que cambian de posición son las
    que el ranking sin ajustar juzga mal por sus horarios.

    La función también debe retornar las dos tablas, en el mismo orden.

    Ejemplo del formato de `carrier_adjusted_delays.csv`:

        reporting_airline,operated_flights,...,crude_rank,adjusted_rank
        EV,819223,...,1,1
        ...
    """

    import os

    df = pd.read_csv("data/flights_by_carrier_day_hour.csv.gz")
    hour = "scheduled_departure_hour"
    airline = "reporting_airline"
    operated = "operated_flights"
    delayed = "delayed_departure_15_flights"

    # 1. Tasa nacional de demora por hora
    hourly = df.groupby(hour)[[operated, delayed]].sum().reindex(range(24), fill_value=0)
    hourly["delay_rate"] = hourly[delayed] / hourly[operated]

    # 2. Demoras esperadas por aerolínea
    by_carrier_hour = df.groupby([airline, hour])[[operated, delayed]].sum().reset_index()
    by_carrier_hour["expected"] = by_carrier_hour[operated] * by_carrier_hour[hour].map(
        hourly["delay_rate"]
    )

    carriers = by_carrier_hour.groupby(airline)[[operated, delayed, "expected"]].sum()
    carriers = carriers[carriers[operated] >= 100_000].copy()
    carriers["delay_rate"] = carriers[delayed] / carriers[operated]
    carriers["expected_delayed_flights"] = carriers["expected"]
    carriers["observed_to_expected_ratio"] = carriers[delayed] / carriers["expected"]
    carriers["crude_rank"] = (
        carriers["delay_rate"].rank(ascending=False, method="first").astype(int)
    )
    carriers["adjusted_rank"] = (
        carriers["observed_to_expected_ratio"]
        .rank(ascending=False, method="first")
        .astype(int)
    )

    hourly_delay_rates = hourly.reset_index()
    hourly_delay_rates[[operated, delayed]] = hourly_delay_rates[
        [operated, delayed]
    ].astype("int64")
    hourly_delay_rates["delay_rate"] = hourly_delay_rates["delay_rate"].round(4)

    carrier_adjusted_delays = (
        carriers.reset_index()
        .sort_values("adjusted_rank")
        .reset_index(drop=True)[
            [
                airline,
                operated,
                delayed,
                "delay_rate",
                "expected_delayed_flights",
                "observed_to_expected_ratio",
                "crude_rank",
                "adjusted_rank",
            ]
        ]
    )
    carrier_adjusted_delays[[operated, delayed]] = carrier_adjusted_delays[
        [operated, delayed]
    ].astype("int64")
    carrier_adjusted_delays = carrier_adjusted_delays.round(
        {
            "delay_rate": 4,
            "expected_delayed_flights": 4,
            "observed_to_expected_ratio": 4,
        }
    )

    os.makedirs("submission", exist_ok=True)
    hourly_delay_rates.to_csv("submission/hourly_delay_rates.csv", index=False)
    carrier_adjusted_delays.to_csv(
        "submission/carrier_adjusted_delays.csv", index=False
    )

    return hourly_delay_rates, carrier_adjusted_delays

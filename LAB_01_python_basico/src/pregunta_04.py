def pregunta_04():
    """
    Cuente cuántos registros hay en cada mes, usando la fecha de la tercera
    columna (`date`). Represente el mes como un texto de dos dígitos y retorne
    una lista de tuplas `(mes, cantidad)` ordenada por el mes.

    Ejemplo del formato de la respuesta:

        [("01", 3), ("02", 4), ("03", 2), ...]
    """

    import gzip
    from collections import Counter

    with gzip.open("data/data.csv.gz", "rt", encoding="utf-8") as file:
        rows = [line.rstrip("\n").split("\t") for line in file if line.strip()]

    counts = Counter(row[2].split("-")[1] for row in rows)
    return sorted(counts.items())

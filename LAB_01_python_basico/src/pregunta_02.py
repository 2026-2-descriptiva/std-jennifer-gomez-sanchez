def pregunta_02():
    """
    Cuente cuántos registros hay para cada letra de la primera columna
    (`letter`). Retorne una lista de tuplas `(letra, cantidad)` ordenada
    alfabéticamente por la letra.

    Ejemplo del formato de la respuesta:

        [("A", 8), ("B", 7), ("C", 5), ...]
    """

    import gzip
    from collections import Counter

    with gzip.open("data/data.csv.gz", "rt", encoding="utf-8") as file:
        rows = [line.rstrip("\n").split("\t") for line in file if line.strip()]

    counts = Counter(row[0] for row in rows)
    return sorted(counts.items())

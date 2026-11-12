def pregunta_06():
    """
    La quinta columna (`metrics`) contiene pares `clave:valor` separados por
    comas. Para cada clave, encuentre el valor mínimo y el valor máximo que
    aparecen en todo el archivo. Retorne una lista de tuplas
    `(clave, mínimo, máximo)` ordenada alfabéticamente por la clave.

    Observe que el orden es mínimo y luego máximo, al contrario de la
    pregunta 5.

    Ejemplo del formato de la respuesta:

        [("aaa", 1, 9), ("bbb", 1, 9), ...]
    """

    import gzip
    from collections import defaultdict

    with gzip.open("data/data.csv.gz", "rt", encoding="utf-8") as file:
        rows = [line.rstrip("\n").split("\t") for line in file if line.strip()]

    values = defaultdict(list)
    for row in rows:
        for pair in row[4].split(","):
            key, value = pair.split(":")
            values[key].append(int(value))
    return [(key, min(vals), max(vals)) for key, vals in sorted(values.items())]

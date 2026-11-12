def pregunta_08():
    """
    Repita la pregunta 7, pero ahora cada lista de letras debe contener cada
    letra una sola vez y estar ordenada alfabéticamente. Retorne una lista de
    tuplas `(valor, letras)` ordenada por el valor.

    Ejemplo del formato de la respuesta:

        [(0, ["C"]), (1, ["B", "E"]), (2, ["A", "E"]), ...]
    """

    import gzip
    from collections import defaultdict

    with gzip.open("data/data.csv.gz", "rt", encoding="utf-8") as file:
        rows = [line.rstrip("\n").split("\t") for line in file if line.strip()]

    letters = defaultdict(set)
    for row in rows:
        letters[int(row[1])].add(row[0])
    return [(value, sorted(group)) for value, group in sorted(letters.items())]

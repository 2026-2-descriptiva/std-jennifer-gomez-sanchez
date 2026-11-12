def pregunta_01():
    """
    Calcule la suma de los valores de la segunda columna (`value`) del
    archivo `data/data.csv.gz` y retorne el resultado como un número entero.

    Ejemplo del formato de la respuesta:

        214
    """

    import gzip

    with gzip.open("data/data.csv.gz", "rt", encoding="utf-8") as file:
        rows = [line.rstrip("\n").split("\t") for line in file if line.strip()]

    return sum(int(row[1]) for row in rows)

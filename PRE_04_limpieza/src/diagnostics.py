import pandas as pd

OUTPUT_FILE = "PRE_04_limpieza/submission/ventas.csv"


def main():
    df = pd.read_csv(OUTPUT_FILE)
    series = df["purchase_date"]

    # series = series[series.str.contains(r"-\d{2}$", regex=True)]

    series = series.sort_values()
    series = series.drop_duplicates()

    print(series)
    print(len(series))


if __name__ == "__main__":
    main()
    
    
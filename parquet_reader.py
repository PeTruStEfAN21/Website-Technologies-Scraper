import pandas as pd

PARQUET_FILE = "part-00000-66e0628d-2c7f-425a-8f5b-738bcd6bf198-c000.snappy.parquet"
OUTPUT_FILE = "domenii.txt"

df = pd.read_parquet(PARQUET_FILE)
domenii = df["root_domain"].tolist()

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for domeniu in domenii:
        f.write(domeniu + "\n")

print(f"Gata! Am extras {len(domenii)} domenii in fisierul '{OUTPUT_FILE}'.")
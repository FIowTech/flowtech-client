import pandas as pd

df = pd.read_csv("vizzaccaro_692F018C-6BC9-11F0-82CE-60C72739D046_2026-09-07.csv", encoding="cp1252")

df["cpu"] = pd.to_numeric(df["cpu"], errors="coerce")
df["ram"] = pd.to_numeric(df["memoria"], errors="coerce")
df["disco"] = pd.to_numeric(df["disco"], errors="coerce")

medias = df.groupby("uuid")[["cpu", "ram", "disco"]].mean()

print(medias)
import pycountry
import pandas as pd

# Vytvoříme seznam slovníků
countries = []

for country in pycountry.countries:
    countries.append({
        "Country": country.name,
        "Code": country.alpha_2
    })

# Převedeme na DataFrame a uložíme do CSV
df = pd.DataFrame(countries)
df.to_csv("countries.csv", index=False, encoding="utf-8-sig")

print("Data byla úspěšně uložena do countries.csv")

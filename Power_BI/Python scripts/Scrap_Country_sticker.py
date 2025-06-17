import pycountry
import pandas as pd

# Create a list of dictionaries
countries = []

for country in pycountry.countries:
    countries.append({
        "Country": country.name,
        "Code": country.alpha_2
    })

# Convert to DataFrame and save to CSV
df = pd.DataFrame(countries)
df.to_csv("countries.csv", index=False, encoding="utf-8-sig")

print("Data successfully saved to countries.csv")
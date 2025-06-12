import requests
import pandas as pd
import pycountry
import time

API_KEY = "Your api coude"
for country in pycountry.countries:
    country_code = country.alpha_2
    url = f"https://api.openchargemap.io/v3/poi/?output=json&countrycode={country_code}&maxresults=200000&key={API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data:  # pokud nejsou data prázdná
                df = pd.json_normalize(data)
                filename = f"openchargemap_{country_code}.csv"
                df.to_csv(filename, index=False)
                print(f"Data for {country.name} saved to {filename}")
            else:
                print(f"No data for {country.name}")
        else:
            print(f"Failed to fetch data for {country.name} ({country.alpha_2}). Status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching data for {country.name}: {e}")

    time.sleep(15)  # Pauza 2 sekundy mezi požadavky
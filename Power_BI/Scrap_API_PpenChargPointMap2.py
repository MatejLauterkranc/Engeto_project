import requests
import pandas as pd
import pycountry
import time

API_KEY = "d1613f8c-b100-465f-a020-9f800887a141"
country_code = "CZ"
all_data = []

max_results_per_request = 5000
offset = 0

while True:
    url = f"https://api.openchargemap.io/v3/poi/?output=json&countrycode={country_code}&maxresults={max_results_per_request}&offset={offset}&key={API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if not data:  # už žádná data
                break
            all_data.extend(data)
            print(f"Fetched {len(data)} records with offset {offset}")
            offset += max_results_per_request
            time.sleep(5)  # pauza mezi požadavky
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            break
    except Exception as e:
        print(f"Error fetching data: {e}")
        break

if all_data:
    df = pd.json_normalize(all_data)
    filename = f"openchargemap_{country_code}.csv"
    df.to_csv(filename, index=False)
    print(f"Total {len(all_data)} records saved to {filename}")
else:
    print("No data found")

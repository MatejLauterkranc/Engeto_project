import requests
from bs4 import BeautifulSoup
import time
import pandas as pd

# Base URL of the website
base_url = "https://www.auto-data.net"
# URL of the initial page with brand overview
initial_url = base_url + "/en/"

# Headers for HTTP request (recommended to simulate a browser)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Lists to store data in memory for each step
all_brands = []
all_models = []
all_generations = []
all_engine_variants = []
final_dataset = [] # List to store complete specifications

# --- IMPORTANT: If the final output file already exists, it might indicate a previous successful run. ---
# For a single-file output, restarting means starting from scratch if the final file isn't complete.
# This simplified logic means no intermediate recovery points.
try:
    # Attempt to load the FINAL dataset. If it loads, the job might be considered done.
    # If you want to force a fresh run even if the final file exists, just comment out this try-except block.
    df_check = pd.read_csv("full_car_specs.csv")
    print("Found 'full_car_specs.csv'. Assuming previous run was complete. Exiting.")
    exit() # Exit if the final file already exists
except FileNotFoundError:
    print("No existing 'full_car_specs.csv' found. Starting full scraping process.")

# --- Step 1: Extract Brands ---
print(f"\n--- STEP 1: Scraping brands from {initial_url} ---")
try:
    response = requests.get(initial_url, headers=headers)
    response.raise_for_status() 
    soup = BeautifulSoup(response.text, 'html.parser')
    brands_container = soup.find('div', class_='markite')
    if brands_container:
        brand_links = brands_container.find_all('a', class_='marki_blok')
        
        print(f"  Found {len(brand_links)} potential brands.")

        for i, link in enumerate(brand_links):
            brand_name = link.find('strong').text.strip() if link.find('strong') else "N/A"
            relative_url = link.get('href')
            full_brand_url = base_url + relative_url
            if brand_name and brand_name.lower() != "all brands":
                all_brands.append({"BrandName": brand_name, "BrandURL": full_brand_url})
                print(f"  Processing brand: {brand_name} ({i+1}/{len(brand_links)})")
    else:
        print("Brand container (<div class='markite'>) not found.")
    
    print(f"  Step 1 finished. Retrieved {len(all_brands)} brands.")
    
except requests.exceptions.RequestException as e:
    print(f"Error downloading initial page: {e}")
    exit() # Exit if Step 1 fails, as subsequent steps depend on it
except Exception as e:
    print(f"An unexpected error occurred while processing the initial page: {e}")
    exit()

# --- Step 2: Extract Models for each Brand ---
if all_brands:
    print("\n--- STEP 2: Starting to download models for each brand ---")
    for i, brand_info in enumerate(all_brands):
        brand_name = brand_info['BrandName']
        brand_url = brand_info['BrandURL']
        print(f"  Downloading models for brand: {brand_name} ({i+1}/{len(all_brands)})")
        time.sleep(0.5) # Short pause
        try:
            brand_response = requests.get(brand_url, headers=headers)
            brand_response.raise_for_status()
            brand_soup = BeautifulSoup(brand_response.text, 'html.parser')
            model_links = brand_soup.find_all('a', class_='modeli')
            if model_links:
                for model_link in model_links:
                    model_name = model_link.find('strong').text.strip() if model_link.find('strong') else "N/A"
                    production_years = model_link.find('div', class_='redcolor').text.strip() if model_link.find('div', class_='redcolor') else "N/A"
                    relative_model_url = model_link.get('href')
                    full_model_url = base_url + relative_model_url
                    all_models.append({
                        "BrandName": brand_name,
                        "ModelName": model_name,
                        "ProductionYears": production_years,
                        "ModelURL": full_model_url
                    })
        except requests.exceptions.RequestException as e:
            print(f"  Error downloading brand page {brand_name}: {e}")
        except Exception as e:
            print(f"  An unexpected error occurred while processing brand page {brand_name}: {e}")
    
    print(f"  Step 2 finished. Retrieved {len(all_models)} models.")


# --- Step 3: Extract Generations for each Model ---
if all_models:
    print("\n--- STEP 3: Starting to download generations for each model ---")
    for i, model_info in enumerate(all_models):
        brand_name = model_info['BrandName']
        model_name = model_info['ModelName']
        model_url = model_info['ModelURL']
        print(f"  Downloading generations for: {brand_name} {model_name} ({i+1}/{len(all_models)})")
        time.sleep(0.5) # Short pause 
        try:
            model_response = requests.get(model_url, headers=headers)
            model_response.raise_for_status()
            model_soup = BeautifulSoup(model_response.text, 'html.parser')
            generation_links = model_soup.find_all('a', class_='position')
            if generation_links:
                for gen_link in generation_links:
                    generation_name = gen_link.find('strong', class_='tit').text.strip() if gen_link.find('strong', class_='tit') else "N/A"
                    relative_generation_url = gen_link.get('href')
                    full_generation_url = base_url + relative_generation_url
                    all_generations.append({
                        "BrandName": brand_name,
                        "ModelName": model_name,
                        "GenerationName": generation_name,
                        "GenerationURL": full_generation_url
                    })
        except requests.exceptions.RequestException as e:
            print(f"  Error downloading model page {brand_name} {model_name}: {e}")
        except Exception as e:
            print(f"  An unexpected error occurred while processing model page {brand_name} {model_name}: {e}")
    
    print(f"  Step 3 finished. Retrieved {len(all_generations)} generations.")


# --- Step 4: Extract Engine Variants for each Generation ---
if all_generations:
    print("\n--- STEP 4: Starting to download engine variants for each generation ---")
    for i, gen_info in enumerate(all_generations):
        brand_name = gen_info['BrandName']
        model_name = gen_info['ModelName']
        generation_name = gen_info['GenerationName']
        generation_url = gen_info['GenerationURL']
        print(f"  Downloading variants for: {brand_name} {model_name} {generation_name} ({i+1}/{len(all_generations)})")
        time.sleep(0.5) # Short pause 
        try:
            gen_response = requests.get(generation_url, headers=headers)
            gen_response.raise_for_status()
            gen_soup = BeautifulSoup(gen_response.text, 'html.parser')
            engine_variant_links = gen_soup.find_all('a', href=True)
            
            for link in engine_variant_links:
                strong_tag = link.find('strong')
                if strong_tag:
                    title_span = strong_tag.find('span', class_='tit')
                    end_span = strong_tag.find('span', class_='end')
                    
                    # You previously changed this condition. I'm putting back the '/hp-' check for now.
                    # If you want to test without it, modify this line.
                    if title_span and end_span and link.get('href').endswith(tuple('0123456789')) and '/hp-' in link.get('href') :
                    # And don't forget to uncomment your DEBUG print if you want it:
                    # print(f"    DEBUG: Found potential engine link: {link.get('href')} with title '{title_span.text.strip()}' and end '{end_span.text.strip()}'")

                        engine_variant_name = title_span.text.strip()
                        engine_production_years = end_span.text.strip()
                        relative_engine_url = link.get('href')
                        full_engine_url = base_url + relative_engine_url

                        all_engine_variants.append({
                            "BrandName": brand_name,
                            "ModelName": model_name,
                            "GenerationName": generation_name,
                            "EngineVariantName": engine_variant_name,
                            "EngineVariantProductionYears": engine_production_years,
                            "EngineVariantURL": full_engine_url
                        })
        except requests.exceptions.RequestException as e:
            print(f"  Error downloading generation page {brand_name} {model_name} {generation_name}: {e}")
        except Exception as e:
            print(f"  An unexpected error occurred while processing generation page {brand_name} {model_name} {generation_name}: {e}")
    
    print(f"  Step 4 finished. Retrieved {len(all_engine_variants)} engine variants.")
else:
    print("No generations were retrieved for further processing of engine variants. Exiting.")
    exit() # Exit if no generations were found

# --- Step 5: Extract Detailed Specifications for each Engine Variant ---

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os

# Pouze pro Krok 5: Specifická URL, kterou jste poskytl
url_to_scrape = "https://www.auto-data.net/en/acura-adx-1.5l-190hp-sh-awd-cvt-53849"

# Headers pro HTTP požadavek (doporučeno pro simulaci prohlížeče)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# REVIDOVANÁ pomocná funkce pro čištění klíčů (názvů sloupců)
# Cílem je vzít text z <th> a udělat z něj čistý název sloupce
def clean_spec_key(key_text):
    # Odstranit mezery na začátku/konci
    key_text = key_text.strip()
    
    # Odstranit jakýkoli text v závorkách, např. "Torque (Nm)" -> "Torque"
    key_text = re.sub(r'\s*\(.*?\)', '', key_text).strip()

    # Odstranit čísla a jednotky, které jsou součástí nadpisu, např. "Engine displacement 1498 cm3" -> "Engine displacement"
    # To se týká jen klíče, ne hodnoty. Zajišťuje, že klíč je čistý parametr.
    key_text = re.sub(r'\s*\d+[\d\s.,]*\s*(Hp|Nm|l|cm3|cu\. in\.|mm|in\.|lb\.-ft\.|km/h|mph|sec|kg|lbs|litres|gallons|seats|doors|cylinders|Hz)\s*$', '', key_text, flags=re.IGNORECASE).strip()

    # Odstranit generické fráze, které by neměly být součástí názvu specifikace
    # Příklad: "Engine layout type" -> "Engine layout" (pokud by se objevilo)
    key_text = re.sub(r'\s*(type|configuration|system|architecture|specs|size)\s*$', '', key_text, flags=re.IGNORECASE).strip()


    # Nahradit vícenásobné mezery jednou mezerou a odstranit interpunkci
    key_text = re.sub(r'[\s\.,\?!]+', ' ', key_text).strip()
    
    # První písmeno velké
    if key_text:
        key_text = key_text[0].upper() + key_text[1:]

    return key_text.strip()

# Funkce pro získání hodnoty z <td> tagu
def get_value_from_td(td_tag):
    # Pro hodnoty chceme získat veškerý text, ale bez zbytečných mezer
    # a zohlednit span.val2 pro alternativní jednotky
    
    # Provedeme víceúrovňovou extrakci textu.
    # Nejprve odstraníme elementy, které nechceme (např. span.val2 pokud chceme jen primární jednotku,
    # nebo reklamy uvnitř td, pokud by tam byly)
    
    # Pokud chcete pouze hlavní hodnotu (např. 53 l, ne i 14 US gal), můžete udělat toto:
    # primary_value = td_tag.find(text=True, recursive=False) # Získá text přímo v td, ne vnořený ve span
    # return primary_value.strip() if primary_value else ""

    # Pokud chcete VŠECHNY textové informace z td (např. "53 l 14 US gal | 11.66 UK gal")
    return td_tag.get_text(separator=" ", strip=True)


print(f"--- Spouštění Krok 5: Získávání detailních specifikací z URL: {url_to_scrape} ---")

final_dataset = []
current_spec_data = {
    "BrandName": "Acura", # Statické hodnoty pro tento testovací běh
    "ModelName": "ADX",
    "GenerationName": "ADX",
    "EngineVariantName": "1.5L (190 Hp) SH-AWD CVT",
    "EngineVariantURL": url_to_scrape,
    "EngineVariantProductionYears": "2025 year",
}

try:
    response = requests.get(url_to_scrape, headers=headers)
    response.raise_for_status()
    html_content = response.text

    current_dir = os.getcwd()
    debug_html_filename = "debug_krok5_requests_output.html"
    full_html_path = os.path.join(current_dir, debug_html_filename)
    try:
        with open(full_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"  DEBUG: HTML obsah byl úspěšně uložen do {full_html_path} pro inspekci.")
    except Exception as file_error:
        print(f"  CHYBA: Nepodařilo se uložit debug HTML soubor do {full_html_path}: {file_error}")

    soup = BeautifulSoup(html_content, "html.parser")

    main_spec_table = soup.find("table", class_="cardetailsout car2")
    
    if not main_spec_table:
        print(f"  CHYBA: Hlavní tabulka specifikací (class='cardetailsout car2') nebyla nalezena na stránce {url_to_scrape}.")
        print("  Bude přidáno pouze základní info o variantě.")
        final_dataset.append(current_spec_data)
    else:
        spec_table_body = main_spec_table.find("tbody") 

        if not spec_table_body:
            print(f"  CHYBA: tbody nebyl nalezen uvnitř hlavní tabulky specifikací na stránce {url_to_scrape}.")
            print("  Bude přidáno pouze základní info o variantě.")
            final_dataset.append(current_spec_data)
        else:
            rows = spec_table_body.find_all("tr")
            print(f"  DEBUG: Nalezeno {len(rows)} řádků v tbody hlavní tabulky specifikací.")
            
            for row_idx, row in enumerate(rows):
                # FILTROVÁNÍ NEŽÁDOUCÍCH ŘÁDKŮ
                # Přeskočíme řádky, které mají třídu "no" (nadpisy sekcí nebo reklamy)
                # a kde th má colspan="2"
                if row.has_attr('class') and 'no' in row['class']:
                    th_tag = row.find('th')
                    if th_tag and th_tag.has_attr('colspan') and th_tag['colspan'] == '2':
                        # print(f"  DEBUG: Přeskakuji řádek s nadpisem/reklamou v tbody[{row_idx}]: {row.text.strip()}")
                        continue # Přeskočíme tento řádek

                # Najdeme <th> a <td> v aktuálním řádku
                header = row.find("th")
                value_td = row.find("td") # Použijeme jiný název proměnné, aby to bylo jasnější

                if header and value_td: # Ujistíme se, že oba existují
                    raw_key = header.text.strip()
                    key = clean_spec_key(raw_key) 
                    val = get_value_from_td(value_td) # Použijeme novou funkci pro získání hodnoty

                    if "Log in to see" in val: # Pokud je hodnota "Log in to see...", považujeme ji za prázdnou
                        val = None
                    
                    print(f"  DEBUG: V tbody řádku[{row_idx}]: Původní klíč: '{raw_key}', Vyčištěný klíč: '{key}', Extrahovaná hodnota: '{val}'")

                    current_spec_data[key] = val
                # else: # Tento else blok můžeme zakomentovat, pokud nás nezajímají řádky bez th/td
                #     print(f"  DEBUG: Přeskakuji řádek bez relevantních dat v tbody[{row_idx}].")
            
            final_dataset.append(current_spec_data)

except requests.exceptions.RequestException as e: 
    print(f"  CHYBA při stahování specifikací z {url_to_scrape}: {e}")
except Exception as e:
    print(f"  NEČEKANÁ CHYBA při zpracování specifikací pro {url_to_scrape}: {e}")

# --- Uložení získaných dat do CSV/Excel souboru ---
if final_dataset:
    print("\n--- DOKONČENO: Ukládání kompletních specifikací do souboru ---")
    print("  Celkem získaných detailních specifikací:", len(final_dataset))

    df_final = pd.DataFrame(final_dataset)

    output_csv_filename = "acura_adx_specs_krok5_only.csv"
    df_final.to_csv(output_csv_filename, index=False, encoding="utf-8")
    print(f"  Kompletní specifikace uloženy do {output_csv_filename}")

    try:
        output_excel_filename = "acura_adx_specs_krok5_only.xlsx"
        df_final.to_excel(output_excel_filename, index=False)
        print(f"  Kompletní specifikace uloženy do {output_excel_filename}")
    except ImportError:
        print("  Knihovna 'openpyxl' není nainstalována. Nainstalujte ji pro ukládání do Excelu (pip install openpyxl).")

    print("\n  DataFrame s kompletními specifikacemi (prvních 5 řádků):")
    print(df_final.head())
    print(f"  Počet sloupců (parametrů): {len(df_final.columns)}")

else:
    print("Nebyly nalezeny žádné detailní specifikace nebo došlo k chybě. Výsledný soubor nebude vytvořen.")

print("\n--- Skript dokončen ---")
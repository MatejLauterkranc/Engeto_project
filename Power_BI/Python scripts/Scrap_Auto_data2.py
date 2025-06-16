import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import re

# --- Základní konfigurace ---
base_url = "https://www.auto-data.net"
initial_url = base_url + "/en/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# --- Seznamy pro ukládání dat z jednotlivých kroků ---
all_brands = []
all_models = []
all_generations = []
all_engine_variants = []
final_dataset = []

# --- Pomocné funkce pro čištění dat ---

# Funkce pro čištění klíčů (názvů sloupců)
def clean_spec_key(key_text):
    key_text = key_text.strip()
    key_text = re.sub(r'\s*\(.*?\)', '', key_text).strip()
    key_text = re.sub(r'\s*\d+[\d\s.,]*\s*(Hp|Nm|l|cm3|cu\. in\.|mm|in\.|lb\.-ft\.|km/h|mph|sec|kg|lbs|litres|gallons|seats|doors|cylinders|Hz|m)\s*$', '', key_text, flags=re.IGNORECASE).strip()
    key_text = re.sub(r'\s*(type|configuration|system|architecture|specs|size|arrangement|valvetrain)\s*$', '', key_text, flags=re.IGNORECASE).strip()
    key_text = re.sub(r'[\s\.,\?!:;]+', ' ', key_text).strip()
    
    if key_text:
        key_text = key_text[0].upper() + key_text[1:]
    return key_text.strip()

# Funkce pro získání hodnoty z <td> tagu
def get_value_from_td(td_tag):
    return td_tag.get_text(separator=" ", strip=True)

# --- KROK 1: Extract Brands ---
print(f"\n--- KROK 1: Scrapování značek z {initial_url} ---")
try:
    response = requests.get(initial_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    brands_container = soup.find("div", class_="markite")
    if brands_container:
        brand_links = brands_container.find_all("a", class_="marki_blok")
        print(f"   Nalezeno {len(brand_links)} potenciálních značek. Zpracovávám pouze první (testovací běh).")
        for i, link in enumerate(brand_links[:1]): # Zpracováváme pouze první značku
            brand_name = link.find("strong").text.strip() if link.find("strong") else "N/A"
            relative_url = link.get("href")
            full_brand_url = base_url + relative_url
            if brand_name and brand_name.lower() != "all brands":
                all_brands.append({"BrandName": brand_name, "BrandURL": full_brand_url})
                print(f"   Zpracovávám značku: {brand_name} ({i+1}/1)")
    else:
        print("❌ Kontejner značek (<div class='markite'>) nebyl nalezen.")
    print(f"✅ Krok 1 dokončen. Získáno {len(all_brands)} značek.")
except requests.exceptions.RequestException as e:
    print(f"❌ CHYBA při stahování úvodní stránky: {e}")
    exit()
except Exception as e:
    print(f"❌ NEČEKANÁ CHYBA při zpracování úvodní stránky: {e}")
    exit()

# --- KROK 2: Extract Models for each Brand ---
if all_brands:
    print("\n--- KROK 2: Stahování modelů pro každou značku ---")
    for i, brand_info in enumerate(all_brands): # Zpracováváme všechny získané značky z Kroku 1
        brand_name = brand_info["BrandName"]
        brand_url = brand_info["BrandURL"]
        print(f"   Stahuji modely pro značku: {brand_name} ({i+1}/{len(all_brands)})")
        time.sleep(0.5)
        try:
            brand_response = requests.get(brand_url, headers=headers)
            brand_response.raise_for_status()
            brand_soup = BeautifulSoup(brand_response.text, "html.parser")
            model_links = brand_soup.find_all("a", class_="modeli")
            if model_links:
                print(f"     Nalezeno {len(model_links)} potenciálních modelů. Zpracovávám pouze první (testovací běh).")
                for model_link in model_links[:1]: # Zpracováváme pouze první model
                    model_name = model_link.find("strong").text.strip() if model_link.find("strong") else "N/A"
                    production_years = model_link.find("div", class_="redcolor").text.strip() if model_link.find("div", class_="redcolor") else "N/A"
                    relative_model_url = model_link.get("href")
                    full_model_url = base_url + relative_model_url
                    all_models.append(
                        {
                            "BrandName": brand_name,
                            "ModelName": model_name,
                            "ProductionYears": production_years,
                            "ModelURL": full_model_url,
                        }
                    )
                    print(f"     Zpracovávám model: {model_name} (1/1)")
            else:
                print(f"     Nenalezeny žádné odkazy na modely na {brand_url}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ CHYBA při stahování stránky značky {brand_name}: {e}")
        except Exception as e:
            print(f"   ❌ NEČEKANÁ CHYBA při zpracování stránky značky {brand_name}: {e}")
    print(f"✅ Krok 2 dokončen. Získáno {len(all_models)} modelů.")

# --- KROK 3: Extract Generations for each Model ---
if all_models:
    print("\n--- KROK 3: Stahování generací pro každý model ---")
    for i, model_info in enumerate(all_models): # Zpracováváme všechny získané modely z Kroku 2
        brand_name = model_info["BrandName"]
        model_name = model_info["ModelName"]
        model_url = model_info["ModelURL"]
        print(f"   Stahuji generace pro: {brand_name} {model_name} ({i+1}/{len(all_models)})")
        time.sleep(0.5)
        try:
            model_response = requests.get(model_url, headers=headers)
            model_response.raise_for_status()
            model_soup = BeautifulSoup(model_response.text, "html.parser")
            generation_links = model_soup.find_all("a", class_="position")
            if generation_links:
                print(f"     Nalezeno {len(generation_links)} potenciálních generací. Zpracovávám pouze první (testovací běh).")
                for gen_link in generation_links[:1]: # Zpracováváme pouze první generaci
                    generation_name = gen_link.find("strong", class_="tit").text.strip() if gen_link.find("strong", class_="tit") else "N/A"
                    relative_generation_url = gen_link.get("href")
                    full_generation_url = base_url + relative_generation_url
                    all_generations.append(
                        {
                            "BrandName": brand_name,
                            "ModelName": model_name,
                            "GenerationName": generation_name,
                            "GenerationURL": full_generation_url,
                        }
                    )
                    print(f"     Zpracovávám generaci: {generation_name} (1/1)")
            else:
                print(f"     Nenalezeny žádné odkazy na generace na {model_url}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ CHYBA při stahování stránky modelu {brand_name} {model_name}: {e}")
        except Exception as e:
            print(f"   ❌ NEČEKANÁ CHYBA při zpracování stránky modelu {brand_name} {model_name}: {e}")
    print(f"✅ Krok 3 dokončen. Získáno {len(all_generations)} generací.")

# --- KROK 4: Extract Engine Variants for each Generation ---
if all_generations:
    print("\n--- KROK 4: Stahování variant motoru pro každou generaci ---")
    for i, gen_info in enumerate(all_generations): # Zpracováváme všechny získané generace z Kroku 3
        brand_name = gen_info["BrandName"]
        model_name = gen_info["ModelName"]
        generation_name = gen_info["GenerationName"]
        generation_url = gen_info["GenerationURL"]
        
        print(f"   Stahuji varianty pro: {brand_name} {model_name} {generation_name} ({i+1}/{len(all_generations)})")
        time.sleep(0.5)
        try:
            gen_response = requests.get(generation_url, headers=headers)
            gen_response.raise_for_status()
            gen_soup = BeautifulSoup(gen_response.text, "html.parser")
            engine_variant_links = gen_soup.find_all("a", href=True)

            if engine_variant_links:
                print(f"     Nalezeno {len(engine_variant_links)} potenciálních odkazů. Nyní vyhodnocuji každý odkaz.")
                
                found_engine_variant = False
                for link in engine_variant_links:
                    strong_tag = link.find("strong")
                    if not strong_tag:
                        continue 

                    title_span = strong_tag.find("span", class_="tit")
                    end_span_text = strong_tag.find("span", class_="end").text.strip() if strong_tag.find("span", class_="end") else 'N/A'
                    
                    if (
                        title_span # Musí mít název
                        and link.get("href") # Musí mít href
                        and link.get("href").endswith(tuple("0123456789")) # Musí končit číslem (typické pro detailní stránky)
                        and "hp-" in link.get("href") # Přidáme specifickou kontrolu jako 'hp-'
                    ):
                        print(f"     SHODA! Nalezen platný odkaz na variantu: {link.get('href')} s názvem '{title_span.text.strip()}'")

                        engine_variant_name = title_span.text.strip()
                        engine_production_years = end_span_text 
                        relative_engine_url = link.get("href")
                        full_engine_url = base_url + relative_engine_url

                        all_engine_variants.append(
                            {
                                "BrandName": brand_name,
                                "ModelName": model_name,
                                "GenerationName": generation_name,
                                "EngineVariantName": engine_variant_name,
                                "EngineVariantProductionYears": engine_production_years,
                                "EngineVariantURL": full_engine_url,
                            }
                        )
                        print(f"     Zpracovávám variantu motoru: {engine_variant_name} (1/1)")
                        found_engine_variant = True
                        break # Důležité: Zastavíme se po nalezení první platné varianty motoru (pro tento testovací běh)
                
                if not found_engine_variant:
                    print(f"     Nenalezen žádný platný odkaz na variantu motoru odpovídající kritériím na {generation_url}")

            else:
                print(f"     Nenalezeny žádné odkazy na varianty motoru na {generation_url}")

        except requests.exceptions.RequestException as e:
            print(f"   ❌ CHYBA při stahování stránky generace {brand_name} {model_name} {generation_name}: {e}")
        except Exception as e:
            print(f"   ❌ NEČEKANÁ CHYBA při zpracování stránky generace {brand_name} {model_name} {generation_name}: {e}")
    print(f"✅ Krok 4 dokončen. Získáno {len(all_engine_variants)} variant motoru.")
else:
    print("⚠️  Nebyly získány žádné generace pro další zpracování variant motoru. Ukončuji.")
    exit()

# --- KROK 5: Download detailed specifications for each engine variant ---
if all_engine_variants:
    print("\n--- KROK 5: Stahování detailních specifikací pro každou variantu motoru ---")
    print("   UPOZORNĚNÍ: Toto je testovací běh pro jediný záznam. Žádné mezilehlé CSV soubory nebudou uloženy.")

    sleep_time_per_spec = 1 # Prodleva mezi stahováním jednotlivých specifikací

    data_source = all_engine_variants # V produkčním kódu byste zde iterovali přes všechny varianty

    for i, eng_var_info in enumerate(data_source): # Procházíme získané varianty motoru
        brand_name = eng_var_info["BrandName"]
        model_name = eng_var_info["ModelName"]
        generation_name = eng_var_info["GenerationName"]
        engine_variant_name = eng_var_info["EngineVariantName"]
        engine_variant_url = eng_var_info["EngineVariantURL"]

        print(f"   ({i+1}/{len(data_source)}) Stahuji specifikace pro: {brand_name} {model_name} {generation_name} - {engine_variant_name}")
        print(f"     URL specifikací: {engine_variant_url}")
        time.sleep(sleep_time_per_spec)

        try:
            current_spec_data = {
                "BrandName": brand_name,
                "ModelName": model_name,
                "GenerationName": generation_name,
                "EngineVariantName": engine_variant_name,
                "EngineVariantURL": engine_variant_url,
                "EngineVariantProductionYears": eng_var_info["EngineVariantProductionYears"],
            }

            # --- POUŽÍVÁME POUZE REQUESTS ---
            response = requests.get(engine_variant_url, headers=headers)
            response.raise_for_status() # Vyvolá výjimku pro chybové stavy HTTP (4xx nebo 5xx)
            spec_html = response.text
            # --- KONEC POUŽITÍ POUZE REQUESTS ---

            spec_soup = BeautifulSoup(spec_html, "html.parser")

            main_spec_table = spec_soup.find("table", class_="cardetailsout car2")
            
            if not main_spec_table:
                print(f"     ❌ CHYBA: Hlavní tabulka specifikací (class='cardetailsout car2') nebyla nalezena na stránce {engine_variant_url}. Přidávám pouze základní info.")
                final_dataset.append(current_spec_data)
                continue

            spec_table_body = main_spec_table.find("tbody") 

            if not spec_table_body:
                print(f"     ❌ CHYBA: tbody nebyl nalezen uvnitř hlavní tabulky specifikací na stránce {engine_variant_url}. Přidávám pouze základní info.")
                final_dataset.append(current_spec_data)
                continue

            rows = spec_table_body.find_all("tr")
            print(f"     DEBUG: Nalezeno {len(rows)} řádků v tbody hlavní tabulky specifikací.")
            
            for row_idx, row in enumerate(rows):
                # Filtrování nežádoucích řádků: nadpisy sekcí a reklamy
                th_tag = row.find("th")
                if th_tag:
                    # Pokud je to nadpis sekce (např. "General information")
                    if th_tag.has_attr('colspan') and th_tag['colspan'] == '2':
                        # print(f"       DEBUG: Přeskakuji řádek s nadpisem sekce: '{th_tag.text.strip()}' v tbody[{row_idx}].")
                        continue
                    # Pokud je to reklama uvnitř <th>
                    if th_tag.find("div", class_="adin"):
                        # print(f"       DEBUG: Přeskakuji řádek s reklamou v <th> v tbody[{row_idx}].")
                        continue
                
                # Zpracování řádků s daty (th a td)
                header = row.find("th")
                value_td = row.find("td") 

                if header and value_td: # Ujistíme se, že oba tagy existují
                    raw_key = header.text.strip()
                    key = clean_spec_key(raw_key) 
                    val = get_value_from_td(value_td)

                    if "Log in to see" in val: # Pokud je hodnota "Log in to see...", považujeme ji za prázdnou
                        val = None
                    
                    print(f"       DEBUG: V řádku [{row_idx}]: Původní klíč: '{raw_key}' -> Vyčištěný klíč: '{key}', Extrahovaná hodnota: '{val}'")

                    current_spec_data[key] = val
                # else: 
                #    print(f"       DEBUG: Přeskakuji řádek bez relevantních dat v tbody[{row_idx}]. HTML řádku: {row}")
            
            final_dataset.append(current_spec_data)

        except requests.exceptions.RequestException as e: 
            print(f"   ❌ CHYBA stahování specifikací pro {engine_variant_url}: {e}")
            final_dataset.append(current_spec_data) # Přidáme alespoň základní info v případě chyby
        except Exception as e:
            print(f"   ❌ NEČEKANÁ CHYBA při zpracování specifikací pro {engine_variant_url}: {e}")
            final_dataset.append(current_spec_data) # Přidáme alespoň základní info v případě chyby

# --- Uložení získaných dat do jediného CSV/Excel souboru ---
if final_dataset:
    print("\n--- ✅ DOKONČENO: Ukládání kompletních specifikací do jediného souboru ---")
    print(f"   Celkem získaných detailních specifikací: {len(final_dataset)}")

    df_final = pd.DataFrame(final_dataset)

    output_csv_filename = "full_car_specs.csv"
    df_final.to_csv(output_csv_filename, index=False, encoding="utf-8")
    print(f"   Kompletní specifikace uloženy do {output_csv_filename}")

    try:
        output_excel_filename = "full_car_specs.xlsx"
        df_final.to_excel(output_excel_filename, index=False)
        print(f"   Kompletní specifikace uloženy do {output_excel_filename}")
    except ImportError:
        print("   ⚠️  Knihovna 'openpyxl' není nainstalována. Nainstalujte ji pro ukládání do Excelu (pip install openpyxl).")

    print("\n   DataFrame s kompletními specifikacemi (prvních 5 řádků):")
    print(df_final.head())
    print(f"   Počet sloupců (parametrů): {len(df_final.columns)}")

else:
    print("❌ Nebyly nalezeny žádné detailní specifikace nebo došlo k chybám. Výsledný soubor nebude vytvořen.")

print("\n--- 🏁 Skript dokončen ---")
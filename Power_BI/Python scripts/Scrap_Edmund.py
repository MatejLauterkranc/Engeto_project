import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re
import os
import random # Pro náhodné pauzy

# --- Konfigurace ---
EDMUNDS_URL = "https://www.edmunds.com/inventory/srp.html"
OUTPUT_CSV_FILE = "edmunds_scraped_prices_firefox_paginated_v2.csv" # Nový název pro odlišení

script_dir = os.path.dirname(os.path.abspath(__file__))
GECKODRIVER_PATH = os.path.join(script_dir, 'geckodriver.exe')

BRANDS_TO_SCRAPE = [
    "Volkswagen",
    "Tesla",
    "Honda"
]

US_ZIP_CODE = "90210" 

# --- Inicializace WebDriveru (beze změny) ---
def initialize_driver():
    options = webdriver.FirefoxOptions()
    # options.add_argument("--headless")
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0") 
    try:
        service = Service(GECKODRIVER_PATH) 
        driver = webdriver.Firefox(service=service, options=options)
        return driver
    except Exception as e:
        print(f"Chyba při inicializaci WebDriveru (Firefox): {e}")
        print(f"Ujistěte se, že '{GECKODRIVER_PATH}' existuje a je kompatibilní s vaším Firefoxem.")
        return None

# --- Funkce pro scraping jedné stránky (úpravy v čekání a rolování) ---
def scrape_page(driver, url):
    """Načte URL, zavře privacy banner, počká na další pop-upy, roluje a vrátí HTML."""
    try:
        driver.get(url)

        # Čekání na privacy banner - stále důležité, i když se ne vždy objeví
        try:
            privacy_close_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.close-btn[data-tracking-id="close_privacy_disclaimer"]'))
            )
            privacy_close_button.click()
            print("Privacy banner byl uzavřen.")
            time.sleep(random.uniform(2, 4)) # Náhodná pauza
        except Exception as e:
            print(f"Privacy banner nebyl nalezen nebo se nepodařilo kliknout (možná už není zobrazen): {e}")
            
        print("Čekám na zmizení dalších pop-upů (např. Google přihlášení)...")
        time.sleep(random.uniform(5, 9)) # Delší náhodná pauza pro pop-upy

        # Čekáme na přítomnost hlavního prvku s auty (`clickable-card`)
        try:
            WebDriverWait(driver, 60).until( # Dlouhé čekání
                EC.presence_of_element_located((By.CLASS_NAME, "clickable-card"))
            )
            print("Nalezen alespoň jeden 'clickable-card' prvek vozidla. Stránka by měla být načtena.")
            time.sleep(random.uniform(3, 6)) # Náhodná pauza po nalezení prvku
        except Exception as e:
            print(f"Chyba: Žádné 'clickable-card' vozidlo nebylo nalezeno po 60 sekundách čekání na {url}: {e}")
            # Pokud se nenašlo žádné auto, vrátíme prázdné HTML (nebo to nechejme zpracovat dál)
            # Důležité: Tady nevracíme None, abychom umožnili ověření v extract_car_data
            return BeautifulSoup("", 'html.parser') # Vrátíme prázdný soup, pokud se nic nenašlo

        # Agresivní rolování pro načtení veškerého obsahu
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 10 # Zvýšil jsem počet pokusů o rolování
        while scroll_attempts < max_scroll_attempts:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(5, 9)) # Delší náhodná pauza po každém rolování
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print(f"Dosaženo dna po {scroll_attempts + 1} rolováních.")
                break 
            last_height = new_height
            scroll_attempts += 1
        
        print("Rolování dokončeno, získávám HTML kód stránky.")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        return soup
    except Exception as e:
        print(f"Chyba při načítání stránky {url} (celkově): {e}")
        return None

# --- Funkce pro extrakci dat z HTML (beze změny) ---
def extract_car_data(soup):
    cars_data = []
    
    vehicle_cards = soup.find_all('div', class_='clickable-card')
    
    if not vehicle_cards:
        return []

    for card in vehicle_cards:
        name_element = card.find('div', class_='size-16 text-cool-gray-10 fw-bold mb-0_5')
        price_element = card.find('span', class_='heading-3')

        car_name = name_element.get_text(strip=True) if name_element else None
        price_text = price_element.get_text(strip=True) if price_element else None

        if car_name and price_text:
            cleaned_price = re.sub(r'[$,]', '', price_text)
            try:
                price_value = float(cleaned_price)
                cars_data.append({
                    'Scraped_Car_Name': car_name,
                    'Scraped_Price_USD': price_value,
                    'Scraped_Currency': 'USD'
                })
            except ValueError:
                print(f"Nelze převést cenu '{cleaned_price}' na číslo pro {car_name}.")
            
    return cars_data

# --- Hlavní logika skriptu s upravenou paginací ---
def main():
    driver = initialize_driver()
    if not driver:
        return

    all_scraped_data = []

    for brand in BRANDS_TO_SCRAPE:
        print(f"\n--- Scraping dat pro značku: {brand} ---")
        current_page_num = 1
        max_pages_to_scrape = 100 # Zvýšil jsem limit stránek, když víme, že existují
        
        # Sledujeme, zda jsme našli nějaká data na předchozí stránce.
        # Pokud se na dvou po sobě jdoucích stránkách nenašly žádné karty, pak jsme pravděpodobně na konci.
        consecutive_empty_pages = 0
        max_consecutive_empty = 2 # Počet prázdných stránek, po kterých zastavíme

        while current_page_num <= max_pages_to_scrape:
            search_url = f"{EDMUNDS_URL}?make={brand}&zip={US_ZIP_CODE}&pagenumber={current_page_num}"
            print(f"Načítám stránku {current_page_num} pro {brand} (URL: {search_url})")

            soup = scrape_page(driver, search_url)
            
            if soup is None: # Zcela selhalo načtení stránky (např. chyba s driverem)
                print(f"Nepodařilo se načíst stránku {current_page_num} pro {brand}. Přeskakuji na další značku.")
                break 

            brand_data_on_page = extract_car_data(soup)
            
            if brand_data_on_page: # Pokud se na stránce našla nějaká auta
                all_scraped_data.extend(brand_data_on_page)
                print(f"Nalezeno {len(brand_data_on_page)} aut na stránce {current_page_num} pro značku {brand}. Celkem: {len(all_scraped_data)}")
                current_page_num += 1 
                consecutive_empty_pages = 0 # Resetujeme počítadlo prázdných stránek
                time.sleep(random.uniform(4, 8)) # Náhodná pauza před další stránkou
            else:
                consecutive_empty_pages += 1
                print(f"Na stránce {current_page_num} pro {brand} nebyla nalezena žádná auta. Po sobě jdoucí prázdné stránky: {consecutive_empty_pages}")
                
                if consecutive_empty_pages >= max_consecutive_empty:
                    print(f"Dosaženo {max_consecutive_empty} po sobě jdoucích prázdných stránek pro {brand}. Předpokládám konec výsledků.")
                    break # Ukončíme smyčku pro tuto značku
                
                current_page_num += 1 # I když je stránka prázdná, zkusíme další, pro jistotu
                time.sleep(random.uniform(4, 8)) # Pauza i po prázdné stránce


        time.sleep(random.uniform(8, 15)) # Delší náhodná pauza mezi značkami

    driver.quit()

    if all_scraped_data:
        df_scraped = pd.DataFrame(all_scraped_data)
        df_scraped.to_csv(OUTPUT_CSV_FILE, index=False)
        print(f"\nScraping dokončen. Data uložena do '{OUTPUT_CSV_FILE}'")
        print(df_scraped.head())
    else:
        print("Žádná data nebyla nalezena.")

if __name__ == "__main__":
    main()
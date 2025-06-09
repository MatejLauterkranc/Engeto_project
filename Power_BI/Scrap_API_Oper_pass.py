import requests
import csv
import json
import time

# --- Konfigurace ---
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OUTPUT_FILENAME = "ev_chargers_czechia.csv"

# Bounding box pro celou Českou republiku (přibližné souřadnice)
# Tato oblast bude rozdělena na menší čtverce.
CZ_BOUNDING_BOX = (48.5, 12.0, 51.1, 19.0) # min_lat, min_lon, max_lat, max_lon

# Velikost kroku pro rozdělení ČR na menší čtverce (ve stupních)
# Menší hodnoty = více dotazů, delší běh, ale menší riziko timeoutů.
# Větší hodnoty = méně dotazů, rychlejší běh, ale vyšší riziko timeoutů/chyb.
# Pro ČR je 0.1 stupeň dobrý kompromis.
STEP_LAT, STEP_LON = 0.1, 0.1

# Pauza mezi jednotlivými dotazy na Overpass API (v sekundách)
# Důležité pro respektování Fair Use Policy Overpass API.
QUERY_PAUSE_SECONDS = 5

# --- Funkce pro stažení dat ---
def get_overpass_data(bbox):
    """
    Stáhne data o nabíjecích stanicích z Overpass API pro daný bounding box.
    """
    min_lat, min_lon, max_lat, max_lon = bbox

    # Overpass QL dotaz pro amenity=charging_station.
    # Timeout nastaven na 90 sekund, což by mělo být dostatečné pro menší čtverce.
    overpass_query = f"""
    [out:json][timeout:90];
    (
      node["amenity"="charging_station"]({min_lat},{min_lon},{max_lat},{max_lon});
      way["amenity"="charging_station"]({min_lat},{min_lon},{max_lat},{max_lon});
      relation["amenity"="charging_station"]({min_lat},{min_lon},{max_lat},{max_lon});
    );
    out body;
    >;
    out skel qt;
    """
    try:
        response = requests.post(OVERPASS_URL, data=overpass_query)
        response.raise_for_status() # Vyhodí chybu pro špatné HTTP kódy (4xx nebo 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Chyba při stahování dat z Overpass API pro box {bbox}: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Chyba při dekódování JSON odpovědi pro box {bbox}. Odpověď API: {response.text[:500]}...")
        return None

# --- Funkce pro generování mřížky bounding boxů ---
def generate_cz_grid_boxes(min_lat, min_lon, max_lat, max_lon, step_lat, step_lon):
    """
    Generuje souřadnice bounding boxů pro pokrytí dané oblasti mřížkou.
    """
    boxes = []
    current_lat = min_lat
    while current_lat < max_lat:
        current_lon = min_lon
        while current_lon < max_lon:
            box_max_lat = min(current_lat + step_lat, max_lat)
            box_max_lon = min(current_lon + step_lon, max_lon)
            boxes.append((current_lat, current_lon, box_max_lat, box_max_lon))
            current_lon += step_lon
        current_lat += step_lon # Použijte step_lon zde místo step_lat
    return boxes

# --- Funkce pro zpracování a uložení dat do CSV ---
def save_to_csv(data_elements, filename):
    """
    Zpracuje seznam elementů z Overpass API a uloží vybrané informace do CSV souboru.
    Zahrnuje deduplikaci podle ID.
    """
    if not data_elements:
        print("Žádné elementy k uložení.")
        return

    # Definujeme hlavičky CSV souboru a snažíme se pokrýt běžné tagy pro nabíječky
    # Rozšířený seznam potenciálních tagů pro lepší data
    fieldnames = [
        'id', 'type', 'lat', 'lon', 'name', 'operator', 'capacity',
        'ref', 'authentication', 'fee', 'payment:cards', 'payment:credit_cards',
        'payment:cash', 'socket_outlet:type', 'socket_outlet:count',
        'socket_outlet:max_power', 'opening_hours', 'access', 'website', 'phone'
    ]
    
    # Dynamicky přidáme pole pro jednotlivé typy konektorů a jejich výkony
    for i in range(1, 11): # Kontrolujeme až 10 potenciálních konektorů
        fieldnames.append(f'socket_outlet:{i}:type')
        fieldnames.append(f'socket_outlet:{i}:power')
        fieldnames.append(f'socket_outlet:{i}:current')
        fieldnames.append(f'socket_outlet:{i}:voltage')


    processed_chargers = []
    seen_ids = set() # Pro deduplikaci

    for element in data_elements:
        if element['id'] in seen_ids:
            continue # Přeskočit, pokud už jsme tento element zpracovali
        seen_ids.add(element['id'])

        # Zpracováváme pouze "nodes" (uzly), které jsou nejčastější pro jednotlivé nabíječky.
        # "Ways" a "relations" (složitější geometrie) pro tento účel přeskočíme.
        if element['type'] == 'node':
            tags = element.get('tags', {})
            charger_info = {
                'id': element['id'],
                'type': element['type'],
                'lat': element.get('lat'),
                'lon': element.get('lon'),
            }
            # Vyplnění všech definovaných polí z tagů
            for field in fieldnames:
                if field not in ['id', 'type', 'lat', 'lon']:
                    charger_info[field] = tags.get(field, 'N/A')
            
            processed_chargers.append(charger_info)
        # Informace o přeskočení "way" a "relation" jsou nyní tišší
        # elif element['type'] == 'way':
        #     pass
        # elif element['type'] == 'relation':
        #     pass

    if not processed_chargers:
        print("Po filtraci nejsou žádné uzly nabíjecích stanic k uložení.")
        return

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader() # Zapíše hlavičky
            writer.writerows(processed_chargers) # Zapíše řádky dat
        print(f"Data byla úspěšně uložena do souboru '{filename}'.")
        print(f"Celkem uloženo {len(processed_chargers)} unikátních záznamů.")
    except IOError as e:
        print(f"Chyba při zápisu do souboru '{filename}': {e}")

# --- Hlavní spouštěcí blok ---
if __name__ == "__main__":
    print("Spouštím skript pro stahování dat o EV nabíječkách pro celou Českou republiku...")
    start_time = time.time()

    # Generování všech bounding boxů pro ČR
    all_cz_boxes = generate_cz_grid_boxes(CZ_BOUNDING_BOX[0], CZ_BOUNDING_BOX[1],
                                          CZ_BOUNDING_BOX[2], CZ_BOUNDING_BOX[3],
                                          STEP_LAT, STEP_LON)
    
    print(f"Česká republika rozdělena do {len(all_cz_boxes)} čtverců k prohledání.")

    all_ev_charger_elements = [] # Zde budeme shromažďovat všechny elementy z API

    for i, bbox in enumerate(all_cz_boxes):
        print(f"Zpracovávám čtverec {i+1}/{len(all_cz_boxes)}: {bbox}")
        
        osm_data = get_overpass_data(bbox)

        if osm_data and 'elements' in osm_data:
            all_ev_charger_elements.extend(osm_data['elements'])
            print(f"  Nalezeno {len(osm_data['elements'])} elementů v tomto čtverci.")
        else:
            print(f"  Žádná data nebo chyba pro tento čtverec.")

        # Pauza mezi dotazy pro respektování Fair Use Policy Overpass API
        time.sleep(QUERY_PAUSE_SECONDS)

    print("\n--- Stahování dokončeno. Zahajuji zpracování a ukládání dat. ---")
    save_to_csv(all_ev_charger_elements, OUTPUT_FILENAME)

    end_time = time.time()
    print(f"Skript dokončen za {end_time - start_time:.2f} sekund.")
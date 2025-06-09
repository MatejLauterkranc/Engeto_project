import requests
import csv
import json
import time
import os

# --- Konfigurace ---
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OUTPUT_FILENAME = "ev_chargers_czechia_specific_metrics.csv"
FAILED_BOXES_LOG = "failed_boxes.json" # Soubor pro záznam selhaných čtverců

# Bounding box pro celou Českou republiku (přibližné souřadnice)
CZ_BOUNDING_BOX = (48.5, 12.0, 51.1, 19.0) # min_lat, min_lon, max_lat, max_lon

# Velikost kroku pro rozdělení ČR na menší čtverce (ve stupních)
STEP_LAT, STEP_LON = 0.05, 0.05

# Pauza mezi jednotlivými dotazy na Overpass API (v sekundách)
QUERY_PAUSE_SECONDS = 10

# Nastavení pro opakované pokusy
MAX_RETRIES = 3    # Kolikrát se pokusit o stažení pro jeden čtverec
RETRY_DELAY = 15   # Pauza mezi opakovanými pokusy (v sekundách)

# --- Funkce pro stažení dat s opakovanými pokusy ---
def get_overpass_data(bbox, current_attempt=1):
    """
    Stáhne data o nabíjecích stanicích z Overpass API pro daný bounding box.
    Implementuje opakované pokusy.
    """
    min_lat, min_lon, max_lat, max_lon = bbox

    # Overpass QL dotaz s vyšším timeoutem
    overpass_query = f"""
    [out:json][timeout:180];
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
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Chyba při stahování dat pro box {bbox} (pokus {current_attempt}): {e}")
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
        current_lat += step_lat
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

    # Definujeme HLAVIČKY CSV souboru PŘESNĚ podle tvého JSON příkladu
    # Všimni si, že 'amenity' je také tag, i když je v kořeni JSONu jako "amenity".
    # Zde ho dáme do tags, protože se tak získává z 'tags' dictionary.
    fieldnames = [
        'id', 'lat', 'lon', 'amenity', 'authentication:nfc', 'capacity',
        'capacity:car', 'motorcar', 'operator', 'operator:wikidata',
        'socket:schuko', 'socket:schuko:current', 'socket:schuko:voltage',
        'socket:type2', 'socket:type2:current', 'socket:type2:voltage'
    ]

    processed_chargers = []
    seen_ids = set() # Pro deduplikaci

    for element in data_elements:
        if element['id'] in seen_ids:
            continue # Přeskočit, pokud už jsme tento element zpracovali
        seen_ids.add(element['id'])

        # Zpracováváme pouze "nodes" (uzly)
        if element['type'] == 'node':
            tags = element.get('tags', {})
            charger_info = {
                'id': element['id'],
                'lat': element.get('lat'),
                'lon': element.get('lon'),
                # 'amenity' je speciální případ, v JSONu je v kořeni i v tags
                # Zde ho bereme z tags dictionary, jak je obvyklé pro ostatní tagy
                'amenity': tags.get('amenity', 'N/A'),
            }
            # Vyplnění zbývajících definovaných polí z tagů
            for field in fieldnames:
                if field not in ['id', 'lat', 'lon', 'amenity']: # Tyto už máme zpracované
                    charger_info[field] = tags.get(field, 'N/A') # 'N/A' pro chybějící data
            
            processed_chargers.append(charger_info)

    if not processed_chargers:
        print("Po filtraci nejsou žádné uzly nabíjecích stanic k uložení.")
        return

    try:
        file_exists = os.path.exists(filename)
        file_is_empty = not file_exists or os.path.getsize(filename) == 0

        with open(filename, 'a' if file_exists and not file_is_empty else 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if file_is_empty: # Zapíše hlavičky jen pokud soubor neexistoval nebo byl prázdný
                writer.writeheader()
            writer.writerows(processed_chargers) # Zapíše řádky dat
        print(f"Data byla úspěšně přidána/uložena do souboru '{filename}'.")
        print(f"Celkem přidáno {len(processed_chargers)} unikátních záznamů.")
    except IOError as e:
        print(f"Chyba při zápisu do souboru '{filename}': {e}")

# --- Hlavní spouštěcí blok ---
if __name__ == "__main__":
    print("Spouštím skript pro stahování dat o EV nabíječkách pro celou Českou republiku s přesně definovanými metrikami...")
    start_time = time.time()

    # Generování všech bounding boxů pro ČR
    all_cz_boxes = generate_cz_grid_boxes(CZ_BOUNDING_BOX[0], CZ_BOUNDING_BOX[1],
                                          CZ_BOUNDING_BOX[2], CZ_BOUNDING_BOX[3],
                                          STEP_LAT, STEP_LON)
    
    print(f"Česká republika rozdělena do {len(all_cz_boxes)} čtverců k prohledání.")

    all_ev_charger_elements = [] # Zde budeme shromažďovat všechny úspěšně stažené elementy
    failed_boxes = []            # Zde budeme ukládat souřadnice čtverců, které selhaly

    # --- První průchod: Stahování dat ---
    for i, bbox in enumerate(all_cz_boxes):
        print(f"Zpracovávám čtverec {i+1}/{len(all_cz_boxes)}: {bbox}")
        
        success = False
        for attempt in range(MAX_RETRIES):
            osm_data = get_overpass_data(bbox, attempt + 1)
            if osm_data and 'elements' in osm_data:
                all_ev_charger_elements.extend(osm_data['elements'])
                print(f"  Nalezeno {len(osm_data['elements'])} elementů v tomto čtverci.")
                success = True
                break # Úspěch, jdeme na další box
            elif attempt < MAX_RETRIES - 1:
                print(f"  Čekám {RETRY_DELAY} sekund před dalším pokusem pro box {bbox}...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"  Všechny pokusy pro box {bbox} selhaly.")
        
        if not success:
            failed_boxes.append(bbox) # Zaznamenáme selhaný box

        # Pauza mezi dotazy pro respektování Fair Use Policy Overpass API
        time.sleep(QUERY_PAUSE_SECONDS)

    print("\n--- Stahování hlavního průchodu dokončeno. ---")
    print(f"Celkem úspěšně staženo {len(all_ev_charger_elements)} elementů.")
    print(f"Selhalo {len(failed_boxes)} čtverců. Ukládám jejich souřadnice do '{FAILED_BOXES_LOG}'.")

    # Uložení selhaných čtverců do JSON souboru
    try:
        with open(FAILED_BOXES_LOG, 'w', encoding='utf-8') as f:
            json.dump(failed_boxes, f, indent=4)
    except IOError as e:
        print(f"Chyba při ukládání selhaných čtverců do {FAILED_BOXES_LOG}: {e}")

    # --- Druhý průchod: Zpracování selhaných čtverců ---
    if failed_boxes:
        print("\n--- Spouštím druhý průchod pro selhané čtverce. ---")
        retried_failed_boxes = []
        for i, bbox in enumerate(failed_boxes):
            print(f"Zpracovávám selhaný čtverec {i+1}/{len(failed_boxes)}: {bbox}")
            
            success = False
            for attempt in range(MAX_RETRIES): # Opětovné pokusy pro selhané boxy
                osm_data = get_overpass_data(bbox, attempt + 1)
                if osm_data and 'elements' in osm_data:
                    all_ev_charger_elements.extend(osm_data['elements'])
                    print(f"  Nalezeno {len(osm_data['elements'])} elementů v tomto selhaném čtverci.")
                    success = True
                    break
                elif attempt < MAX_RETRIES - 1:
                    print(f"  Čekám {RETRY_DELAY} sekund před dalším pokusem pro selhaný box {bbox}...")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"  Všechny pokusy pro selhaný box {bbox} opět selhaly.")
            
            if not success:
                retried_failed_boxes.append(bbox) # Zaznamenáme boxy, které selhaly i po druhém průchodu

            time.sleep(QUERY_PAUSE_SECONDS) # Pauza i ve druhém průchodu
        
        print("\n--- Druhý průchod dokončen. ---")
        if retried_failed_boxes:
            print(f"Tyto čtverce selhaly i po druhém průchodu ({len(retried_failed_boxes)}):")
            for bbox in retried_failed_boxes:
                print(f"  {bbox}")
            # Můžeš zvážit uložení i těchto "trvale" selhaných boxů do jiného souboru

    print("\n--- Ukládám všechna shromážděná data do CSV souboru. ---")
    save_to_csv(all_ev_charger_elements, OUTPUT_FILENAME)

    end_time = time.time()
    print(f"Skript dokončen za {end_time - start_time:.2f} sekund.")
import requests
import csv
import json
import time
import os
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError
from shapely.geometry import shape, MultiPolygon, Polygon
import warnings

# Potlačíme UserWarning od shapely pro neplatné geometrie,
# abychom nezahlcovali výstup, ale stále je logujeme.
warnings.filterwarnings("ignore", category=UserWarning, module='shapely')


# --- Konfigurace ---
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
MAIN_OUTPUT_FILENAME = "ev_chargers_global_with_location.csv"
FAILED_GEOCODING_LOG = "failed_geocoding_global.json"
GEOJSON_DATA_FOLDER = "country_geojson_data" # Složka s GeoJSON soubory zemí

# Velikost kroku pro rozdělení oblasti na menší čtverce (ve stupních)
STEP_LAT, STEP_LON = 0.05, 0.05

# Pauza mezi jednotlivými dotazy na Overpass API (v sekundách)
QUERY_PAUSE_SECONDS = 5 # Buďte opatrní při zvyšování, může vést k blokaci

# Nastavení pro opakované pokusy Overpass API
MAX_RETRIES_OVERPASS = 3
RETRY_DELAY_OVERPASS = 10

# Nastavení pro reverzní geokódování (Nominatim)
GEOCODING_PAUSE_SECONDS = 1.0 # Nominatim doporučuje min. 1 dotaz za sekundu
MAX_RETRIES_GEOCODING = 2

# Inicializace geokodéru Nominatim
# PROSÍM, nahraďte toto něčím specifickým pro vaši aplikaci!
geolocator = Nominatim(user_agent="EV_Charger_Scraper_Global/1.0 (vas_email@example.com)")


# --- Pomocné funkce pro Overpass API ---
def get_overpass_data(bbox, current_attempt=1):
    """
    Stáhne data o nabíjecích stanicích z Overpass API pro daný bounding box.
    Implementuje opakované pokusy.
    """
    min_lat, min_lon, max_lat, max_lon = bbox

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
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Chyba při stahování dat pro box {bbox} (pokus {current_attempt}): {e}")
        return None

# --- Pomocné funkce pro geokódování ---
def get_location_details(lat, lon, current_attempt=1):
    """
    Provede reverzní geokódování pro dané souřadnice a vrátí město, stát a zemi.
    """
    try:
        location = geolocator.reverse((lat, lon), language="cs", timeout=10)
        if location and location.address:
            address = location.raw.get('address', {})
            city = address.get('city') or address.get('town') or address.get('village') or 'N/A'
            state = address.get('state') or 'N/A'
            country = address.get('country') or 'N/A'
            return city, state, country
        return 'N/A', 'N/A', 'N/A'
    except (GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError) as e:
        print(f"Chyba při geokódování souřadnic ({lat}, {lon}) (pokus {current_attempt}): {e}")
        return None, None, None
    except Exception as e:
        print(f"Neočekávaná chyba při geokódování ({lat}, {lon}): {e}")
        return 'N/A', 'N/A', 'N/A'

# --- Funkce pro generování mřížky bounding boxů ---
def generate_grid_boxes(min_lat, min_lon, max_lat, max_lon, step_lat, step_lon):
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

# --- Funkce pro získávání Bounding Boxů z GeoJSON souborů ---
def get_bbox_from_geojson(geojson_data):
    """
    Extrahování bounding boxu (min_lat, min_lon, max_lat, max_lat)
    z GeoJSON dat.
    """
    if not geojson_data or 'features' not in geojson_data:
        return None

    all_coordinates = []
    for feature in geojson_data['features']:
        geometry = feature.get('geometry')
        if geometry and 'coordinates' in geometry:
            try:
                # Shapely dokáže přímo zpracovat GeoJSON geometrie
                geom = shape(geometry)
                
                if geom.is_valid:
                    # bounds vrátí (minx, miny, maxx, maxy) což je (min_lon, min_lat, max_lon, max_lat)
                    min_lon, min_lat, max_lon, max_lat = geom.bounds
                    all_coordinates.append((min_lon, min_lat, max_lon, max_lat))
                else:
                    # Logování neplatných geometrií namísto vyhození chyby
                    print(f"Varování: Neplatná geometrie v GeoJSON souboru. Typ: {geometry.get('type')}. Přeskakuji.")
            except Exception as e:
                print(f"Chyba při zpracování geometrie: {e}. Geometrie: {geometry}. Přeskakuji.")
                
    if not all_coordinates:
        return None

    # Spočítáme globální bounding box pro všechny geometrie v souboru
    # (pokud by feature collection obsahovala více částí pro jednu zemi)
    global_min_lon = min(bbox[0] for bbox in all_coordinates)
    global_min_lat = min(bbox[1] for bbox in all_coordinates)
    global_max_lon = max(bbox[2] for bbox in all_coordinates)
    global_max_lat = max(bbox[3] for bbox in all_coordinates)

    # Vrátíme ve formátu (min_lat, min_lon, max_lat, max_lon) pro konzistenci se stávajícím skriptem
    return (global_min_lat, global_min_lon, global_max_lat, global_max_lon)

def generate_country_bboxes(folder_path):
    """
    Projede všechny GeoJSON soubory v dané složce a vrátí slovník
    {country_code: (country_name, bbox_tuple)}.
    """
    countries_data = {}
    
    if not os.path.isdir(folder_path):
        print(f"Chyba: Složka '{folder_path}' nebyla nalezena. Ujistěte se, že soubory jsou tam.")
        return countries_data

    print(f"Načítám bounding boxy zemí ze složky: '{folder_path}'")
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            filepath = os.path.join(folder_path, filename)
            # Předpokládáme, že název souboru je kód země (např. "cz.json" -> "CZ")
            # Nebo jednoduše "afghanistan.json" -> "afghanistan"
            country_name_from_file = os.path.splitext(filename)[0].replace("_", " ").title() # afghanistan -> Afghanistan
            country_code = country_name_from_file[:3].upper() # Jen pro jednoduchost, ideálně mapovat dle ISO kódů

            print(f"  Zpracovávám soubor: {filename}")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)
                
                bbox = get_bbox_from_geojson(geojson_data)
                if bbox:
                    countries_data[country_code] = (country_name_from_file, bbox)
                    print(f"    Nalezen bounding box: {bbox}")
                else:
                    print(f"    Nepodařilo se získat bounding box pro {country_name_from_file} z {filename}.")

            except json.JSONDecodeError:
                print(f"Chyba: Soubor {filename} není platný JSON.")
            except Exception as e:
                print(f"Došlo k neočekávané chybě při zpracování {filename}: {e}")
    
    return countries_data

# --- Hlavní spouštěcí blok ---
if __name__ == "__main__":
    total_start_time = time.time()
    
    # 1. Generuj bounding boxy ze souborů GeoJSON
    print("Načítám bounding boxy zemí z GeoJSON souborů...")
    COUNTRIES_TO_PROCESS = generate_country_bboxes(folder_path=GEOJSON_DATA_FOLDER)
    
    if not COUNTRIES_TO_PROCESS:
        print("Nebyly nalezeny žádné bounding boxy zemí ke zpracování. Ujistěte se, že složka 'country_geojson_data' existuje a obsahuje GeoJSON soubory.")
        exit()
    
    print(f"\nCelkem zemí k prohledání: {len(COUNTRIES_TO_PROCESS)}")

    # Nastavení pro globální ukládání dat
    global_seen_ids = set() # Pro deduplikaci napříč všemi zeměmi
    global_geocoding_failures = [] # Pro záznam všech selhaných geokódování

    # Definice hlaviček CSV souboru
    fieldnames = [
        'id', 'lat', 'lon', 'city', 'state', 'country', 'scraped_country_code', 'scraped_country_name',
        'amenity', 'authentication:nfc', 'capacity',
        'capacity:car', 'motorcar', 'operator', 'operator:wikidata',
        'socket:schuko', 'socket:schuko:current', 'socket:schuko:voltage',
        'socket:type2', 'socket:type2:current', 'socket:type2:voltage'
    ]
    
    # Otevření/vytvoření CSV souboru a zápis hlavičky, pokud je prázdný
    file_exists = os.path.exists(MAIN_OUTPUT_FILENAME)
    file_is_empty = not file_exists or os.path.getsize(MAIN_OUTPUT_FILENAME) == 0

    try:
        with open(MAIN_OUTPUT_FILENAME, 'a' if file_exists and not file_is_empty else 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if file_is_empty:
                writer.writeheader()

            print("\nSpouštím scrapování dat o EV nabíječkách po zemích s geokódováním...")
            
            # Smyčka přes všechny země
            for country_code, (country_name, bbox_coords) in COUNTRIES_TO_PROCESS.items():
                print(f"\n--- Spouštím scrapování pro zemi: {country_name} ({country_code}) ---")
                country_start_time = time.time()

                min_lat, min_lon, max_lat, max_lon = bbox_coords
                target_boxes = generate_grid_boxes(min_lat, min_lon, max_lat, max_lon, STEP_LAT, STEP_LON)
                
                print(f"  Země {country_name} rozdělena do {len(target_boxes)} čtverců k prohledání.")

                current_country_elements_to_process = [] # Elementy pro aktuální zemi před geokódováním
                country_failed_boxes = [] # Lokální pro logování selhaných boxů pro danou zemi
                
                # Pro odhad času
                processed_boxes_count = 0
                box_processing_times = [] # Ukládáme časy zpracování jednotlivých boxů

                # První průchod pro stahování dat z Overpass API
                for i, bbox in enumerate(target_boxes):
                    box_start_time = time.time() # Čas začátku zpracování boxu
                    print(f"    Zpracovávám čtverec {i+1}/{len(target_boxes)} pro {country_name}: {bbox}")
                    
                    success = False
                    for attempt in range(MAX_RETRIES_OVERPASS):
                        osm_data = get_overpass_data(bbox, attempt + 1)
                        if osm_data and 'elements' in osm_data:
                            # Filtrujeme pouze uzly a přidáváme unikátní ID do global_seen_ids
                            for element in osm_data['elements']:
                                if element['type'] == 'node' and element['id'] not in global_seen_ids:
                                    current_country_elements_to_process.append(element)
                                    global_seen_ids.add(element['id'])
                            print(f"      Nalezeno {len(osm_data['elements'])} elementů, přidáno {len(current_country_elements_to_process) - (len(osm_data['elements']) - len([e for e in osm_data['elements'] if e['id'] in global_seen_ids]))} unikátních.")
                            success = True
                            break
                        elif attempt < MAX_RETRIES_OVERPASS - 1:
                            print(f"      Čekám {RETRY_DELAY_OVERPASS} sekund před dalším pokusem pro box {bbox}...")
                            time.sleep(RETRY_DELAY_OVERPASS)
                        else:
                            print(f"      Všechny pokusy pro box {bbox} selhaly pro {country_name}.")
                    
                    if not success:
                        country_failed_boxes.append(bbox)
                        # Zde můžeš volitelně ukládat failed_boxes pro každou zemi zvlášť:
                        # try:
                        #     with open(f"failed_boxes_{country_code}.json", 'w', encoding='utf-8') as f:
                        #         json.dump(country_failed_boxes, f, indent=4)
                        # except IOError as e:
                        #     print(f"Chyba při ukládání selhaných čtverců pro {country_code}: {e}")

                    time.sleep(QUERY_PAUSE_SECONDS) # Pauza mezi dotazy na Overpass

                    # Aktualizace odhadu času
                    box_end_time = time.time()
                    box_processing_time = box_end_time - box_start_time
                    box_processing_times.append(box_processing_time)
                    processed_boxes_count += 1

                    if processed_boxes_count > 0:
                        average_box_time = sum(box_processing_times) / processed_boxes_count
                        remaining_boxes = len(target_boxes) - processed_boxes_count
                        estimated_remaining_time_seconds = average_box_time * remaining_boxes
                        
                        # Převod na čitelnější formát H:MM:SS
                        hours, remainder = divmod(int(estimated_remaining_time_seconds), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        
                        print(f"    Odhadovaný zbývající čas pro {country_name}: {hours:02d}h {minutes:02d}m {seconds:02d}s")


                # Druhý průchod pro selhané čtverce pro aktuální zemi
                if country_failed_boxes:
                    print(f"\n  --- Spouštím druhý průchod pro {len(country_failed_boxes)} selhaných čtverců v {country_name}. ---")
                    retried_failed_boxes = []
                    for i, bbox in enumerate(country_failed_boxes):
                        box_start_time_retry = time.time() # Čas začátku zpracování opakovaného boxu
                        print(f"    Zpracovávám selhaný čtverec {i+1}/{len(country_failed_boxes)} pro {country_name}: {bbox}")
                        success = False
                        for attempt in range(MAX_RETRIES_OVERPASS):
                            osm_data = get_overpass_data(bbox, attempt + 1)
                            if osm_data and 'elements' in osm_data:
                                for element in osm_data['elements']:
                                    if element['type'] == 'node' and element['id'] not in global_seen_ids:
                                        current_country_elements_to_process.append(element)
                                        global_seen_ids.add(element['id'])
                                print(f"      Nalezeno {len(osm_data['elements'])} elementů v tomto selhaném čtverci.")
                                success = True
                                break
                            elif attempt < MAX_RETRIES_OVERPASS - 1:
                                print(f"      Čekám {RETRY_DELAY_OVERPASS} sekund před dalším pokusem pro selhaný box {bbox}...")
                                time.sleep(RETRY_DELAY_OVERPASS)
                            else:
                                print(f"      Všechny pokusy pro selhaný box {bbox} opět selhaly.")
                        if not success:
                            retried_failed_boxes.append(bbox)
                        time.sleep(QUERY_PAUSE_SECONDS)

                        # Aktualizace odhadu času po druhém průchodu (volitelné, ale užitečné)
                        box_processing_times.append(time.time() - box_start_time_retry)
                        processed_boxes_count += 1
                        if processed_boxes_count > 0:
                            average_box_time = sum(box_processing_times) / processed_boxes_count
                            remaining_boxes = len(target_boxes) - processed_boxes_count # Zbývá ještě pro druhý průchod
                            hours, remainder = divmod(int(average_box_time * remaining_boxes), 3600)
                            minutes, seconds = divmod(remainder, 60)
                            print(f"    Odhadovaný zbývající čas pro {country_name} (včetně druhého průchodu): {hours:02d}h {minutes:02d}m {seconds:02d}s")


                    if retried_failed_boxes:
                        print(f"  Tyto čtverce v {country_name} selhaly i po druhém průchodu ({len(retried_failed_boxes)}):")
                        for bbox in retried_failed_boxes:
                            print(f"      {bbox}")
                    print(f"  --- Druhý průchod pro {country_name} dokončen. ---")


                print(f"\n  --- Geokódování a ukládání {len(current_country_elements_to_process)} unikátních dat pro {country_name}. ---")
                processed_chargers_for_csv = []
                
                # Zde je odhad pro geokódování, ale je méně přesný, protože počet elementů se liší
                total_elements_for_geocoding = len(current_country_elements_to_process)
                if total_elements_for_geocoding > 0:
                    estimated_geocoding_time_seconds = total_elements_for_geocoding * GEOCODING_PAUSE_SECONDS
                    hours, remainder = divmod(int(estimated_geocoding_time_seconds), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    print(f"  Odhadovaný čas geokódování pro {country_name}: {hours:02d}h {minutes:02d}m {seconds:02d}s")

                # Geokódování a příprava dat pro zápis do CSV
                for element_idx, element in enumerate(current_country_elements_to_process):
                    tags = element.get('tags', {})
                    charger_info = {
                        'id': element['id'],
                        'lat': element.get('lat'),
                        'lon': element.get('lon'),
                        'amenity': tags.get('amenity', 'N/A'),
                        'scraped_country_code': country_code,
                        'scraped_country_name': country_name,
                    }
                    for field in fieldnames:
                        if field not in ['id', 'lat', 'lon', 'amenity', 'city', 'state', 'country', 'scraped_country_code', 'scraped_country_name']:
                            charger_info[field] = tags.get(field, 'N/A')

                    city, state, country = None, None, None
                    try:
                        lat_val = float(charger_info['lat'])
                        lon_val = float(charger_info['lon'])
                    except (ValueError, TypeError):
                        print(f"    Přeskočeno geokódování pro ID {charger_info['id']}: Neplatné souřadnice ({charger_info['lat']}, {charger_info['lon']}).")
                        charger_info['city'] = 'N/A'
                        charger_info['state'] = 'N/A'
                        charger_info['country'] = 'N/A'
                        global_geocoding_failures.append({'id': charger_info['id'], 'lat': charger_info['lat'], 'lon': charger_info['lon'], 'reason': 'Invalid_Coordinates', 'country': country_name})
                        processed_chargers_for_csv.append(charger_info)
                        continue

                    for attempt in range(MAX_RETRIES_GEOCODING):
                        city, state, country = get_location_details(lat_val, lon_val, attempt + 1)
                        if city is not None:
                            break
                        else:
                            if attempt < MAX_RETRIES_GEOCODING - 1:
                                print(f"    Geokódování pro ({lat_val}, {lon_val}) selhalo, zkouším znovu za {GEOCODING_PAUSE_SECONDS}s.")
                                time.sleep(GEOCODING_PAUSE_SECONDS)
                            else:
                                print(f"    Geokódování pro ({lat_val}, {lon_val}) selhalo po všech pokusech.")
                                global_geocoding_failures.append({'id': charger_info['id'], 'lat': charger_info['lat'], 'lon': charger_info['lon'], 'reason': 'GeocoderError', 'country': country_name})
                                city, state, country = 'N/A', 'N/A', 'N/A'
                    
                    charger_info['city'] = city
                    charger_info['state'] = state
                    charger_info['country'] = country
                    processed_chargers_for_csv.append(charger_info)
                    time.sleep(GEOCODING_PAUSE_SECONDS) # Důležitá pauza pro Nominatim
                
                # Zápis zpracovaných dat pro aktuální zemi do CSV
                if processed_chargers_for_csv:
                    writer.writerows(processed_chargers_for_csv)
                    print(f"  Úspěšně přidáno {len(processed_chargers_for_csv)} unikátních záznamů pro {country_name} do '{MAIN_OUTPUT_FILENAME}'.")
                else:
                    print(f"  Žádné unikátní nabíječky k přidání pro {country_name}.")

                country_end_time = time.time()
                print(f"Země {country_name} dokončena za {country_end_time - country_start_time:.2f} sekund.")
                
                # Volitelná delší pauza mezi zeměmi, aby se serverům trochu odlehčilo
                print("Pauza mezi zeměmi (30 sekund)...")
                time.sleep(30) 

    except IOError as e:
        print(f"Chyba při zápisu do souboru '{MAIN_OUTPUT_FILENAME}': {e}")

    total_end_time = time.time()
    print(f"\n--- Celý skript dokončen za {total_end_time - total_start_time:.2f} sekund. ---")
    
    # Uložení globálních selhaných geokódovacích dotazů
    if global_geocoding_failures:
        try:
            with open(FAILED_GEOCODING_LOG, 'w', encoding='utf-8') as f:
                json.dump(global_geocoding_failures, f, indent=4)
            print(f"Některé geokódovací dotazy selhaly. Detaily jsou v '{FAILED_GEOCODING_LOG}'.")
        except IOError as e:
            print(f"Chyba při ukládání selhaných geokódování do {FAILED_GEOCODING_LOG}: {e}")
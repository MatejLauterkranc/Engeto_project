import requests
import csv
import json
import time
import os
import glob
import shutil
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError
from shapely.geometry import shape, MultiPolygon, Polygon
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
import datetime
import sys # For redirecting output

# --- Configuration ---
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
GEOJSON_DATA_FOLDER = "country_geojson_data" # Folder with GeoJSON country boundary files
TEMP_OSM_DATA_FOLDER = "temp_osm_data" # Folder for temporary CSVs with raw OSM data (before geocoding)
FINAL_OUTPUT_FOLDER = "final_output_by_country" # Folder for final geocoded CSV files
LOGS_FOLDER = "logs" # Folder for log files
FAILED_GEOCODING_LOG = os.path.join(LOGS_FOLDER, "failed_geocoding_global.json") # Log for geocoding failures

# Step size for dividing the area into smaller squares (in degrees)
STEP_LAT, STEP_LON = 0.5, 0.5

# Maximum number of grid squares per output file for a country in temp_osm_data
# Helps keep temporary files smaller and more manageable
MAX_SQUARES_PER_COUNTRY_PART_FILE = 2000

# Pause between individual queries to Overpass API (in seconds)
QUERY_PAUSE_SECONDS = 5

# Settings for retrying Overpass API queries
MAX_RETRIES_OVERPASS = 3
RETRY_DELAY_OVERPASS = 10

# Settings for reverse geocoding (Nominatim)
GEOCODING_PAUSE_SECONDS = 1.0 # Nominatim recommends min. 1 query per second
MAX_RETRIES_GEOCODING = 2

# Maximum number of parallel processes
MAX_WORKERS = os.cpu_count() or 4 # Use all available CPU cores, or default to 4

# User agent for Nominatim - MUST CHANGE!
NOMINATIM_USER_AGENT = "EV_Charger_Scraper_Global/1.0 (your_email@example.com)"

# Suppress UserWarnings from shapely for invalid geometries
warnings.filterwarnings("ignore", category=UserWarning, module='shapely')

# --- Global CSV Column Configuration ---
# These are the fields we expect in the final CSV
ALL_FIELDNAMES = [
    'id', 'lat', 'lon', 'amenity',
    # Added geocoding columns
    'city', 'state', 'country', 'scraped_country_code', 'scraped_country_name',
    # Example of other OSM tags that might be of interest
    'authentication:nfc', 'capacity', 'capacity:car', 'motorcar', 'operator',
    'operator:wikidata', 'socket:schuko', 'socket:schuko:current',
    'socket:schuko:voltage', 'socket:type2', 'socket:type2:current',
    'socket:type2:voltage', 'ref', 'addr:housenumber', 'addr:street',
    'addr:postcode', 'brand', 'charge', 'opening_hours', 'fee'
]

# Columns that are required for geocoding (should be filled by geocoding phase)
GEOCODED_COLUMNS = ['city', 'state', 'country', 'scraped_country_code', 'scraped_country_name']

# --- Logging to File ---
class Tee:
    """
    A class to redirect stdout and stderr to multiple destinations (e.g., console and file).
    """
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush() # Ensure data is written immediately
    def flush(self) :
        for f in self.files:
            f.flush()

# --- Helper Functions for Overpass API ---
def get_overpass_data(bbox, current_attempt=1):
    """
    Downloads EV charging station data from Overpass API for a given bounding box.
    Implements retries.
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
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Error downloading data for box {bbox} (attempt {current_attempt}): {e}")
        return None

# --- Helper Functions for Geocoding ---
def get_location_details(lat, lon, geolocator_instance, current_attempt=1):
    """
    Performs reverse geocoding for given coordinates and returns city, state, and country.
    Requires a geolocator instance.
    """
    try:
        location = geolocator_instance.reverse((lat, lon), language="en", timeout=10)
        if location and location.address:
            address = location.raw.get('address', {})
            city = address.get('city') or address.get('town') or address.get('village') or 'N/A'
            state = address.get('state') or 'N/A'
            country = address.get('country') or 'N/A'
            return city, state, country
        return 'N/A', 'N/A', 'N/A'
    except (GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError) as e:
        # print(f"Geocoding error for coordinates ({lat}, {lon}) (attempt {current_attempt}): {e}") # Logged in main process
        return None, None, None # Return None to indicate failure and prompt a retry
    except Exception as e:
        print(f"Unexpected error during geocoding ({lat}, {lon}): {e}")
        return 'N/A', 'N/A', 'N/A'

# --- Function for Generating Grid Bounding Boxes ---
def generate_grid_boxes(min_lat, min_lon, max_lat, max_lon, step_lat, step_lon):
    """
    Generates bounding box coordinates to cover a given area with a grid.
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

# --- Function for Getting Bounding Boxes from GeoJSON files ---
def get_bbox_from_geojson(geojson_data):
    """
    Extracts the overall bounding box (min_lat, min_lon, max_lat, max_lon)
    from GeoJSON data.
    """
    if not geojson_data or 'features' not in geojson_data:
        # print("   Debug: No GeoJSON data or features found.") # Debug
        return None

    all_coordinates = []
    for feature in geojson_data['features']:
        geometry = feature.get('geometry')
        if geometry and 'coordinates' in geometry:
            try:
                geom = shape(geometry)
                if geom.is_valid:
                    min_lon, min_lat, max_lon, max_lat = geom.bounds
                    all_coordinates.append((min_lon, min_lat, max_lon, max_lat))
                else:
                    print(f"Warning: Invalid geometry in GeoJSON file. Type: {geometry.get('type')}. Skipping feature.")
            except Exception as e:
                print(f"Error processing geometry in feature: {e}. Geometry type: {geometry.get('type')}. Skipping feature.")

    if not all_coordinates:
        # print("   Debug: No valid coordinates found after processing all features.") # Debug
        return None

    global_min_lon = min(bbox[0] for bbox in all_coordinates)
    global_min_lat = min(bbox[1] for bbox in all_coordinates)
    global_max_lon = max(bbox[2] for bbox in all_coordinates)
    global_max_lat = max(bbox[3] for bbox in all_coordinates)

    return (global_min_lat, global_min_lon, global_max_lat, global_max_lon)

def generate_country_bboxes(folder_path):
    """
    Iterates through all GeoJSON files in the given folder and returns a dictionary
    {country_code: (country_name, bbox_tuple, num_squares)}.
    """
    countries_data = {}
    
    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_path}' not found. Make sure the GeoJSON files are there.")
        return countries_data

    print(f"Loading country bounding boxes from folder: '{folder_path}'")
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            filepath = os.path.join(folder_path, filename)
            country_name_from_file = os.path.splitext(filename)[0].replace("_", " ").title()
            country_code = country_name_from_file[:3].upper() # For simplicity, ideally map by ISO codes

            print(f"   Processing file: {filename}")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)
                
                bbox = get_bbox_from_geojson(geojson_data)
                if bbox:
                    # Here we calculate the number of squares
                    num_squares = len(generate_grid_boxes(bbox[0], bbox[1], bbox[2], bbox[3], STEP_LAT, STEP_LON))
                    countries_data[country_code] = (country_name_from_file, bbox, num_squares)
                    print(f"     Found bounding box: {bbox}, Number of squares: {num_squares}")
                else:
                    print(f"     Failed to get bounding box for {country_name_from_file} from {filename}.")

            except json.JSONDecodeError:
                print(f"Error: File {filename} is not a valid JSON.")
            except Exception as e:
                print(f"An unexpected error occurred while processing {filename}: {e}")
    
    return countries_data

# --- Phase 1: Downloading data from Overpass API ---
def download_osm_data_for_country_part(country_data, temp_folder, global_fieldnames_subset):
    """
    Downloads charging station data for a given country (or part of it)
    and saves raw data (ID, lat, lon, OSM tags) to a temporary CSV file.
    """
    country_code, (country_name, bbox_coords, num_squares_total) = country_data
    
    print(f"\n--- Starting OSM data download for {country_name} ({country_code}) ---")
    
    min_lat, min_lon, max_lat, max_lon = bbox_coords
    all_country_boxes = generate_grid_boxes(min_lat, min_lon, max_lat, max_lon, STEP_LAT, STEP_LON)
    
    num_parts = (len(all_country_boxes) + MAX_SQUARES_PER_COUNTRY_PART_FILE - 1) // MAX_SQUARES_PER_COUNTRY_PART_FILE
    
    overall_elements_downloaded = 0
    
    for part_index in range(num_parts):
        part_suffix = ""
        if num_parts > 1:
            part_suffix = f" [Part {part_index + 1}]"
        
        output_filename_for_part = os.path.join(temp_folder, f"ev_chargers_osm_raw_{country_name.replace(' ', '_').lower()}{part_suffix}.csv")

        if os.path.exists(output_filename_for_part):
            print(f"\n  --- File '{output_filename_for_part}' already exists. Skipping this part for {country_name}. ---")
            # If the file exists, load the number of elements for logging
            try:
                with open(output_filename_for_part, 'r', newline='', encoding='utf-8') as infile:
                    reader = csv.DictReader(infile)
                    overall_elements_downloaded += sum(1 for row in reader)
            except Exception as e:
                print(f"  Warning: Error reading row count from existing file '{output_filename_for_part}': {e}")
            continue

        start_idx = part_index * MAX_SQUARES_PER_COUNTRY_PART_FILE
        end_idx = min((part_index + 1) * MAX_SQUARES_PER_COUNTRY_PART_FILE, len(all_country_boxes))
        
        target_boxes_part = all_country_boxes[start_idx:end_idx]
        
        if num_parts > 1:
            print(f"\n  --- Processing {country_name} (Part {part_index + 1}/{num_parts}, Squares {start_idx + 1}-{end_idx}) ---")
        else:
             print(f"\n  --- Processing {country_name} (Squares {start_idx + 1}-{end_idx}) ---")
        
        current_country_elements_to_save = []
        seen_ids_for_part = set() # Deduplication within this country part
        country_failed_boxes_part = []
        
        processed_boxes_count_part = 0
        box_processing_times_part = []

        for i, bbox in enumerate(target_boxes_part):
            box_start_time = time.time()
            print(f"    Processing square {i+1}/{len(target_boxes_part)} for {country_name}{part_suffix}: {bbox}")
            
            success = False
            for attempt in range(MAX_RETRIES_OVERPASS):
                osm_data = get_overpass_data(bbox, attempt + 1)
                if osm_data and 'elements' in osm_data:
                    for element in osm_data['elements']:
                        if element['id'] not in seen_ids_for_part:
                            seen_ids_for_part.add(element['id'])
                            # Add basic info and all tags
                            charger_info = {
                                'id': element['id'],
                                'lat': element.get('lat'),
                                'lon': element.get('lon'),
                                'amenity': element.get('tags', {}).get('amenity', 'N/A'),
                                'scraped_country_code': country_code, # Add country info from GeoJSON
                                'scraped_country_name': country_name
                            }
                            # Add all other OSM tags that are in our ALL_FIELDNAMES
                            for field in ALL_FIELDNAMES:
                                if field not in charger_info and field not in GEOCODED_COLUMNS:
                                    charger_info[field] = element.get('tags', {}).get(field, 'N/A')
                            current_country_elements_to_save.append(charger_info)
                    print(f"      Found {len(osm_data['elements'])} elements (total unique {len(seen_ids_for_part)}).")
                    success = True
                    break
                elif attempt < MAX_RETRIES_OVERPASS - 1:
                    print(f"      Waiting {RETRY_DELAY_OVERPASS} seconds before next attempt for box {bbox}...")
                    time.sleep(RETRY_DELAY_OVERPASS)
                else:
                    print(f"      All attempts for box {bbox} failed for {country_name}{part_suffix}.")
            
            if not success:
                country_failed_boxes_part.append(bbox)

            time.sleep(QUERY_PAUSE_SECONDS)

            box_end_time = time.time()
            box_processing_time = box_end_time - box_start_time
            box_processing_times_part.append(box_processing_time)
            processed_boxes_count_part += 1

            if processed_boxes_count_part > 0:
                average_box_time = sum(box_processing_times_part) / processed_boxes_count_part
                remaining_boxes = len(target_boxes_part) - processed_boxes_count_part
                estimated_remaining_time_seconds = average_box_time * remaining_boxes
                
                hours, remainder = divmod(int(estimated_remaining_time_seconds), 3600)
                minutes, seconds = divmod(remainder, 60)
                
                print(f"    Estimated remaining time for {country_name}{part_suffix}: {hours:02d}h {minutes:02d}m {seconds:02d}s")

        # Second pass for failed squares for this country part (if needed)
        if country_failed_boxes_part:
            print(f"\n  --- Initiating second pass for {len(country_failed_boxes_part)} failing squares in {country_name}{part_suffix}. ---")
            retried_failed_boxes_part = []
            for i, bbox in enumerate(country_failed_boxes_part):
                box_start_time_retry = time.time()
                print(f"    Processing failing square {i+1}/{len(country_failed_boxes_part)} for {country_name}{part_suffix}: {bbox}")
                success = False
                for attempt in range(MAX_RETRIES_OVERPASS):
                    osm_data = get_overpass_data(bbox, attempt + 1)
                    if osm_data and 'elements' in osm_data:
                        for element in osm_data['elements']:
                            if element['id'] not in seen_ids_for_part: # Deduplicate again
                                seen_ids_for_part.add(element['id'])
                                charger_info = {
                                    'id': element['id'],
                                    'lat': element.get('lat'),
                                    'lon': element.get('lon'),
                                    'amenity': element.get('tags', {}).get('amenity', 'N/A'),
                                    'scraped_country_code': country_code,
                                    'scraped_country_name': country_name
                                }
                                for field in ALL_FIELDNAMES:
                                    if field not in charger_info and field not in GEOCODED_COLUMNS:
                                        charger_info[field] = element.get('tags', {}).get(field, 'N/A')
                                current_country_elements_to_save.append(charger_info)
                        print(f"      Found {len(osm_data['elements'])} elements in this failing square.")
                        success = True
                        break
                    elif attempt < MAX_RETRIES_OVERPASS - 1:
                        print(f"      Waiting {RETRY_DELAY_OVERPASS} seconds before next attempt for failing box {bbox}...")
                        time.sleep(RETRY_DELAY_OVERPASS)
                    else:
                        print(f"      All attempts for failing box {bbox} failed again.")
                if not success:
                    retried_failed_boxes_part.append(bbox)
                time.sleep(QUERY_PAUSE_SECONDS)

        # Saving downloaded OSM data for this country part
        if current_country_elements_to_save:
            try:
                with open(output_filename_for_part, 'w', newline='', encoding='utf-8') as part_csvfile:
                    writer = csv.DictWriter(part_csvfile, fieldnames=[f for f in ALL_FIELDNAMES if f not in GEOCODED_COLUMNS])
                    writer.writeheader()
                    # Write only the fields available at this stage
                    rows_to_write = []
                    for row in current_country_elements_to_save:
                        clean_row = {key: row.get(key, 'N/A') for key in writer.fieldnames}
                        rows_to_write.append(clean_row)
                    writer.writerows(rows_to_write)
                print(f"  Successfully saved {len(current_country_elements_to_save)} unique records for {country_name}{part_suffix} to '{output_filename_for_part}'.")
                overall_elements_downloaded += len(current_country_elements_to_save)
            except IOError as e:
                print(f"  Error writing country part file '{output_filename_for_part}': {e}")
        else:
            print(f"  No unique chargers to download for {country_name}{part_suffix}.")
    
    print(f"\n--- OSM data download for {country_name} ({country_code}) completed. Total unique elements downloaded: {overall_elements_downloaded}. ---")
    return overall_elements_downloaded # Return total count of downloaded elements for this country

# --- Phase 2: Geocoding Downloaded Data ---
def geocode_country_data(country_data, temp_folder, final_folder, all_fieldnames, geocoded_columns):
    """
    Loads raw OSM data from temp_folder, performs geocoding (only for missing data),
    and saves the complete file to final_folder.
    """
    country_code, (country_name, bbox_coords, num_squares_total) = country_data
    
    geolocator_process = Nominatim(user_agent=NOMINATIM_USER_AGENT)
    
    print(f"\n--- Starting geocoding for {country_name} ({country_code}) ---")
    country_start_time = time.time()

    # Get all temporary files for the given country
    raw_osm_files = glob.glob(os.path.join(temp_folder, f"ev_chargers_osm_raw_{country_name.replace(' ', '_').lower()}*.csv"))
    if not raw_osm_files:
        print(f"  No raw OSM files found for {country_name} in folder '{temp_folder}'. Skipping geocoding.")
        return []

    # Load all raw data from temporary files
    all_raw_elements = {}
    for filepath in raw_osm_files:
        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                for row in reader:
                    # Ensure all necessary keys exist
                    clean_row = {field: row.get(field, 'N/A') for field in all_fieldnames if field not in geocoded_columns}
                    # Add ID, lat, lon
                    clean_row['id'] = row.get('id')
                    clean_row['lat'] = row.get('lat')
                    clean_row['lon'] = row.get('lon')
                    clean_row['scraped_country_code'] = row.get('scraped_country_code')
                    clean_row['scraped_country_name'] = row.get('scraped_country_name')
                    all_raw_elements[row['id']] = clean_row
        except Exception as e:
            print(f"  Error reading RAW file '{filepath}': {e}")
            
    if not all_raw_elements:
        print(f"  No RAW data to geocode for {country_name}. Skipping.")
        return []

    # Load existing final file (if any) to identify already geocoded records
    final_output_file = os.path.join(final_folder, f"ev_chargers_geocoded_{country_name.replace(' ', '_').lower()}.csv")
    existing_geocoded_data = {}
    if os.path.exists(final_output_file):
        print(f"  Found existing final file '{final_output_file}'. Loading already geocoded data.")
        try:
            with open(final_output_file, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                for row in reader:
                    # Check if the row has filled geocoding fields
                    if all(row.get(col, 'N/A') not in ['N/A', ''] for col in geocoded_columns):
                        existing_geocoded_data[row['id']] = row
                    else:
                        # If any of the geocoded_columns is 'N/A' or empty, we consider it incomplete and will re-geocode it
                        pass # This row will not be in existing_geocoded_data, so it will be reprocessed
        except Exception as e:
            print(f"  Warning: Error loading existing final file '{final_output_file}': {e}. Recomputing everything.")
            existing_geocoded_data = {} # Reset if failed to load

    processed_chargers_for_csv = []
    local_geocoding_failures = []
    
    total_elements_to_geocode = 0
    for osm_id, element in all_raw_elements.items():
        if osm_id not in existing_geocoded_data:
            total_elements_to_geocode += 1

    if total_elements_to_geocode > 0:
        estimated_geocoding_time_seconds = total_elements_to_geocode * GEOCODING_PAUSE_SECONDS
        hours, remainder = divmod(int(estimated_geocoding_time_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"  Estimated geocoding time for {country_name}: {hours:02d}h {minutes:02d}m {seconds:02d}s ({total_elements_to_geocode} elements to geocode).")
    else:
        print(f"  All records for {country_name} appear to be already geocoded. Skipping geocoding.")
        # If all records are already geocoded, just copy the existing data
        processed_chargers_for_csv = list(existing_geocoded_data.values())
        if processed_chargers_for_csv:
            try:
                with open(final_output_file, 'w', newline='', encoding='utf-8') as outfile:
                    writer = csv.DictWriter(outfile, fieldnames=all_fieldnames)
                    writer.writeheader()
                    writer.writerows(processed_chargers_for_csv)
                print(f"  Successfully re-written {len(processed_chargers_for_csv)} records for {country_name} to '{final_output_file}' (no new geocoding).")
            except IOError as e:
                print(f"  Error writing final file '{final_output_file}': {e}")
        return [] # No new geocoding errors if nothing was geocoded

    # Geocoding and preparing data for writing
    for element_idx, (osm_id, element) in enumerate(all_raw_elements.items()):
        
        # If the element is already geocoded, add it to the list and skip geocoding
        if osm_id in existing_geocoded_data:
            processed_chargers_for_csv.append(existing_geocoded_data[osm_id])
            continue
            
        if (element_idx + 1) % 100 == 0: # Log progress every 100 elements
             print(f"  Geocoding {element_idx + 1}/{len(all_raw_elements)} for {country_name} (ID: {element.get('id')})...")

        charger_info = element # Start with raw data
        
        city, state, country = None, None, None
        try:
            lat_val = float(charger_info['lat'])
            lon_val = float(charger_info['lon'])
        except (ValueError, TypeError):
            print(f"  Skipping geocoding for ID {charger_info['id']}: Invalid coordinates ({charger_info['lat']}, {charger_info['lon']}).")
            charger_info['city'] = 'N/A'
            charger_info['state'] = 'N/A'
            charger_info['country'] = 'N/A'
            local_geocoding_failures.append({'id': charger_info['id'], 'lat': charger_info['lat'], 'lon': charger_info['lon'], 'reason': 'Invalid_Coordinates', 'country': country_name})
            processed_chargers_for_csv.append(charger_info)
            continue

        success_geocoding = False
        for attempt in range(MAX_RETRIES_GEOCODING):
            city, state, country = get_location_details(lat_val, lon_val, geolocator_process, attempt + 1)
            if city is not None: # If the result is valid (not None)
                success_geocoding = True
                break
            else:
                if attempt < MAX_RETRIES_GEOCODING - 1:
                    print(f"  Geocoding for ({lat_val}, {lon_val}) failed, retrying in {GEOCODING_PAUSE_SECONDS}s.")
                    time.sleep(GEOCODING_PACODING_SECONDS)
                else:
                    print(f"  Geocoding for ({lat_val}, {lon_val}) failed after all attempts.")
                    local_geocoding_failures.append({'id': charger_info['id'], 'lat': charger_info['lat'], 'lon': charger_info['lon'], 'reason': 'GeocoderError', 'country': country_name})
                    city, state, country = 'N/A', 'N/A', 'N/A' # Set to N/A after failure
        
        charger_info['city'] = city
        charger_info['state'] = state
        charger_info['country'] = country
        # scraped_country_code and scraped_country_name should already be in charger_info from Phase 1
        processed_chargers_for_csv.append(charger_info)
        time.sleep(GEOCODING_PAUSE_SECONDS) # Important pause for Nominatim
    
    # Writing processed data to the final CSV file
    if processed_chargers_for_csv:
        try:
            # Ensure data list is sorted by ID for consistent output
            processed_chargers_for_csv.sort(key=lambda x: x.get('id', 0))
            
            with open(final_output_file, 'w', newline='', encoding='utf-8') as final_csvfile:
                final_writer = csv.DictWriter(final_csvfile, fieldnames=all_fieldnames)
                final_writer.writeheader()
                
                # Write rows, ensuring all fields are present
                rows_to_write_final = []
                for row_data in processed_chargers_for_csv:
                    clean_row = {field: row_data.get(field, 'N/A') for field in all_fieldnames}
                    rows_to_write_final.append(clean_row)
                final_writer.writerows(rows_to_write_final)

            print(f"  Successfully saved {len(processed_chargers_for_csv)} records for {country_name} to '{final_output_file}'.")
        except IOError as e:
            print(f"  Error writing final file '{final_output_file}': {e}")
    else:
        print(f"  No records to save for {country_name} to the final file.")

    country_end_time = time.time()
    print(f"\n--- Geocoding for {country_name} completed in {country_end_time - country_start_time:.2f} seconds. ---")
    
    return local_geocoding_failures # Return geocoding failures for this country

# --- Main Execution Block ---
if __name__ == "__main__":
    # Create folders if they don't exist
    os.makedirs(TEMP_OSM_DATA_FOLDER, exist_ok=True)
    os.makedirs(FINAL_OUTPUT_FOLDER, exist_ok=True)
    os.makedirs(LOGS_FOLDER, exist_ok=True)

    # Setup logging to file
    log_filename = datetime.datetime.now().strftime("scrape_log_%Y-%m-%d_%H-%M-%S.txt")
    log_filepath = os.path.join(LOGS_FOLDER, log_filename)
    
    # Redirect standard output and error output
    f_log = open(log_filepath, 'w', encoding='utf-8')
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = Tee(original_stdout, f_log)
    sys.stderr = Tee(original_stderr, f_log)

    print(f"Logging progress to file: '{log_filepath}'")
    print(f"Temporary OSM data will be saved in: '{TEMP_OSM_DATA_FOLDER}'")
    print(f"Final geocoded data will be saved in: '{FINAL_OUTPUT_FOLDER}'")

    total_script_start_time = time.time()

    # 1. Generating bounding boxes from GeoJSON files
    print("\nLoading country bounding boxes from GeoJSON files and calculating square counts...")
    COUNTRIES_DATA_RAW = generate_country_bboxes(folder_path=GEOJSON_DATA_FOLDER)
    
    if not COUNTRIES_DATA_RAW:
        print("No country bounding boxes found to process. Ensure 'country_geojson_data' folder exists and contains GeoJSON files.")
        sys.exit(1)
    
    # Sort countries by number of squares (smallest to largest)
    sorted_countries_list = sorted(COUNTRIES_DATA_RAW.items(), key=lambda item: item[1][2])
    
    print("\nList of countries sorted by number of search squares:")
    for code, (name, bbox, num_squares) in sorted_countries_list:
        print(f"- {name} ({code}): {num_squares} squares")

    print(f"\nTotal countries to process: {len(sorted_countries_list)}")

    # --- PHASE 1: Downloading data from Overpass API ---
    print("\n\n--- PHASE 1: STARTING OVERPASS API DATA DOWNLOAD ---")
    phase1_start_time = time.time()
    
    # Get a set of already existing files in temp_osm_data (for checking what to skip)
    existing_temp_osm_files = {os.path.basename(f) for f in glob.glob(os.path.join(TEMP_OSM_DATA_FOLDER, "*.csv"))}
    print(f"Found {len(existing_temp_osm_files)} existing temporary OSM files. These will be skipped if complete.")
    # for f_name in sorted(list(existing_temp_osm_files)):
    #     print(f"  - {f_name}")

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures_phase1 = []
        for country_code, country_info in sorted_countries_list:
            # Pass the entire country_data object, as country_info already contains num_squares
            futures_phase1.append(executor.submit(download_osm_data_for_country_part,
                                                  (country_code, country_info),
                                                  TEMP_OSM_DATA_FOLDER,
                                                  ALL_FIELDNAMES)) # Pass ALL_FIELDNAMES to determine columns

        for future in as_completed(futures_phase1):
            try:
                downloaded_count = future.result()
                # print(f"Completed OSM data download. Total unique elements downloaded: {downloaded_count}")
            except Exception as exc:
                print(f'Data download process for a country generated an exception: {exc}')
    
    phase1_end_time = time.time()
    print(f"\n--- PHASE 1 COMPLETED in {phase1_end_time - phase1_start_time:.2f} seconds. ---")


    # --- PHASE 2: Geocoding Data ---
    print("\n\n--- PHASE 2: STARTING DATA GEOCODING ---")
    phase2_start_time = time.time()
    
    global_geocoding_failures = [] # For recording all geocoding failures

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures_phase2 = []
        for country_code, country_info in sorted_countries_list:
            futures_phase2.append(executor.submit(geocode_country_data,
                                                  (country_code, country_info),
                                                  TEMP_OSM_DATA_FOLDER,
                                                  FINAL_OUTPUT_FOLDER,
                                                  ALL_FIELDNAMES,
                                                  GEOCODED_COLUMNS))

        for future in as_completed(futures_phase2):
            try:
                country_failed_geocodings = future.result()
                global_geocoding_failures.extend(country_failed_geocodings)
            except Exception as exc:
                print(f'Geocoding process for a country generated an exception: {exc}')

    phase2_end_time = time.time()
    print(f"\n--- PHASE 2 COMPLETED in {phase2_end_time - phase2_start_time:.2f} seconds. ---")

    # --- Conclusion ---
    total_script_end_time = time.time()
    print(f"\n--- Entire script completed in {total_script_end_time - total_script_start_time:.2f} seconds. ---")
    
    # Save global geocoding failures
    if global_geocoding_failures:
        try:
            with open(FAILED_GEOCODING_LOG, 'w', encoding='utf-8') as f:
                json.dump(global_geocoding_failures, f, indent=4)
            print(f"Some geocoding queries failed. Details are in '{FAILED_GEOCODING_LOG}'.")
        except IOError as e:
            print(f"Error saving geocoding failures to {FAILED_GEOCODING_LOG}: {e}")
    else:
        print("All geocoding queries were successful (or were skipped because data already existed).")

    # Restore original stdout and stderr
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    f_log.close()
    print(f"\nProgress has been logged to file: {log_filepath}")
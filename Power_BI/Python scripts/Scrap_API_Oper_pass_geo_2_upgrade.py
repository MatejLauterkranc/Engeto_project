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
from concurrent.futures import ProcessPoolExecutor, as_completed # Import for parallel processing
import sys # Import for sys.stdout.write and sys.stdout.flush

# Suppress UserWarnings from shapely for invalid geometries,
# to avoid cluttering the output, but still log them.
warnings.filterwarnings("ignore", category=UserWarning, module='shapely')


# --- Configuration ---
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
MAIN_OUTPUT_FILENAME = "ev_chargers_global_with_location.csv"
FAILED_GEOCODING_LOG = "failed_geocoding_global.json"
GEOJSON_DATA_FOLDER = "country_geojson_data" # Folder with country GeoJSON files
TEMP_COUNTRY_DATA_FOLDER = "temp_country_data_2" # Folder for temporary country CSVs

# Step size for dividing the area into smaller squares (in degrees)
STEP_LAT, STEP_LON = 0.05, 0.05

# Maximum number of squares per individual country output file
MAX_SQUARES_PER_COUNTRY_FILE = 2000

# Pause between individual queries to Overpass API (in seconds)
QUERY_PAUSE_SECONDS = 5 # Be careful when increasing, it might lead to blocking

# Settings for Overpass API retries
MAX_RETRIES_OVERPASS = 3
RETRY_DELAY_OVERPASS = 10

# Settings for reverse geocoding (Nominatim)
GEOCODING_PAUSE_SECONDS = 1.0 # Nominatim recommends min. 1 query per second
MAX_RETRIES_GEOCODING = 2

# Maximum number of parallel processes
MAX_WORKERS = os.cpu_count() or 4 # Use all CPU cores available, or default to 4

# Initialize Nominatim geocoder (NOTE: geolocator needs to be initialized per process,
# or passed as a callable factory for ProcessPoolExecutor to work correctly)
# For simplicity, we'll initialize it inside the process_country function.
# PLEASE, replace this with something specific to your application!
# geolocator = Nominatim(user_agent="EV_Charger_Scraper_Global/1.0 (your_email@example.com)")


# --- Helper functions for Overpass API ---
def get_overpass_data(bbox, current_attempt=1):
    """
    Downloads charging station data from Overpass API for the given bounding box.
    Implements retries.
    """
    min_lat, min_lon, max_lat, max_lon = bbox

    # Overpass query to find charging stations within the bounding box
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
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Error downloading data for box {bbox} (attempt {current_attempt}): {e}")
        return None

# --- Helper functions for geocoding ---
def get_location_details(lat, lon, geolocator_instance, current_attempt=1):
    """
    Performs reverse geocoding for the given coordinates and returns city, state, and country.
    Requires a geolocator instance.
    """
    try:
        # Perform reverse geocoding with a timeout and specify English language for results
        location = geolocator_instance.reverse((lat, lon), language="en", timeout=10)
        if location and location.address:
            # Extract address components, preferring city, town, or village
            address = location.raw.get('address', {})
            city = address.get('city') or address.get('town') or address.get('village') or 'N/A'
            state = address.get('state') or 'N/A'
            country = address.get('country') or 'N/A'
            return city, state, country
        return 'N/A', 'N/A', 'N/A' # Default if no location or address found
    except (GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError) as e:
        # Handle specific geocoding service errors
        print(f"Error geocoding coordinates ({lat}, {lon}) (attempt {current_attempt}): {e}")
        return None, None, None # Return None to indicate a retryable error
    except Exception as e:
        # Catch any other unexpected errors during geocoding
        print(f"Unexpected error during geocoding ({lat}, {lon}): {e}")
        return 'N/A', 'N/A', 'N/A' # Return 'N/A' for non-retryable errors

# --- Function for generating a grid of bounding boxes ---
def generate_grid_boxes(min_lat, min_lon, max_lat, max_lon, step_lat, step_lon):
    """
    Generates bounding box coordinates to cover the given area with a grid.
    Each box is (min_lat, min_lon, max_lat_for_box, max_lon_for_box).
    """
    boxes = []
    current_lat = min_lat
    while current_lat < max_lat:
        current_lon = min_lon
        while current_lon < max_lon:
            # Ensure the last box does not exceed the max_lat/max_lon
            box_max_lat = min(current_lat + step_lat, max_lat)
            box_max_lon = min(current_lon + step_lon, max_lon)
            boxes.append((current_lat, current_lon, box_max_lat, box_max_lon))
            current_lon += step_lon
        current_lat += step_lat
    return boxes

# --- Function for getting Bounding Boxes from GeoJSON files ---
def get_bbox_from_geojson(geojson_data):
    """
    Extracts the combined bounding box (min_lat, min_lon, max_lat, max_lon)
    from GeoJSON data, considering all features within the file.
    Handles potentially invalid geometries by logging warnings.
    """
    if not geojson_data or 'features' not in geojson_data:
        # print("  Debug: No GeoJSON data or features found.") # Debug message
        return None

    all_coordinates = [] # To store bounding box of each valid feature
    for feature in geojson_data['features']:
        geometry = feature.get('geometry')
        if geometry and 'coordinates' in geometry:
            try:
                geom = shape(geometry) # Create a shapely geometry object
                
                if geom.is_valid:
                    min_lon, min_lat, max_lon, max_lat = geom.bounds # Get bounds of the current geometry
                    all_coordinates.append((min_lon, min_lat, max_lon, max_lat))
                else:
                    # Log a warning if geometry is invalid, but continue processing
                    print(f"Warning: Invalid geometry in GeoJSON file. Type: {geometry.get('type')}. Skipping feature.")
            except Exception as e:
                # Catch errors during geometry processing
                print(f"Error processing geometry in feature: {e}. Geometry type: {geometry.get('type')}. Skipping feature.")
                
    if not all_coordinates: 
        # print("  Debug: No valid coordinates found after processing all features.") # Debug message
        return None # Return None if no valid bounding boxes could be extracted

    # Calculate the overall bounding box encompassing all valid feature bounding boxes
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
        print(f"Error: Folder '{folder_path}' not found. Make sure the files are there.")
        return countries_data

    print(f"Loading country bounding boxes from folder: '{folder_path}'")
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            filepath = os.path.join(folder_path, filename)
            # Derive country name and a simplified code from the filename
            country_name_from_file = os.path.splitext(filename)[0].replace("_", " ").title()
            country_code = country_name_from_file[:3].upper() # For simplicity, ideally map by ISO codes

            print(f"  Processing file: {filename}")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)
                
                bbox = get_bbox_from_geojson(geojson_data)
                if bbox:
                    # Calculate the number of grid squares required for this country's bounding box
                    num_squares = len(generate_grid_boxes(bbox[0], bbox[1], bbox[2], bbox[3], STEP_LAT, STEP_LON))
                    countries_data[country_code] = (country_name_from_file, bbox, num_squares)
                    print(f"    Bounding box found: {bbox}, Number of squares: {num_squares}")
                else:
                    print(f"    Failed to get bounding box for {country_name_from_file} from {filename}. Skipping.")

            except json.JSONDecodeError:
                print(f"Error: File {filename} is not valid JSON. Skipping.")
            except Exception as e:
                print(f"An unexpected error occurred while processing {filename}: {e}. Skipping.")
    
    return countries_data

# --- Function to merge all individual CSV files into one ---
def merge_csv_files(input_folder, output_filename, fieldnames):
    """
    Merges all CSV files in the input_folder into a single output_filename.
    Assumes all input CSVs have the same header row. Deduplicates records based on 'id'.
    """
    print(f"\n--- Merging all individual country CSVs from '{input_folder}' into '{output_filename}' ---")
    all_rows = []
    seen_ids_for_merge = set() # Set to track unique IDs during merging for deduplication
    
    # Get all CSV files in the temporary folder
    csv_files = glob.glob(os.path.join(input_folder, "*.csv"))
    
    if not csv_files:
        print("No individual country CSV files found to merge.")
        return

    # Sort files for consistent merging order (optional, but good practice)
    csv_files.sort()

    for i, filepath in enumerate(csv_files):
        print(f"  Reading file {i+1}/{len(csv_files)}: {os.path.basename(filepath)}")
        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                
                # Basic check if headers match. If not, print a warning.
                # Note: This is a soft check, actual merging uses 'fieldnames' explicitly.
                if reader.fieldnames and set(reader.fieldnames) != set(fieldnames):
                    print(f"Warning: Fieldnames in {os.path.basename(filepath)} do not fully match expected fieldnames. Merging might have inconsistencies.")

                for row in reader:
                    # Deduplicate based on 'id' during the merge
                    charger_id = row.get('id')
                    if charger_id and charger_id not in seen_ids_for_merge:
                        seen_ids_for_merge.add(charger_id)
                        # Ensure the row has all required fieldnames, filling with 'N/A' if missing
                        clean_row = {field: row.get(field, 'N/A') for field in fieldnames}
                        all_rows.append(clean_row)
                    elif not charger_id:
                        print(f"Warning: Skipping a row in {os.path.basename(filepath)} due to missing 'id'.")


        except IOError as e:
            print(f"  Error reading file {filepath}: {e}")
        except Exception as e:
            print(f"  An unexpected error occurred while processing {filepath}: {e}")

    if all_rows:
        try:
            with open(output_filename, 'w', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_rows)
            print(f"\nSuccessfully merged {len(all_rows)} unique records into '{output_filename}'.")
        except IOError as e:
            print(f"Error writing merged file '{output_filename}': {e}")
    else:
        print("No data found to merge into the final output file.")

# --- Function to process a single country (run in parallel processes) ---
def process_country(country_data_tuple, existing_temp_file_basenames, temp_folder, fieldnames, total_estimated_squares_for_all_countries_ignored):
    """
    Processes data for a single country, including downloading, geocoding,
    and saving to temporary CSV files. Returns a list of failed geocoding attempts
    for this country.
    
    Note: total_estimated_squares_for_all_countries_ignored is passed
    but not used within this function as global progress is handled by the main process.
    """
    country_code, (country_name, bbox_coords, num_squares) = country_data_tuple
    
    # Initialize geolocator for this *specific process* (crucial for multiprocessing)
    geolocator_process = Nominatim(user_agent=f"EV_Charger_Scraper_Global_Process_{os.getpid()}/1.0 (your_email@example.com)")

    print(f"\n--- Starting processing for {country_name} ({country_code}) ---")
    country_start_time = time.time()
    
    min_lat, min_lon, max_lat, max_lon = bbox_coords
    all_country_boxes = generate_grid_boxes(min_lat, min_lon, max_lat, max_lon, STEP_LAT, STEP_LON)
    
    num_parts = (len(all_country_boxes) + MAX_SQUARES_PER_COUNTRY_FILE - 1) // MAX_SQUARES_PER_COUNTRY_FILE
    
    # Determine all expected filenames for this country to check if fully processed
    expected_country_part_filenames = set()
    if num_parts > 1:
        for part_index_check in range(num_parts):
            expected_filename_check = f"ev_chargers_{country_name.replace(' ', '_').lower()}_part_{part_index_check + 1}.csv"
            expected_country_part_filenames.add(expected_filename_check)
    else:
        expected_filename_check = f"ev_chargers_{country_name.replace(' ', '_').lower()}.csv"
        expected_country_part_filenames.add(expected_filename_check)

    # Check if ALL expected files for this country already exist in the temporary folder
    is_country_fully_processed = True
    if not expected_country_part_filenames: # Handle case of 0 squares / no data for country
        is_country_fully_processed = False # Treat as not processed if no files expected
    else:
        for filename in expected_country_part_filenames:
            if filename not in existing_temp_file_basenames:
                is_country_fully_processed = False
                break # If any part is missing, the country is not fully processed
    
    if is_country_fully_processed:
        print(f"\n--- {country_name} ({country_code}) is already fully processed. Skipping. ---")
        return [] # Return empty list of failed geocoding attempts

    print(f"  {country_name} divided into {len(all_country_boxes)} squares to search across {num_parts} parts.")
    
    local_geocoding_failures = [] # For logging failed geocoding attempts for this country
    
    # Initialize a set for deduplicating elements *within this country process*
    seen_ids_for_country_process = set()
    all_elements_for_country_to_geocode = [] # List to collect all unique elements before geocoding

    for part_index in range(num_parts):
        part_suffix = ""
        if num_parts > 1:
            part_suffix = f"_part_{part_index + 1}"
        
        output_filename_for_part = os.path.join(temp_folder, f"ev_chargers_{country_name.replace(' ', '_').lower()}{part_suffix}.csv")

        # Check if this specific *part* of the country is already processed
        if os.path.basename(output_filename_for_part) in existing_temp_file_basenames:
            print(f"\n  --- {country_name} (Part {part_index + 1}/{num_parts}) is already processed. Skipping this part. ---")
            continue # Move to the next part

        start_idx = part_index * MAX_SQUARES_PER_COUNTRY_FILE
        end_idx = min((part_index + 1) * MAX_SQUARES_PER_COUNTRY_FILE, len(all_country_boxes))
        
        target_boxes_part = all_country_boxes[start_idx:end_idx]
        
        if num_parts > 1:
            print(f"\n  --- Processing {country_name} (Part {part_index + 1}/{num_parts}, Squares {start_idx + 1}-{end_idx}) ---")
        
        country_failed_boxes_part = [] # For boxes that failed Overpass query in this part
        
        # For time estimation for this part
        processed_boxes_count_part = 0
        box_processing_times_part = []

        # First pass for downloading data from Overpass API for this part
        for i, bbox in enumerate(target_boxes_part):
            box_start_time = time.time()
            print(f"    Processing square {i+1}/{len(target_boxes_part)} for {country_name}{part_suffix}: {bbox}")
            
            success = False
            for attempt in range(MAX_RETRIES_OVERPASS):
                osm_data = get_overpass_data(bbox, attempt + 1)
                if osm_data and 'elements' in osm_data:
                    for element in osm_data['elements']:
                        # Deduplicate elements based on 'id' within this country process
                        if element['id'] not in seen_ids_for_country_process:
                            seen_ids_for_country_process.add(element['id'])
                            all_elements_for_country_to_geocode.append(element)
                    print(f"      Found {len(osm_data['elements'])} elements (total unique for country: {len(seen_ids_for_country_process)}).")
                    success = True
                    break
                elif attempt < MAX_RETRIES_OVERPASS - 1:
                    print(f"      Waiting {RETRY_DELAY_OVERPASS} seconds before next attempt for box {bbox}...")
                    time.sleep(RETRY_DELAY_OVERPASS)
                else:
                    print(f"      All attempts for box {bbox} failed for {country_name}{part_suffix}.")
            
            if not success:
                country_failed_boxes_part.append(bbox)

            time.sleep(QUERY_PAUSE_SECONDS) # Pause after each Overpass query

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


        # Second pass for failed squares for this country part
        if country_failed_boxes_part:
            print(f"\n  --- Starting second pass for {len(country_failed_boxes_part)} failed squares in {country_name}{part_suffix}. ---")
            retried_failed_boxes_part = []
            for i, bbox in enumerate(country_failed_boxes_part):
                box_start_time_retry = time.time()
                print(f"    Processing failed square {i+1}/{len(country_failed_boxes_part)} for {country_name}{part_suffix}: {bbox}")
                success = False
                for attempt in range(MAX_RETRIES_OVERPASS):
                    osm_data = get_overpass_data(bbox, attempt + 1)
                    if osm_data and 'elements' in osm_data:
                        for element in osm_data['elements']:
                            if element['id'] not in seen_ids_for_country_process:
                                seen_ids_for_country_process.add(element['id'])
                                all_elements_for_country_to_geocode.append(element)
                        print(f"      Found {len(osm_data['elements'])} elements in this failed square (total unique: {len(seen_ids_for_country_process)}).")
                        success = True
                        break
                    elif attempt < MAX_RETRIES_OVERPASS - 1:
                        print(f"      Waiting {RETRY_DELAY_OVERPASS} seconds before next attempt for failed box {bbox}...")
                        time.sleep(RETRY_DELAY_OVERPASS)
                    else:
                        print(f"      All attempts for failed box {bbox} failed again.")
                if not success:
                    retried_failed_boxes_part.append(bbox)
                time.sleep(QUERY_PAUSE_SECONDS)

                box_processing_times_part.append(time.time() - box_start_time_retry)
                processed_boxes_count_part += 1
                if processed_boxes_count_part > 0:
                    average_box_time = sum(box_processing_times_part) / processed_boxes_count_part
                    remaining_boxes_in_part = len(target_boxes_part) - processed_boxes_count_part # Still based on original target_boxes_part
                    hours, remainder = divmod(int(average_box_time * remaining_boxes_in_part), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    print(f"    Estimated remaining time for {country_name}{part_suffix} (including second pass): {hours:02d}h {minutes:02d}m {seconds:02d}s")


            if retried_failed_boxes_part:
                print(f"  These squares in {country_name}{part_suffix} failed even after the second pass ({len(retried_failed_boxes_part)}):")
                for bbox in retried_failed_boxes_part:
                    print(f"      {bbox}")
            print(f"  --- Second pass for {country_name}{part_suffix} completed. ---")

    
    print(f"\n  --- Geocoding and preparing {len(all_elements_for_country_to_geocode)} unique elements for {country_name}{part_suffix}. ---")
    processed_chargers_for_csv = []
    
    total_elements_for_geocoding = len(all_elements_for_country_to_geocode)
    if total_elements_for_geocoding > 0:
        # Give an estimate for geocoding time for this country part
        estimated_geocoding_time_seconds = total_elements_for_geocoding * GEOCODING_PAUSE_SECONDS
        hours, remainder = divmod(int(estimated_geocoding_time_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"  Estimated geocoding time for {country_name}{part_suffix}: {hours:02d}h {minutes:02d}m {seconds:02d}s")

    # Geocoding and preparing data for writing for this country part
    for element_idx, element in enumerate(all_elements_for_country_to_geocode):
        tags = element.get('tags', {})
        charger_info = {
            'id': element['id'],
            'lat': element.get('lat'),
            'lon': element.get('lon'),
            'amenity': tags.get('amenity', 'N/A'),
            'scraped_country_code': country_code,
            'scraped_country_name': country_name,
        }
        # Populate other specific fields from 'tags' or set to 'N/A'
        for field in fieldnames:
            if field not in ['id', 'lat', 'lon', 'amenity', 'city', 'state', 'country', 'scraped_country_code', 'scraped_country_name']:
                charger_info[field] = tags.get(field, 'N/A')

        city, state, country = None, None, None
        try:
            lat_val = float(charger_info['lat'])
            lon_val = float(charger_info['lon'])
        except (ValueError, TypeError):
            print(f"    Skipping geocoding for ID {charger_info['id']}: Invalid coordinates ({charger_info['lat']}, {charger_info['lon']}).")
            charger_info['city'] = 'N/A'
            charger_info['state'] = 'N/A'
            charger_info['country'] = 'N/A'
            local_geocoding_failures.append({'id': charger_info['id'], 'lat': charger_info['lat'], 'lon': charger_info['lon'], 'reason': 'Invalid_Coordinates', 'country': country_name})
            processed_chargers_for_csv.append(charger_info)
            continue # Move to next element

        # Retry logic for geocoding
        for attempt in range(MAX_RETRIES_GEOCODING):
            city, state, country = get_location_details(lat_val, lon_val, geolocator_process, attempt + 1)
            if city is not None: # If successfully got details (city is not None)
                break
            else: # Geocoding failed, check if retries are available
                if attempt < MAX_RETRIES_GEOCODING - 1:
                    print(f"    Geocoding for ({lat_val}, {lon_val}) failed, retrying in {GEOCODING_PAUSE_SECONDS}s.")
                    time.sleep(GEOCODING_PAUSE_SECONDS)
                else:
                    # All attempts failed, log and set to 'N/A'
                    print(f"    Geocoding for ({lat_val}, {lon_val}) failed after all attempts.")
                    local_geocoding_failures.append({'id': charger_info['id'], 'lat': charger_info['lat'], 'lon': charger_info['lon'], 'reason': 'GeocoderError', 'country': country_name})
                    city, state, country = 'N/A', 'N/A', 'N/A' # Default to N/A

        charger_info['city'] = city
        charger_info['state'] = state
        charger_info['country'] = country
        processed_chargers_for_csv.append(charger_info)
        time.sleep(GEOCODING_PAUSE_SECONDS) # Important pause for Nominatim API courtesy
    
    # Write processed data for the current country part to its own CSV file
    if processed_chargers_for_csv:
        try:
            with open(output_filename_for_part, 'w', newline='', encoding='utf-8') as part_csvfile:
                part_writer = csv.DictWriter(part_csvfile, fieldnames=fieldnames)
                part_writer.writeheader()
                part_writer.writerows(processed_chargers_for_csv)
            print(f"  Successfully saved {len(processed_chargers_for_csv)} unique records for {country_name}{part_suffix} to '{output_filename_for_part}'.")
        except IOError as e:
            print(f"  Error writing country part file '{output_filename_for_part}': {e}")
    else:
        print(f"  No unique chargers to save for {country_name}{part_suffix} to a country-specific file.")

    country_end_time = time.time()
    print(f"\n--- {country_name} completed in {country_end_time - country_start_time:.2f} seconds. ---")
    
    return local_geocoding_failures # Return failed geocoding attempts for this country

# --- Main execution block ---
if __name__ == "__main__":
    total_start_time = time.time()
    
    # Create the temporary folder if it doesn't exist
    os.makedirs(TEMP_COUNTRY_DATA_FOLDER, exist_ok=True)
    print(f"Temporary country data will be stored in: '{TEMP_COUNTRY_DATA_FOLDER}'")

    # Get a set of already processed file basenames in the temp folder
    existing_temp_file_basenames = {os.path.basename(f) for f in glob.glob(os.path.join(TEMP_COUNTRY_DATA_FOLDER, "*.csv"))}
    print(f"Found {len(existing_temp_file_basenames)} existing temporary files. These will be skipped if complete.")
    for f_name in sorted(list(existing_temp_file_basenames)):
        print(f"  - {f_name}")


    # 1. Generate bounding boxes from GeoJSON files and get the number of squares
    print("\nLoading country bounding boxes from GeoJSON files and calculating the number of squares...")
    COUNTRIES_DATA_RAW = generate_country_bboxes(folder_path=GEOJSON_DATA_FOLDER)
    
    if not COUNTRIES_DATA_RAW:
        print("No country bounding boxes found to process. Make sure the 'country_geojson_data' folder exists and contains GeoJSON files.")
        exit() # Exit if no countries to process
    
    # Sort countries by the number of squares (from smallest to largest) for potentially faster initial feedback
    sorted_countries_list = sorted(COUNTRIES_DATA_RAW.items(), key=lambda item: item[1][2])
    
    print("\nList of countries sorted by the number of search squares:")
    total_estimated_squares = 0
    for code, (name, bbox, num_squares) in sorted_countries_list:
        print(f"- {name} ({code}): {num_squares} squares")
        total_estimated_squares += num_squares # Accumulate total squares

    total_countries_to_process = len(sorted_countries_list)
    print(f"\nTotal countries to search: {total_countries_to_process}")
    print(f"Total estimated Overpass API squares to process: {total_estimated_squares}")

    # Global data storage for failed geocoding queries
    global_geocoding_failures = [] 

    # Define CSV file headers (including all potential OpenStreetMap tags to extract)
    fieldnames = [
        'id', 'lat', 'lon', 'city', 'state', 'country', 'scraped_country_code', 'scraped_country_name',
        'amenity', 'authentication:nfc', 'capacity',
        'capacity:car', 'motorcar', 'operator', 'operator:wikidata',
        'socket:schuko', 'socket:schuko:current', 'socket:schuko:voltage',
        'socket:type2', 'socket:type2:current', 'socket:type2:voltage',
        'access', 'addr:city', 'addr:country', 'addr:housenumber', 'addr:postcode', 'addr:street',
        'amenity:description', 'bicycle_parking', 'building', 'car_sharing', 'covered', 'description',
        'disused:amenity', 'drive_through', 'ele', 'emergency', 'fee', 'fixme', 'fuel:diesel',
        'fuel:electric', 'fuel:petrol', 'gnss:accuracy', 'gnss:source', 'highway', 'internet_access',
        'internet_access:fee', 'level', 'light', 'lit', 'maxstay', 'name', 'opening_hours',
        'payment:cash', 'payment:credit_cards', 'payment:debit_cards', 'payment:mastercard',
        'payment:paypal', 'payment:visa', 'phone', 'qr_code', 'ref', 'source', 'surface',
        'tank_farm', 'website', 'wheelchair', 'wireless', 'osm_type' # Added osm_type if relevant
    ]
    # Dynamically find all unique keys from tags to add to fieldnames (more robust approach)
    # This would require a pre-pass or accumulating all seen keys, but for now fixed list is fine.

    print("\nStarting EV charger data scraping by country with geocoding using parallel processes...")
    
    processed_squares_count = 0 # Counter for overall progress
    
    # Use ProcessPoolExecutor to run country processing in parallel
    # Pass a shared counter or use a mechanism to update progress from child processes
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for country_code, country_info in sorted_countries_list:
            # Check if country is fully processed and skip if so
            is_country_fully_processed_check = True
            num_parts_check = (country_info[2] + MAX_SQUARES_PER_COUNTRY_FILE - 1) // MAX_SQUARES_PER_COUNTRY_FILE
            expected_filenames_for_check = set()
            if num_parts_check > 1:
                for part_idx_chk in range(num_parts_check):
                    expected_filename_check = f"ev_chargers_{country_info[0].replace(' ', '_').lower()}_part_{part_idx_chk + 1}.csv"
                    expected_filenames_for_check.add(expected_filename_check)
            else:
                expected_filename_check = f"ev_chargers_{country_info[0].replace(' ', '_').lower()}.csv"
                expected_filenames_for_check.add(expected_filename_check)

            if not expected_filenames_for_check:
                is_country_fully_processed_check = False
            else:
                for fname_chk in expected_filenames_for_check:
                    if fname_chk not in existing_temp_file_basenames:
                        is_country_fully_processed_check = False
                        break
            
            if is_country_fully_processed_check:
                # If already processed, add its squares to the "processed" count immediately
                processed_squares_count += country_info[2] 
                print(f"Skipping already processed country: {country_info[0]} ({country_info[2]} squares)")
                continue

            # Submit the country processing task to the executor
            # Pass total_estimated_squares for potential future use within process_country
            futures.append(executor.submit(process_country, 
                                           (country_code, country_info), 
                                           existing_temp_file_basenames, 
                                           TEMP_COUNTRY_DATA_FOLDER, 
                                           fieldnames,
                                           total_estimated_squares)) # Pass total for context

        # Use a simple loop to update progress. Note: this won't be perfectly smooth
        # or single-line due to multiprocessing print statements, but provides overall status.
        for future in as_completed(futures):
            try:
                # Each process_country call returns a list of its local failed geocoding attempts
                country_failed_geocodings = future.result()
                global_geocoding_failures.extend(country_failed_geocodings)

                # Find the country info associated with this completed future to update processed_squares_count
                # This requires finding the original country_data_tuple from the submitted futures.
                # A more robust solution might pass back the number of squares processed by the completed future.
                # For simplicity here, we assume if a future completes, its *entire* country's squares were processed.
                # This might not be 100% accurate if a country was partially skipped earlier.
                # A better approach would be to return the *actual* number of squares processed by process_country.
                # For now, let's update by the expected number of squares for the processed country.
                # Find which country this future belongs to:
                completed_country_info = None
                for submitted_country_code, submitted_country_info_tuple in sorted_countries_list:
                    if (submitted_country_code, submitted_country_info_tuple) in [f.args[0] for f in futures if f.done()]: # This is a bit inefficient
                        completed_country_info = submitted_country_info_tuple
                        break # Found it

                if completed_country_info:
                    processed_squares_count += completed_country_info[2] # Add its squares to the total
                    
                # Update the overall progress
                if total_estimated_squares > 0:
                    progress_percentage = (processed_squares_count / total_estimated_squares) * 100
                    # This print statement uses '\r' to try and overwrite the line
                    # However, due to parallel processes, output can be messy.
                    sys.stdout.write(f"\rOverall Progress: {processed_squares_count}/{total_estimated_squares} squares processed ({progress_percentage:.2f}%)")
                    sys.stdout.flush() # Flush ensures the output is written immediately
                
            except Exception as exc:
                print(f'\nA country processing generated an exception: {exc}')

    sys.stdout.write('\n') # Move to a new line after the progress bar is done
    sys.stdout.flush()

    # After all countries (and their parts) are processed, merge the individual CSVs
    merge_csv_files(TEMP_COUNTRY_DATA_FOLDER, MAIN_OUTPUT_FILENAME, fieldnames)

    # Optionally clean up temporary files/folder
    try:
        print(f"\n--- Cleaning up temporary folder '{TEMP_COUNTRY_DATA_FOLDER}' ---")
        shutil.rmtree(TEMP_COUNTRY_DATA_FOLDER)
        print("Temporary files cleaned up.")
    except OSError as e:
        print(f"Error removing temporary folder '{TEMP_COUNTRY_DATA_FOLDER}': {e}")


    total_end_time = time.time()
    print(f"\n--- Entire script completed in {total_end_time - total_start_time:.2f} seconds. ---")
    
    # Save global failed geocoding queries
    if global_geocoding_failures:
        try:
            with open(FAILED_GEOCODING_LOG, 'w', encoding='utf-8') as f:
                json.dump(global_geocoding_failures, f, indent=4)
            print(f"Some geocoding queries failed. Details are in '{FAILED_GEOCODING_LOG}'.")
        except IOError as e:
            print(f"Error saving failed geocoding attempts to {FAILED_GEOCODING_LOG}: {e}")
import os
import time
import pandas as pd
import json
import csv
import sys
import reverse_geocoder as rg
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
import glob
import re
import pycountry

# --- CONSTANTS (PATHS ARE NOW RELATIVE TO SCRIPT LOCATION!) ---

# Get the directory where the current script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

TEMP_OSM_DATA_FOLDER = os.path.join(SCRIPT_DIR, "temp_osm_data")
FINAL_OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, "Final_Output") # Folder for final geocoded files
LOGS_FOLDER = os.path.join(SCRIPT_DIR, "Logs") # Folder for logs
FAILED_GEOCODING_LOG = os.path.join(LOGS_FOLDER, "failed_geocoding_log.json")

# Recommended number of parallel processes.
MAX_WORKERS = os.cpu_count() or 4

# --- Global CSV column configuration ---
ALL_FIELDNAMES = [
    'id', 'lat', 'lon', 'amenity',
    'city', 'state', 'country', # Column content mapping changed as per user request
    'scraped_country_code', 'scraped_country_name', # Keep original scraped info
    'authentication:nfc', 'capacity', 'capacity:car', 'motorcar', 'operator',
    'operator:wikidata', 'socket:schuko', 'socket:schuko:current',
    'socket:schuko:voltage', 'socket:type2', 'socket:type2:current',
    'socket:type2:voltage', 'ref', 'addr:housenumber', 'addr:street',
    'addr:postcode', 'brand', 'charge', 'opening_hours', 'fee'
]

GEOCODED_COLUMNS = ['city', 'state', 'country']

# --- CLASS FOR LOGGING ALL TERMINAL OUTPUT ---
class Tee:
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self, *args, **kwargs):
        for f in self.files:
            f.flush()

# --- Custom mapping for specific country name preferences/simplifications/parent-territory mappings ---
COUNTRY_NAME_OVERRIDES = {
    "Congo, The Democratic Republic of the": "Congo",
    "Palestine, State of": "Palestine",
    "Holy See (Vatican City State)": "Vatican",
    "Réunion": "France",       # Map dependent territory to its parent country
    "Åland Islands": "Finland", # Map dependent territory to its parent country
    "Sint Maarten (Dutch part)": "Sint Maarten", # Simplify the name as requested
    "Türkiye": "Turkiye", # Handle special character and user preference
    # Note: For "Central African Republic", "Chad", "Côte d'Ivoire" -> "Africa",
    # these are not included as "Africa" is a continent, not a country.
    # If you still wish to map these to "Africa", please confirm.
}


# --- HELPER FUNCTION TO GET FULL COUNTRY NAME FROM CODE ---
def get_full_country_name(country_code):
    """
    Converts a 2-letter country code (e.g., 'CH') to its full name (e.g., 'Switzerland').
    Applies custom overrides.
    Returns 'N/A' if the code is not found or is None.
    """
    if country_code is None:
        return 'N/A'
    try:
        country = pycountry.countries.get(alpha_2=country_code.upper())
        if country:
            # Get the pycountry name (prefer common_name, fallback to official name)
            pycountry_name = getattr(country, 'common_name', country.name)
            
            # Apply custom overrides from the dictionary
            return COUNTRY_NAME_OVERRIDES.get(pycountry_name, pycountry_name)
        else:
            return 'N/A'
    except KeyError:
        return 'N/A'
    except Exception as e:
        print(f"Warning: Error getting country name for code '{country_code}': {e}")
        return 'N/A'


# --- FUNCTION FOR GEOCODING DATA ---
def geocode_single_raw_file(raw_csv_filepath, final_output_folder, all_fieldnames, geocoded_columns):
    filename_base = os.path.basename(raw_csv_filepath)
    
    # Remove prefix 'ev_chargers_osm_raw_' and '.csv' suffix to get the core name
    core_name_with_suffix = filename_base.replace('ev_chargers_osm_raw_', '').replace('.csv', '')

    # Enhanced parsing for display purposes (for log and console output)
    display_name = core_name_with_suffix.upper() 

    # Use regex to detect and parse "[Part X]"
    match = re.search(r'^(.*?)\s*\[Part\s*(\d+)\]$', core_name_with_suffix, re.IGNORECASE)
    if match:
        base_country_name = match.group(1).strip() 
        part_number = match.group(2) 
        display_name = f"{base_country_name.upper()} [Part {part_number}]"
    else:
        # If no '[Part X]' pattern, just uppercase the core name
        display_name = core_name_with_suffix.upper()

    print(f"\n[GEOCODING] Starting geocoding for file: {filename_base} (Display Name: {display_name})...")
    
    failed_geocodings = []
    
    # Path for the final output file for this RAW file
    # The final filename will match the RAW filename, just with 'geocoded_' prefix
    final_output_filename = filename_base.replace("osm_raw_", "geocoded_")
    final_output_filepath = os.path.join(final_output_folder, final_output_filename)

    # Check if the final output file already exists
    if os.path.exists(final_output_filepath) and os.path.getsize(final_output_filepath) > 0:
        print(f"  [GEOCODING] Final output file for {filename_base} already exists: '{final_output_filepath}'. Skipping geocoding.")
        return []

    try:
        raw_df = None
        delimiter_used = None
        possible_delimiters = [',', ';'] 

        for delim in possible_delimiters:
            try:
                temp_df = pd.read_csv(raw_csv_filepath, encoding='utf-8', on_bad_lines='skip', dtype=str, sep=delim)
                
                if 'id' in temp_df.columns and 'lat' in temp_df.columns and 'lon' in temp_df.columns:
                    raw_df = temp_df
                    delimiter_used = delim
                    print(f"  [GEOCODING] Detected delimiter '{delim}' for '{filename_base}'.")
                    break 
                else:
                    print(f"  [GEOCODING] Attempted delimiter '{delim}' for '{filename_base}', but critical columns not found. Trying next.")
                    continue 

            except pd.errors.ParserError as e:
                print(f"  [GEOCODING] ParserError with delimiter '{delim}' for '{filename_base}': {e}. Trying next.")
                continue
            except Exception as e:
                print(f"  [GEOCODING] General error with delimiter '{delim}' for '{filename_base}': {e}. Trying next.")
                continue

        if raw_df is None:
            raise ValueError(f"Could not read '{filename_base}' with any of the attempted delimiters: {possible_delimiters}. Critical columns (id, lat, lon) missing or file malformed.")

        print(f"  [GEOCODING] Loaded {len(raw_df)} raw records from '{filename_base}'.")

        if raw_df.empty:
            print(f"  [GEOCODING] No data to geocode for '{filename_base}'. Raw file was empty.")
            empty_df = pd.DataFrame(columns=all_fieldnames)
            os.makedirs(final_output_folder, exist_ok=True)
            empty_df.to_csv(final_output_filepath, index=False, encoding='utf-8', quoting=csv.QUOTE_NONNUMERIC, sep=';') 
            return []

        # Convert lat/lon to float for geocoding
        raw_df['lat_float'] = pd.to_numeric(raw_df['lat'], errors='coerce')
        raw_df['lon_float'] = pd.to_numeric(raw_df['lon'], errors='coerce')

        # Filter out rows with invalid coordinates before geocoding
        valid_coords_df = raw_df.dropna(subset=['lat_float', 'lon_float']).copy()
        invalid_coords_df = raw_df[raw_df['lat_float'].isna() | raw_df['lon_float'].isna()]

        for _, row in invalid_coords_df.iterrows():
            failed_geocodings.append({
                'id': row.get('id', 'N/A'),
                'lat': row.get('lat', 'N/A'),
                'lon': row.get('lon', 'N/A'),
                'raw_tags': row.get('tags', 'N/A'),
                'source_file': filename_base,
                'error': 'Invalid_Coordinates',
                'timestamp': datetime.now().isoformat()
            })
        
        if valid_coords_df.empty:
            print(f"  [GEOCODING] No valid coordinates to geocode for '{filename_base}'. All records have invalid coordinates.")
            output_df = raw_df.copy()
            for col in geocoded_columns:
                output_df[col] = 'N/A'
            for field in all_fieldnames:
                if field not in output_df.columns:
                    output_df[field] = 'N/A'
            
            os.makedirs(final_output_folder, exist_ok=True)
            output_df.to_csv(final_output_filepath, index=False, encoding='utf-8', quoting=csv.QUOTE_NONNUMERIC, columns=all_fieldnames, sep=';')
            return failed_geocodings

        # --- MAIN GEOCODING LOGIC using reverse_geocoder ---
        coordinates = list(zip(valid_coords_df['lat_float'], valid_coords_df['lon_float']))
        
        print(f"  [GEOCODING] Performing reverse geocoding for {len(coordinates)} valid records from '{filename_base}'...")
        geocoding_results = rg.search(coordinates)

        state_col_data = []    # Will store full country name (e.g., USA, Czech Republic)
        country_col_data = []  # Will store admin1 (e.g., California, South Moravian Region)
        city_col_data = []     # Will store admin2 (e.g., Los Angeles, Brno)

        for res in geocoding_results:
            country_code = res.get('cc')
            full_country_name_for_state = get_full_country_name(country_code) # Use helper with overrides for 'State'
            
            # The 'Country' column will now contain admin1 (e.g., California, Graubünden)
            admin1_name_for_country = res.get('admin1', 'N/A')
            
            # The 'City' column will contain admin2 (e.g., Los Angeles, Samedan)
            admin2_name_for_city = res.get('admin2', 'N/A')

            state_col_data.append(full_country_name_for_state)
            country_col_data.append(admin1_name_for_country) 
            city_col_data.append(admin2_name_for_city)    

        # Assign collected names to DataFrame columns
        valid_coords_df['state'] = state_col_data
        valid_coords_df['country'] = country_col_data
        valid_coords_df['city'] = city_col_data

        # Log failures if the primary country name (which goes into 'state' column) is not found
        for idx, row in valid_coords_df.iterrows():
            if pd.isna(row['state']) or row['state'] == '' or row['state'] == 'N/A':
                failed_geocodings.append({
                    'id': row.get('id', 'N/A'),
                    'lat': row.get('lat', 'N/A'),
                    'lon': row.get('lon', 'N/A'),
                    'raw_tags': row.get('tags', 'N/A'),
                    'source_file': filename_base,
                    'error': 'Country_NotFound_By_Geocoder', 
                    'timestamp': datetime.now().isoformat()
                })
                valid_coords_df.loc[idx, 'state'] = 'N/A'
                valid_coords_df.loc[idx, 'country'] = 'N/A'
                valid_coords_df.loc[idx, 'city'] = 'N/A'

        # Merge valid and invalid coordinates back into one DataFrame
        for col in ['country', 'state', 'city']:
            raw_df[col] = raw_df['id'].map(valid_coords_df.set_index('id')[col])
            raw_df[col] = raw_df[col].fillna('N/A') 

        # Drop helper columns
        final_df = raw_df.drop(columns=['lat_float', 'lon_float'], errors='ignore')

        os.makedirs(final_output_folder, exist_ok=True)
        
        # Atomic write of the final file
        temp_final_output_filepath = final_output_filepath + ".tmp"
        
        # Ensure all fieldnames exist in the DataFrame; if not, add them with 'N/A'
        for field in all_fieldnames:
            if field not in final_df.columns:
                final_df[field] = 'N/A'

        # Write to CSV with exactly defined columns, using semicolon as separator
        final_df.to_csv(temp_final_output_filepath, index=False, encoding='utf-8', quoting=csv.QUOTE_NONNUMERIC, columns=all_fieldnames, sep=';')
        os.replace(temp_final_output_filepath, final_output_filepath) 

        print(f"  [GEOCODING] Successfully geocoded and saved {len(final_df)} records from '{filename_base}' to '{final_output_filepath}'.")

    except Exception as e:
        print(f"  [GEOCODING] Error processing file '{filename_base}': {e}")
        failed_geocodings.append({
            'source_file': filename_base,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })
    
    return failed_geocodings

# --- MAIN FUNCTION TO RUN PHASE 2 ---
if __name__ == "__main__":
    total_script_start_time = time.time()

    # --- Setup logging to a file ---
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    log_filename = datetime.now().strftime("geocoding_process_log_%Y-%m-%d_%H-%M-%S.txt")
    log_filepath = os.path.join(LOGS_FOLDER, log_filename)
    
    f_log = open(log_filepath, 'w', encoding='utf-8', buffering=1)
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = Tee(original_stdout, f_log)
    sys.stderr = Tee(original_stderr, f_log)

    print(f"\n--- Starting Phase 2: Geocoding Data (Offline) ---")
    print(f"Loading raw data from: {TEMP_OSM_DATA_FOLDER}")
    print(f"Saving final geocoded data to: {FINAL_OUTPUT_FOLDER}")
    print(f"Log file: {log_filepath}")

    # --- Get list of RAW files to geocode ---
    raw_files_to_process = glob.glob(os.path.join(TEMP_OSM_DATA_FOLDER, 'ev_chargers_osm_raw_*.csv'))
    
    raw_files_to_process.sort() 

    if not raw_files_to_process:
        print("No raw data files found to geocode. Please check TEMP_OSM_DATA_FOLDER and filename patterns ('ev_chargers_osm_raw_*.csv').")
        sys.exit(0)

    print(f"\nFound {len(raw_files_to_process)} files to geocode. Starting processes...")

    # --- PHASE 2: Geocoding Data ---
    phase2_start_time = time.time()
    
    global_geocoding_failures = []

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures_phase2 = []
        for raw_filepath in raw_files_to_process:
            futures_phase2.append(executor.submit(geocode_single_raw_file,
                                                  raw_filepath,
                                                  FINAL_OUTPUT_FOLDER,
                                                  ALL_FIELDNAMES,
                                                  GEOCODED_COLUMNS))

        for future in as_completed(futures_phase2):
            try:
                file_failed_geocodings = future.result()
                global_geocoding_failures.extend(file_failed_geocodings)
            except Exception as exc:
                print(f'Geocoding process for a file generated an exception: {exc}')

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
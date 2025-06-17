import requests
from bs4 import BeautifulSoup
import csv
import time

# --- Helper functions for scraping ---

def get_all_brands(base_url="https://www.auto-data.net/en/"):
    """
    Retrieves a list of all car brands and their URLs from the main page.
    """
    brands = []
    print(f"Downloading brand list from: {base_url}")
    try:
        response = requests.get(base_url)
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')

        brand_div = soup.find('div', class_='markite')
        if brand_div:
            for a_tag in brand_div.find_all('a', class_='marki_blok'):
                brand_name = a_tag.find('strong').text.strip() if a_tag.find('strong') else 'Unknown Brand'
                brand_url = "https://www.auto-data.net" + a_tag['href'] if a_tag.has_attr('href') else None
                # Ignore "All brands" link and empty URLs
                if brand_url and "/en/allbrands" not in brand_url:
                    brands.append({'name': brand_name, 'url': brand_url})
        else:
            print(f"  Error: 'div' element with class 'markite' not found on page {base_url}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading brands from {base_url}: {e}")
    except Exception as e:
        print(f"Unexpected error processing {base_url}: {e}")
    return brands


def get_models_for_brand(brand_url):
    """Retrieves a list of models and their URLs for a given brand URL."""
    models = []
    print(f"  Downloading models from: {brand_url}")
    try:
        response = requests.get(brand_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        modelite_ul = soup.find('ul', class_='modelite')
        if modelite_ul:
            for a_tag in modelite_ul.find_all('a', class_='modeli'):
                model_name = a_tag.find('strong').text.strip() if a_tag.find('strong') else 'Unknown Model'
                model_url = "https://www.auto-data.net" + a_tag['href'] if a_tag.has_attr('href') else None
                
                if model_url:
                    models.append({'name': model_name, 'url': model_url})
        else:
            print(f"    Error: 'ul' element with class 'modelite' not found on page {brand_url}")
    except requests.exceptions.RequestException as e:
        print(f"  Error downloading models from {brand_url}: {e}")
    except Exception as e:
        print(f"  Unexpected error processing {brand_url}: {e}")
    return models

def get_generations_for_model(model_url):
    """Retrieves the name and URL of all generations from the 'generr' table on the model page."""
    generations_data = []
    print(f"    Downloading generations from: {model_url}")
    try:
        response = requests.get(model_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        generr_table = soup.find('table', class_='generr')
        if generr_table:
            # Look for rows with class 'f', regardless of 'lred' or 'lgreen', 
            # as 'f' is common for all generation rows.
            for row in generr_table.find_all('tr', class_=lambda x: x and 'f' in x.split()):
                generation_name = 'Unknown Generation'
                generation_url = None

                title_tag = row.find('strong', class_='tit')
                if title_tag:
                    generation_name = title_tag.text.strip()
                
                gen_link_tag = row.find('th', class_='i').find('a', class_='position')
                if gen_link_tag and gen_link_tag.has_attr('href'):
                    generation_url = "https://www.auto-data.net" + gen_link_tag['href']

                # Add only if a valid generation URL is found
                if generation_url:
                    generations_data.append({'Generation_Name': generation_name, 'Generation_URL': generation_url})
                else:
                    print(f"        Warning: Found generation row '{generation_name}', but URL link is missing. Skipping.")
        else:
            print("      Error: 'generr' table not found on the model page.")
    except requests.exceptions.RequestException as e:
        print(f"    Error downloading generations from {model_url}: {e}")
    except Exception as e:
        print(f"    Unexpected error processing {model_url}: {e}")
    
    return generations_data

def get_engines_for_generation(generation_url):
    """Retrieves the name and URL of all engines from the 'carlist' table on the generation page."""
    engines_data = []
    print(f"      Downloading engines from: {generation_url}")
    try:
        response = requests.get(generation_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        carlist_table = soup.find('table', class_='carlist')
        if carlist_table:
            # Assuming engine rows have class 'i lred'.
            # If other colors/'lgreen' exist, it would need adjustment similar to generations.
            for row in carlist_table.find_all('tr', class_='i lred'): 
                engine_name = 'Unknown Engine'
                engine_url = None

                title_span = row.find('span', class_='tit')
                if title_span:
                    engine_name = title_span.text.strip()
                
                engine_link_tag = row.find('th', class_='i').find('a')
                if engine_link_tag and engine_link_tag.has_attr('href'):
                    engine_url = "https://www.auto-data.net" + engine_link_tag['href']
                    
                    if engine_url: # Ensure URL is not empty
                        engines_data.append({'Engine_Name': engine_name, 'Engine_URL': engine_url})
                    else:
                        print(f"        Warning: Found engine '{engine_name}', but URL link is missing. Skipping.")
        else:
            print("        Error: 'carlist' table not found on the generation page.")
    except requests.exceptions.RequestException as e:
        print(f"      Error downloading engines from {generation_url}: {e}")
    except Exception as e:
        print(f"      Unexpected error processing {generation_url}: {e}")
    
    return engines_data

def get_engine_full_details(engine_url):
    """
    Retrieves all detailed specifications from the 'cardetailsout car2' table on the engine page.
    Filters out section headings and "Log in to see." values.
    """
    details = {}
    try:
        response = requests.get(engine_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        car_details_table = soup.find('table', class_='cardetailsout car2')
        if car_details_table:
            for row in car_details_table.find_all('tr'):
                header_tag = row.find('th')
                value_tag = row.find('td')

                if header_tag and value_tag: # Only process rows that have both a header and a value
                    header_text = header_tag.get_text(separator=" ", strip=True)
                    # Clean and format the header for CSV columns
                    header_text = header_text.replace(' ', '_').replace('(', '').replace(')', '').replace('.', '').replace('/', '_').replace('-', '_')
                    header_text = header_text.replace('adsense', '').strip('_') # Remove 'adsense' and any leading/trailing underscores

                    value_text = value_tag.get_text(separator=" ", strip=True)
                    
                    # Filter out irrelevant data
                    is_valid_header = header_text and not header_tag.get('colspan') # Ignores section headers
                    is_valid_value = 'Log_in_to_see.' not in value_text and 'adsense' not in header_text.lower() # Ignores "Log in to see." and ads

                    if is_valid_header and is_valid_value:
                        details[header_text] = value_text
        # else: # No need to print error here, as some detail pages might not always be found if the URL doesn't exist
            # print(f"        Error: 'cardetailsout car2' table not found on page {engine_url}.")
    except requests.exceptions.RequestException as e:
        print(f"        Error downloading engine details from {engine_url}: {e}")
    except Exception as e:
        print(f"        Unexpected error processing {engine_url}: {e}")
    
    return details

# --- Function for saving data to CSV ---
def save_all_data_to_csv(data_list, filename="complete_auto_data.csv"):
    """
    Saves a list of dictionaries to a CSV file. Dynamically determines all headers.
    """
    if not data_list:
        print("No data to save to CSV.")
        return

    # Collect all unique headers from all rows
    all_fieldnames = set()
    for row_dict in data_list:
        all_fieldnames.update(row_dict.keys())
    
    # Prioritize basic headers for better CSV readability, then sort the rest alphabetically
    initial_fieldnames = ['Brand', 'Model', 'Generation_Name', 'Engine_Name']
    sorted_additional_fieldnames = sorted([f for f in all_fieldnames if f not in initial_fieldnames])
    final_fieldnames = initial_fieldnames + sorted_additional_fieldnames

    print(f"\nSaving {len(data_list)} records to file '{filename}'...")

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=final_fieldnames, delimiter=';', extrasaction='ignore')

            writer.writeheader() 
            for row in data_list:
                writer.writerow(row)
        print(f"Data successfully saved to file '{filename}'.")
    except IOError as e:
        print(f"Error writing to CSV file '{filename}': {e}")


# --- Main script execution block with progress indicators ---
if __name__ == "__main__":
    base_brands_url = "https://www.auto-data.net/en/"
    all_collected_data = []

    print(f"--- STARTING COMPLETE AUTO-DATA.NET SCRAPING ---")

    brands = get_all_brands(base_brands_url)
    if brands:
        total_brands = len(brands)
        print(f"\nFound {total_brands} brands to process.")
        
        for i_brand, brand in enumerate(brands, 1):
            print(f"\nProcessing brand: {brand['name']} ({i_brand}/{total_brands})")
            time.sleep(1) # Decent delay for server courtesy

            models = get_models_for_brand(brand['url'])
            if models:
                total_models = len(models)
                print(f"  Found {total_models} models for {brand['name']}.")
                for i_model, model in enumerate(models, 1):
                    print(f"    Processing model: {model['name']} ({i_model}/{total_models})")
                    time.sleep(1)

                    generations = get_generations_for_model(model['url'])
                    if generations:
                        total_generations = len(generations)
                        print(f"      Found {total_generations} generations for {model['name']}.")
                        for i_gen, gen in enumerate(generations, 1):
                            if gen['Generation_URL']:
                                print(f"        Processing generation: {gen['Generation_Name']} ({i_gen}/{total_generations})")
                                time.sleep(1)

                                engines = get_engines_for_generation(gen['Generation_URL'])
                                if engines:
                                    total_engines = len(engines)
                                    print(f"          Found {total_engines} engines for {gen['Generation_Name']}.")
                                    for i_engine, engine in enumerate(engines, 1):
                                        if engine['Engine_URL']:
                                            print(f"            Downloading engine details: {engine['Engine_Name']} ({i_engine}/{total_engines})")
                                            engine_full_details = get_engine_full_details(engine['Engine_URL'])
                                            
                                            current_row_data = {
                                                'Brand': brand['name'],
                                                'Model': model['name'],
                                                'Generation_Name': gen['Generation_Name'],
                                                'Engine_Name': engine['Engine_Name']
                                            }
                                            current_row_data.update(engine_full_details)
                                            
                                            all_collected_data.append(current_row_data)
                                            time.sleep(0.5)
                                        else:
                                            print(f"          Engine URL for '{engine['Engine_Name']}' not found. Skipping.")
                                else:
                                    print(f"          No engines found for generation '{gen['Generation_Name']}'.")
                            else:
                                print(f"        Generation URL for '{gen['Generation_Name']}' not found. Skipping.")
                    else:
                        print(f"      No generations found for model '{model['name']}'.")
            else:
                print(f"    No models found for brand '{brand['name']}'.")
    else:
        print(f"Error: No brands found from '{base_brands_url}'.")

    if all_collected_data:
        save_all_data_to_csv(all_collected_data, filename="complete_auto_data.csv")
    else:
        print("\nNo data collected to save to CSV.")

    print("\n--- COMPLETE SCRAPING FINISHED ---")
import requests # Used for making HTTP requests to fetch web pages
from bs4 import BeautifulSoup # Used for parsing HTML content
import pandas as pd # Used for data manipulation and saving to CSV
import time # Used to introduce delays to avoid overwhelming the server

# --- Configuration ---
BASE_URL = "https://m.arenaev.com/" # The base URL of the website to be scraped

# --- Helper Functions ---

def make_absolute(url):
    """
    Converts a relative URL into an absolute URL by prepending the BASE_URL
    if the URL is not already absolute (starts with 'http').

    Args:
        url (str): The URL to convert.

    Returns:
        str: The absolute URL.
    """
    if url.startswith("http"):
        return url
    else:
        return BASE_URL + url

def fetch_soup(url):
    """
    Fetches the HTML content from a given URL and parses it using BeautifulSoup.
    Includes basic error handling for network issues and HTTP status codes.

    Args:
        url (str): The URL of the page to fetch.

    Returns:
        BeautifulSoup object: Parsed HTML content of the page, or an empty
                              BeautifulSoup object if fetching fails.
    """
    url = make_absolute(url) # Ensure the URL is absolute
    print(f"Fetching URL: {url}") # Print the URL being fetched for tracking progress
    try:
        # Send a GET request with a User-Agent header to mimic a web browser
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.TooManyRedirects:
        # Handle cases where too many redirects occur, indicating a potential issue
        print(f"Too many redirects on URL: {url}")
        return BeautifulSoup("", "html.parser") # Return empty soup to continue execution
    except Exception as e:
        # Catch any other exceptions during the request (e.g., network errors)
        print(f"Failed to fetch URL: {url} - {e}")
        return BeautifulSoup("", "html.parser") # Return empty soup to continue execution
    
    # If successful, parse the content and return the BeautifulSoup object
    return BeautifulSoup(resp.content, "html.parser")

# --- Scraping Functions ---

def scrap_makers():
    """
    Scrapes the list of EV makers (manufacturers) from the dedicated 'makers' page.

    Returns:
        list of dict: A list where each dictionary contains 'maker_name' and 'maker_url'.
    """
    # Fetch the HTML for the makers page
    soup = fetch_soup(BASE_URL + "makers.php3")
    makers = []
    # Find all <a> tags that have an 'href' attribute
    for a in soup.find_all("a", href=True):
        strong = a.find("strong") # Look for a <strong> tag within the <a> tag
        if strong:
            # If a <strong> tag is found, it contains the maker's name
            makers.append({
                "maker_name": strong.text.strip(), # Extract and clean the maker's name
                "maker_url": make_absolute(a["href"]) # Get the absolute URL for the maker's page
            })
    return makers

def scrap_models(maker):
    """
    Scrapes the list of models for a given EV maker from their dedicated page.

    Args:
        maker (dict): A dictionary containing 'maker_name' and 'maker_url'.

    Returns:
        list of dict: A list where each dictionary contains 'maker_name', 'model_name',
                      'year', and 'model_url'.
    """
    # Fetch the HTML for the specific maker's page
    soup = fetch_soup(maker["maker_url"])
    models = []
    # Find all <a> tags that have a 'data-model-id' attribute
    for a in soup.find_all("a", {"data-model-id": True}):
        models.append({
            "maker_name": maker["maker_name"], # Inherit maker name from the parent
            "model_name": a["data-model-name"], # Extract model name from 'data-model-name' attribute
            "year": a["data-year"].strip(), # Extract and clean year from 'data-year' attribute
            "model_url": make_absolute(a["href"]) # Get the absolute URL for the model's page
        })
    return models

def scrap_versions(model):
    """
    Scrapes different versions (e.g., trim levels or battery variants) for a given model.
    These are typically found in a dropdown selector on the model's page.

    Args:
        model (dict): A dictionary containing model details.

    Returns:
        list of dict: A list where each dictionary contains inherited model details
                      plus 'version_name' and 'version_url'. If no versions are found,
                      it returns the model's URL as a default version.
    """
    # Fetch the HTML for the specific model's page
    soup = fetch_soup(model["model_url"])
    versions = []
    # Find the <select> element within a div with class 'floating-drive-selector'
    select = soup.select_one("div.floating-drive-selector select")
    if select:
        # Iterate over each <option> tag within the <select> dropdown
        for opt in select.find_all("option"):
            href = opt.get("value") # The 'value' attribute contains the URL for the version
            if href: # Ensure the 'value' attribute is not empty
                versions.append({
                    **model, # Unpack existing model details (maker_name, model_name, year, model_url)
                    "version_name": opt.text.strip(), # Extract and clean the version name
                    "version_url": make_absolute(href) # Get the absolute URL for the version's page
                })
    else:
        # If no specific versions (dropdown) are found, treat the main model page
        # as the only version, with an empty version name.
        versions.append({
            **model,
            "version_name": "", # Empty string for the version name if no specific versions exist
            "version_url": model["model_url"] # Use the model's main URL
        })
    return versions

def scrap_specs(ver):
    """
    Scrapes the detailed specifications for a specific EV version.
    Details are typically organized in tables with 'ttl' (title) and 'nfo' (info) classes.

    Args:
        ver (dict): A dictionary containing version details.

    Returns:
        dict: A dictionary containing inherited version details and all scraped
              specifications, with keys formatted as "Section.SpecificationName".
    """
    # Fetch the HTML for the specific version's page
    soup = fetch_soup(ver["version_url"])
    # Initialize data with inherited fields from the version (maker, model, year, etc.)
    data = {k: ver[k] for k in ["maker_name","model_name","year","version_name","version_url"]}
    
    # Find all <table> elements on the page
    for table in soup.find_all("table"):
        # The <th> tag in the first row usually indicates the section title (e.g., "Performance")
        th = table.find("th")
        section = th.text.strip() if th else "Unknown" # Default to "Unknown" if no section header found
        
        # Iterate over each row in the current table
        for row in table.find_all("tr"):
            ttl = row.find("td", class_="ttl") # Find the cell with the specification title
            nfo = row.find("td", class_="nfo") # Find the cell with the specification value
            
            if ttl and nfo: # Ensure both title and info cells are present
                # Create a unique key by combining section and title (e.g., "Performance.Max speed")
                key = f"{section}.{ttl.text.strip()}"
                data[key] = nfo.text.strip() # Store the specification value
    return data

# --- Main Execution Flow ---

def main():
    """
    Orchestrates the entire scraping process:
    1. Scrapes all EV makers.
    2. For each maker, scrapes all models.
    3. For each model, scrapes all versions.
    4. For each version, scrapes detailed specifications.
    5. Collects all data and saves it to a CSV file.
    """
    results = [] # List to store all collected data dictionaries
    
    # Step 1: Scrape all makers
    makers = scrap_makers()
    print(f"💡 Found {len(makers)} manufacturers.") # Inform user about the number of makers found
    
    # Iterate through each maker
    for m in makers:
        print(f"Scraping manufacturer: {m['maker_name']}") # Indicate current manufacturer being processed
        # Step 2: Scrape all models for the current maker
        models = scrap_models(m)
        for mod in models:
            print(f" Model: {mod['model_name']} ({mod['year']})") # Indicate current model being processed
            # Step 3: Scrape all versions for the current model
            versions = scrap_versions(mod)
            for ver in versions:
                print(f"   🔧 Version: {ver['version_name'] if ver['version_name'] else 'Default/Base'}") # Indicate current version
                # Step 4: Scrape detailed specifications for the current version
                spec = scrap_specs(ver)
                results.append(spec) # Add the collected specifications to the results list
                time.sleep(1) # Pause for 1 second after each version's specs (be respectful to the server)
            time.sleep(1) # Pause for 1 second after processing all models for a maker
    
    # After scraping all data, create a Pandas DataFrame and save it to a CSV file
    df = pd.DataFrame(results)
    df.to_csv("arenaev_full_scrape.csv", index=False, encoding="utf-8-sig")
    print("✅ Done! Data saved to arenaev_full_scrape.csv") # Success message

if __name__ == "__main__":
    # This ensures that main() is called only when the script is executed directly
    main()
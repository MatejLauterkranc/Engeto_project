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
import random 

# --- Configuration ---
EDMUNDS_URL = "https://www.edmunds.com/inventory/srp.html"
OUTPUT_CSV_FILE = "edmunds_scraped_prices_firefox_paginated_v3.csv" # Updated file name for new data

script_dir = os.path.dirname(os.path.abspath(__file__))
GECKODRIVER_PATH = os.path.join(script_dir, 'geckodriver.exe')

BRANDS_TO_SCRAPE = [
    "Volkswagen",
    "Tesla",
    "Honda"
]

US_ZIP_CODE = "90210" 

# --- WebDriver Initialization ---
def initialize_driver():
    """Initializes and returns a WebDriver for Firefox."""
    options = webdriver.FirefoxOptions()
    # options.add_argument("--headless") # Runs the browser in the background (without GUI) - uncomment for production
    
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0") 

    try:
        service = Service(GECKODRIVER_PATH) 
        driver = webdriver.Firefox(service=service, options=options)
        return driver
    except Exception as e:
        print(f"Error initializing WebDriver (Firefox): {e}")
        print(f"Ensure that '{GECKODRIVER_PATH}' exists and is compatible with your Firefox.")
        return None

# --- Function for scraping a single page (with adjusted waiting and scrolling) ---
def scrape_page(driver, url):
    """Loads the URL, closes privacy banner, waits for other pop-ups, scrolls, and returns HTML."""
    try:
        driver.get(url)

        # Wait for privacy banner - still important, even if it doesn't always appear
        try:
            privacy_close_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.close-btn[data-tracking-id="close_privacy_disclaimer"]'))
            )
            privacy_close_button.click()
            print("Privacy banner was closed.")
            time.sleep(random.uniform(2, 4)) # Random pause
        except Exception as e:
            print(f"Privacy banner not found or could not be clicked (perhaps no longer displayed): {e}")
            
        print("Waiting for other pop-ups (e.g., Google login) to disappear...")
        time.sleep(random.uniform(5, 9)) # Longer random pause for pop-ups

        # Wait for the main vehicle element (`clickable-card`) to be present
        try:
            WebDriverWait(driver, 60).until( # Long wait
                EC.presence_of_element_located((By.CLASS_NAME, "clickable-card"))
            )
            print("At least one 'clickable-card' vehicle element found. Page should be loaded.")
            time.sleep(random.uniform(3, 6)) # Random pause after finding the element
        except Exception as e:
            print(f"Error: No 'clickable-card' vehicle found after 60 seconds of waiting on {url}: {e}")
            # If no car was found, return empty HTML (or let it be processed further)
            # Important: We are not returning None here, to allow verification in extract_car_data
            return BeautifulSoup("", 'html.parser') # Return empty soup if nothing was found

        # Aggressive scrolling to load all content
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 10 
        while scroll_attempts < max_scroll_attempts:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(5, 9)) # Longer random pause after each scroll
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print(f"Reached bottom after {scroll_attempts + 1} scrolls.")
                break 
            last_height = new_height
            scroll_attempts += 1
        
        print("Scrolling complete, getting page HTML code.")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        return soup
    except Exception as e:
        print(f"Error loading page {url} (overall): {e}")
        return None

# --- Function for extracting data from HTML ---
def extract_car_data(soup):
    """Extracts car data (name, price, year, fuel type) from a BeautifulSoup object."""
    cars_data = []
    
    vehicle_cards = soup.find_all('div', class_='clickable-card')
    
    if not vehicle_cards:
        return []

    for card in vehicle_cards:
        name_element = card.find('div', class_='size-16 text-cool-gray-10 fw-bold mb-0_5')
        price_element = card.find('span', class_='heading-3')
        
        # --- NEW CODE FOR FUEL TYPE ---
        fuel_type = "Gas/Diesel" # Default value
        electric_icon = card.find('i', class_='icon-power2')
        
        if electric_icon:
            fuel_type = "Electric"
        # --- END OF NEW CODE FOR FUEL TYPE ---

        car_name_raw = name_element.get_text(strip=True) if name_element else None
        price_text = price_element.get_text(strip=True) if price_element else None

        # --- NEW CODE FOR YEAR EXTRACTION ---
        car_year = None
        if car_name_raw:
            # Use regex to find a 4-digit number at the beginning of the string
            year_match = re.match(r'(\d{4})', car_name_raw)
            if year_match:
                car_year = int(year_match.group(1))
                # Remove the year and leading space from the car_name
                car_name = car_name_raw[len(year_match.group(0)):].strip()
                # Also remove the electric icon text if it somehow got included
                if electric_icon:
                    # The icon itself is HTML, get_text(strip=True) usually cleans it,
                    # but if "Electric" or similar text from the icon's parent
                    # was included in car_name_raw, we might need to remove it.
                    # For now, let's assume the icon HTML doesn't pollute the name.
                    pass
            else:
                car_name = car_name_raw # If no year found, keep original name
        else:
            car_name = None
        # --- END OF NEW CODE FOR YEAR EXTRACTION ---


        if car_name and price_text:
            cleaned_price = re.sub(r'[$,]', '', price_text)
            try:
                price_value = float(cleaned_price)
                cars_data.append({
                    'Scraped_Car_Name': car_name,
                    'Scraped_Price_USD': price_value,
                    'Scraped_Currency': 'USD',
                    'Car_Year': car_year,  # Add the extracted year
                    'Fuel_Type': fuel_type 
                })
            except ValueError:
                print(f"Could not convert price '{cleaned_price}' to a number for {car_name}.")
            
    return cars_data

# --- Main script logic with adjusted pagination ---
def main():
    driver = initialize_driver()
    if not driver:
        return

    all_scraped_data = []

    for brand in BRANDS_TO_SCRAPE:
        print(f"\n--- Scraping data for brand: {brand} ---")
        current_page_num = 1
        max_pages_to_scrape = 100 
        
        consecutive_empty_pages = 0
        max_consecutive_empty = 2 

        while current_page_num <= max_pages_to_scrape:
            search_url = f"{EDMUNDS_URL}?make={brand}&zip={US_ZIP_CODE}&pagenumber={current_page_num}"
            print(f"Loading page {current_page_num} for {brand} (URL: {search_url})")

            soup = scrape_page(driver, search_url)
            
            if soup is None: 
                print(f"Failed to load page {current_page_num} for {brand}. Skipping to next brand.")
                break 

            brand_data_on_page = extract_car_data(soup)
            
            if brand_data_on_page: 
                all_scraped_data.extend(brand_data_on_page)
                print(f"Found {len(brand_data_on_page)} cars on page {current_page_num} for brand {brand}. Total: {len(all_scraped_data)}")
                current_page_num += 1 
                consecutive_empty_pages = 0 
                time.sleep(random.uniform(4, 8)) 
            else:
                consecutive_empty_pages += 1
                print(f"No cars found on page {current_page_num} for {brand}. Consecutive empty pages: {consecutive_empty_pages}")
                
                if consecutive_empty_pages >= max_consecutive_empty:
                    print(f"Reached {max_consecutive_empty} consecutive empty pages for {brand}. Assuming end of results.")
                    break 
                
                current_page_num += 1 
                time.sleep(random.uniform(4, 8)) 


        time.sleep(random.uniform(8, 15)) 

    driver.quit() 

    if all_scraped_data:
        df_scraped = pd.DataFrame(all_scraped_data)
        df_scraped.to_csv(OUTPUT_CSV_FILE, index=False, decimal=',')
        print(f"\nScraping complete. Data saved to '{OUTPUT_CSV_FILE}'")
        print(df_scraped.head())
    else:
        print("No data found.")

if __name__ == "__main__":
    main()
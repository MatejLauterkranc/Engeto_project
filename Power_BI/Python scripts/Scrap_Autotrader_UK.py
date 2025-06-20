from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import csv
import time

def scrape_autotrader_selenium(postcode, make, model):
    """
    Scrapes car listings from AutoTrader using Selenium.
    Starts from a pre-filtered URL with postcode and make.

    Args:
        postcode (str): The UK postcode used in the URL.
        make (str): The make of the car used in the URL (e.g., "Abarth", "Audi").
        model (str): The model of the car (used for CSV output, as it's part of search criteria).

    Returns:
        list: A list of dictionaries, where each dictionary represents a car
              with 'Make', 'Model', 'Car Name', 'Motorization', and 'Price'.
    """
    # Construct the base URL with pre-filled postcode and make
    # This URL starts directly on a search results page
    base_url = (
        f"https://www.autotrader.co.uk/car-search?"
        f"advertising-location=at_cars&homeDeliveryAdverts=include&"
        f"make={make}&postcode={postcode}&sort=relevance"
    )
    results = []

    # --- Selenium Setup ---
    # IMPORTANT: Replace 'path/to/your/chromedriver' with the actual path to your ChromeDriver executable.
    # Download ChromeDriver from: https://chromedriver.chromium.org/downloads
    # Make sure the ChromeDriver version matches your Chrome browser version.
    service = Service(executable_path='chromedriver.exe') # Assuming chromedriver.exe is in the same directory
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Uncomment this line to run Chrome in headless mode (without opening a browser window)
    options.add_argument("--disable-gpu") # Recommended for headless mode
    options.add_argument("--window-size=1920,1080") # Set a fixed window size for consistent rendering
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36")
    options.add_argument("--no-sandbox") # Bypass OS security model, necessary for some environments
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
    # Add an argument to ignore SSL certificate errors, sometimes helps with some sites
    options.add_argument("--ignore-certificate-errors")

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(base_url)
        print(f"Navigated to: {base_url}")

        # --- Handle Cookie/Consent Pop-up ---
        iframe_handled = False
        try:
            print("Attempting to handle cookie consent...")
            iframe_selectors = [
                (By.CSS_SELECTOR, "iframe[id*='sp_message']"),
                (By.CSS_SELECTOR, "iframe[title*='Privacy']"),
                (By.CSS_SELECTOR, "iframe[src*='consent.cmp.site']"),
                (By.CSS_SELECTOR, "iframe[src*='privacy-center']"),
                (By.CSS_SELECTOR, "iframe[name*='__usp_preview__']"),
                (By.ID, "sp_message_iframe"),
                (By.ID, "gdpr-consent-iframe")
            ]

            for selector in iframe_selectors:
                try:
                    WebDriverWait(driver, 5).until(
                        EC.frame_to_be_available_and_switch_to_it(selector)
                    )
                    iframe_handled = True
                    print(f"Switched to potential cookie consent iframe using selector: {selector}")
                    break
                except TimeoutException:
                    pass

            if not iframe_handled:
                print("No specific cookie consent iframe found using common selectors. Trying to find the button in main content.")

            accept_all_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.message-button[title='Accept All']"))
            )
            accept_all_button.click()
            print("Clicked 'Accept All' for cookies.")
            time.sleep(2) # Give a small pause for the overlay to disappear

        except TimeoutException:
            print("Cookie consent pop-up 'Accept All' button not found or not clickable within 15 seconds. Proceeding without clicking.")
        except ElementClickInterceptedException:
            print("Click on 'Accept All' intercepted. Trying JavaScript click.")
            try:
                accept_all_button = driver.find_element(By.CSS_SELECTOR, "button.message-button[title='Accept All']")
                driver.execute_script("arguments[0].click();", accept_all_button)
                print("Forced click on 'Accept All' via JavaScript.")
                time.sleep(2)
            except NoSuchElementException:
                print("Accept All button not found even for JS click. Proceeding.")
        finally:
            if iframe_handled:
                driver.switch_to.default_content()
                print("Switched back to default content.")
        # --- End Cookie/Consent Handling ---

        # The postcode and make are already in the URL, so no form interaction needed
        print(f"Starting search for: Make={make}, Postcode={postcode}")
        
        # Wait for the search results to load.
        # Look for the main car listing containers.
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-testid*='search-listing-item']"))
        )
        print("Search results page loaded.")
        time.sleep(2) # Give a little extra time for all elements to render

        # Extract car data from the results
        car_listings = driver.find_elements(By.CSS_SELECTOR, "li[data-testid*='search-listing-item']")
        print(f"Found {len(car_listings)} car listings on the page.")

        for listing in car_listings:
            try:
                # Find the main title link which contains car name, motorization, and price
                title_link = listing.find_element(By.CSS_SELECTOR, "a[data-testid='search-listing-title']")
                
                # Get the span tag within the title link for motorization and price
                span_tag = title_link.find_element(By.TAG_NAME, 'span')

                # Extract the full text of the <a> tag
                full_title_text = title_link.text.strip()
                # Extract the text of the <span> tag
                span_text = span_tag.text.strip()

                # Car Name is the text of the <a> tag, excluding the <span> content
                car_name = full_title_text.replace(span_text, '').strip()

                # Split span_text into motorization and price
                parts = span_text.split(',')
                motorization = parts[0].strip()
                price = parts[-1].strip() # Take the last part, robust for multiple commas

                results.append({
                    "Make": make,
                    "Model": model, # Use the model passed as argument, as it's implicit in the search
                    "Car Name": car_name,
                    "Motorization": motorization,
                    "Price": price
                })
            except NoSuchElementException as e:
                print(f"Skipping a listing due to missing element: {e}")
                continue # Continue to the next listing

    except TimeoutException:
        print("Timeout: Element not found or page did not load in time. This might indicate issues with page loading or element selectors.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if driver:
            driver.quit() # Close the browser
            print("Browser closed.")
    return results

def save_to_csv(data, filename="autotrader_cars_selenium.csv"):
    """
    Saves a list of dictionaries to a CSV file.

    Args:
        data (list): A list of dictionaries to save.
        filename (str): The name of the CSV file.
    """
    if not data:
        print("No data to save to CSV.")
        return

    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    print(f"Data successfully saved to {filename}")

# --- Main execution ---
if __name__ == "__main__":
    post_code_to_use = "SW1W 0NY"
    car_make_to_search = "Abarth" # Example: "Abarth", "Audi", "BMW" (must be valid in URL)
    car_model_to_search = "595" # Example: "595", "A3", "1 Series" (used for CSV, not direct selection)

    # Perform the scraping
    car_data = scrape_autotrader_selenium(post_code_to_use, car_make_to_search, car_model_to_search)

    # Save the results to a CSV file
    if car_data:
        save_to_csv(car_data)
    else:
        print("No car data retrieved. CSV file not created.")

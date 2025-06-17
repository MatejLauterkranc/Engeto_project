import requests
import time
import csv

def fetch_data(minlat, maxlat, minlon, maxlon):
    """
    Fetches charging station data for a given bounding box from the OpenChargeMap API.
    """
    url = "https://api.openchargemap.io/v3/poi/"
    params = {
        'output': 'json',
        'minlatitude': minlat,
        'maxlatitude': maxlat,
        'minlongitude': minlon,
        'maxlongitude': maxlon,
        'maxresults': 500,
        'compact': True,
        'verbose': False,
        'key': 'd1613f8c-b100-465f-a020-9f800887a141'  # Your API key
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return []

def fetch_all_data_recursive(minlat, maxlat, minlon, maxlon, step=0.05, depth=0, max_depth=5):
    """
    Recursively fetches data from OpenChargeMap API, splitting the bounding box
    if more than maxresults are found or max_depth is reached.
    """
    results = []
    print(f"{' ' * depth * 2}Fetching bbox: {minlat} to {maxlat}, {minlon} to {maxlon}")
    data = fetch_data(minlat, maxlat, minlon, maxlon)
    time.sleep(1)  # Pause to respect API limits
    if len(data) < 500 or depth >= max_depth:
        results.extend(data)
    else:
        midlat = (minlat + maxlat) / 2
        midlon = (minlon + maxlon) / 2
        # Recursively call for the four quadrants
        results.extend(fetch_all_data_recursive(minlat, midlat, minlon, midlon, step/2, depth+1, max_depth))
        results.extend(fetch_all_data_recursive(minlat, midlat, midlon, maxlon, step/2, depth+1, max_depth))
        results.extend(fetch_all_data_recursive(midlat, maxlat, minlon, midlon, step/2, depth+1, max_depth))
        results.extend(fetch_all_data_recursive(midlat, maxlat, midlon, maxlon, step/2, depth+1, max_depth))
    return results

def flatten_dict(d, parent_key='', sep='.'):
    """
    Flattens a nested dictionary into a single-level dictionary with concatenated keys.
    Handles lists by converting them to strings.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # If the item is a list, convert it to a string (or adjust as needed)
            items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    return dict(items)

def save_data_to_csv(data, filename='chargers_data.csv'):
    """
    Saves the fetched and flattened data to a CSV file.
    """
    flat_data = [flatten_dict(item) for item in data]

    # Collect all unique keys to use as CSV headers
    all_keys = set()
    for row in flat_data:
        all_keys.update(row.keys())
    all_keys = sorted(all_keys) # Sort keys for consistent column order

    with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_keys)
        writer.writeheader()
        for row in flat_data:
            writer.writerow(row)

    print(f"Data successfully saved to file {filename}.")

# Start global data fetching
data = fetch_all_data_recursive(-90, 90, -180, 180, max_depth=5)
print(f"Total records fetched: {len(data)}")
save_data_to_csv(data)
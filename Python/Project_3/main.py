import requests
from bs4 import BeautifulSoup
import csv
import sys

def get_soup(url):
    """Stáhne HTML stránku a převede ji na objekt BeautifulSoup."""
    response = requests.get(url)
    response.raise_for_status()  # Ošetření chyb při stahování
    return BeautifulSoup(response.text, "html.parser")

def get_obce_links(main_url):
    """Najde odkazy na jednotlivé obce."""
    soup = get_soup(main_url)
    obce = []
    for row in soup.find_all("tr")[2:]:  # Preskočí hlavičku tabulky
        cells = row.find_all("td")
        if len(cells) > 0:
            link = cells[0].find("a")
            if link:
                obce.append((cells[1].text, "https://www.volby.cz/pls/ps2017nss/" + link["href"]))
    return obce

def get_obec_results(obec_url):
    """Získá volební výsledky pro danou obec."""
    soup = get_soup(obec_url)
    data = {}
    
    # Získání základních informací
    data["registered"] = soup.find("td", headers="sa2").text.strip()
    data["envelopes"] = soup.find("td", headers="sa3").text.strip()
    data["valid"] = soup.find("td", headers="sa6").text.strip()

    # Hlasování pro strany
    parties = soup.find_all("td", headers="t1sa1 t1sb2")
    votes = soup.find_all("td", headers="t1sa2 t1sb3")
    
    for party, vote in zip(parties, votes):
        data[party.text.strip()] = vote.text.strip()
    
    return data

def save_to_csv(filename, data):
    """Uloží seznam dat do CSV souboru."""
    keys = data[0].keys()
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

def main():
    """Hlavní funkce, která spustí celý scraping proces."""
    if len(sys.argv) != 3:
        print("Použití: python projekt_3.py <URL> <soubor.csv>")
        sys.exit(1)

    url = sys.argv[1]
    filename = sys.argv[2]

    print(f"Scraping dat z: {url}")
    obce = get_obce_links(url)

    all_results = []
    for obec_name, obec_url in obce:
        print(f"Stahuji data pro {obec_name}...")
        data = get_obec_results(obec_url)
        data["code"] = obec_url.split("=")[-1]  # Extrahování kódu obce
        data["location"] = obec_name
        all_results.append(data)

    save_to_csv(filename, all_results)
    print(f"Data byla uložena do {filename}")
# 
if __name__ == "__main__":
    main()

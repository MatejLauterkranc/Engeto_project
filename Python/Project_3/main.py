import requests  # Import knihovny pro HTTP požadavky
from bs4 import BeautifulSoup  # Import knihovny pro parsování HTML
import csv  # Import knihovny pro práci s CSV soubory
import json # Import knihovny pro práci s JSON soubory
import sys  # Import knihovny pro práci s argumenty příkazové řádky
import pandas as pd # Import knihovny pro ukládání dat do formátu Excel
import openpyxl # Import knihovny pro práci s Excel (xlsx) soubory
from collections import OrderedDict  # Import OrderedDict pro zachování pořadí sloupců

def get_soup(url):
    """
    Stáhne HTML stránku a převede ji na objekt BeautifulSoup.

    Args:
        url (str): URL adresa stránky ke stažení.

    Returns:
        BeautifulSoup: Objekt BeautifulSoup pro parsování HTML.

    Raises:
        requests.exceptions.HTTPError: Pokud dojde k chybě při stahování stránky.
    """
    response = requests.get(url)  # Pošle HTTP GET požadavek na danou URL
    response.raise_for_status()  # Ošetří případné HTTP chyby (např. 404)
    print(f"Loading page {url} successful")  # Vypíše zprávu o úspěšném načtení stránky
    return BeautifulSoup(response.text, "html.parser")  # Vytvoří objekt BeautifulSoup z textu odpovědi

def get_municipalities_links(main_url):
    """
    Najde odkazy na jednotlivé obce (municipalities) na hlavní stránce.

    Args:
        main_url (str): URL adresa hlavní stránky.

    Returns:
        list: Seznam trojic (code, name, url) pro každou obec.
    """
    soup = get_soup(main_url)  # Získá objekt BeautifulSoup z hlavní URL
    municipalities = []  # Inicializuje prázdný seznam pro municipalities
    for row in soup.find_all("tr")[2:]:  # Projde všechny řádky tabulky (kromě prvních dvou)
        cells = row.find_all("td")  # Najde všechny buňky v řádku
        if len(cells) > 0:  # Pokud řádek obsahuje buňky
            code = cells[0].text.strip()  # Získá kód municipalities (první buňka)
            name = cells[1].text.strip()  # Získá název municipalities (druhá buňka)
            link = cells[0].find("a")  # Najde odkaz v první buňce
            if link:  # Pokud odkaz existuje
                url = "https://www.volby.cz/pls/ps2017nss/" + link["href"]  # Vytvoří kompletní URL municipalities
                municipalities.append((code, name, url))  # Přidá kód, název a URL municipalities do seznamu
    
    print(f"Number of municipalities found on the page: {len(municipalities)}")  # Vypíše počet nalezených obcí
    return municipalities  # Vrátí seznam obcí

def get_municipality_results(municipality_url, municipality_code, municipality_name):
    """
    Získá volební výsledky pro danou obec a vrací OrderedDict s daty.

    Args:
        municipality_url (str): URL adresa stránky s výsledky obce.
        municipality_code (str): Kód obce.
        municipality_name (str): Název obce.

    Returns:
        OrderedDict: Slovník s volebními výsledky.
    """
    soup = get_soup(municipality_url)  # Získá objekt BeautifulSoup z URL municipalities
    data = OrderedDict()  # Vytvoří OrderedDict pro uložení dat municipalities

    # Přidání code a location na začátek
    data["code"] = municipality_code  # Přidá kód municipalities do OrderedDict
    data["location"] = municipality_name  # Přidá název municipalities do OrderedDict

    # Získání základních informací:
    #
    # Získá počet registrovaných voličů
    element = soup.find("td", headers="sa2") # Najde element s počtem registrovaných voličů
    data["registered"] = (
        element.text.strip() # Získá text elementu a odstraní bílé znaky
        if element # Pokud element existuje
        else "N/A" # Pokud element neexistuje, nastaví hodnotu na "N/A"
    ) 

    # Získá počet vydaných obálek
    element = soup.find("td", headers="sa3") # Najde element s počtem vydaných obálek
    data["envelopes"] = (
        element.text.strip() # Získá text elementu a odstraní bílé znaky
        if element # Pokud element existuje
        else "N/A" # Pokud element neexistuje, nastaví hodnotu na "N/A"
    )
    
    # Získá počet platných hlasů
    element = soup.find("td", headers="sa6") # Najde element s počtem platných hlasů
    data["valid"] = (
        element.text.strip() # Získá text elementu a odstraní bílé znaky
        if element # Pokud element existuje
        else "N/A" # Pokud element neexistuje, nastaví hodnotu na "N/A"
    )
    # Zpracování tabulek
    # while cyklus z duvodu prediktivnosti, nevime z budoucnu nebude vice tabulek
    # na webove strance jedna tabulka obsahuje 15 zaznamu, nemuzeme si byt jisti ze nebudeme zpracovavat vice dat
    table_num = 1
    while True:
        parties = soup.find_all("td", headers=f"t{table_num}sa1 t{table_num}sb2") # Najde názvy stran z tabulky
        votes = soup.find_all("td", headers=f"t{table_num}sa2 t{table_num}sb3")  # Najde počty hlasů pro strany z tabulky
        if not parties:  # Pokud tabulka neexistuje, ukončíme cyklus
            break
        for party, vote in zip(parties, votes):
            data[party.text.strip()] = vote.text.strip()
        table_num += 1

    print(f"Data for municipality {municipality_url}: {data}")
    return data

def save_to(filename, data, format):
    """
    Uloží seznam dat do souboru v zadaném formátu.

    Args:
        filename (str): Název výstupního souboru (bez přípony).
        data (list): Seznam slovníků s daty.
        format (str): Formát souboru ('csv', 'json', 'excel')
    """
    if format == "csv":  # Pokud je formát CSV
        keys = data[0].keys()  # Získá klíče (názvy sloupců) z prvního slovníku v seznamu
        with open(f"{filename}.csv", mode="w", newline="", encoding="utf-8") as file:  # Otevře soubor pro zápis
            writer = csv.DictWriter(file, fieldnames=keys)  # Vytvoří objekt pro zápis CSV
            writer.writeheader()  # Zapíše hlavičku CSV souboru
            writer.writerows(data)  # Zapíše data do CSV souboru
    elif format == "json":  # Pokud je formát JSON
        with open(f"{filename}.json", "w", encoding="utf-8") as file:  # Otevře soubor pro zápis
            json.dump(data, file, ensure_ascii=False, indent=4)  # Zapíše data do JSON souboru
    elif format == "excel":  # Pokud je formát Excel
        df = pd.DataFrame(data)  # Vytvoří DataFrame z dat
        df.to_excel(f"{filename}.xlsx", index=False)  # Zapíše DataFrame do Excel souboru
    print(f"The data was saved as {filename}.{format}")  # Vypíše zprávu o uložení dat

def main():
    """Hlavní funkce, která spustí celý scraping proces."""
    if len(sys.argv) != 3:
        print("Chyba: Skript očekává 2 argumenty (URL a název souboru).")
        return
    # Hlavní URL pro scraping který je zadán v terminálu jako první argument, ve formátu "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7103" excel1
    main_url = sys.argv[1]
    # Výběr názevu výstupního souboru zadan v terminalu jako druhý argument např. csv1
    output_file = sys.argv[2] 
    # Číslo výběru formátu, které určí výstupní formát souboru
    print("Vyberte formát uložení:")
    print("1. CSV")
    print("2. JSON")
    print("3. Excel")
    choice = input("Zadejte číslo volby: ") 

    if choice == "1":
        format = "csv"
    elif choice == "2":
        format = "json"
    elif choice == "3":
        format = "excel"
    else:
        print("Neplatná volba. Ukončuji program.")
        return
    municipalities = get_municipalities_links(main_url)  # Získá seznam obcí
    all_data = []  # Inicializuje seznam pro všechna data
    for code, name, url in municipalities:  # Projde všechny obce
        print(f"Getting results for {name} (Number: {code})")  # Vypíše zprávu
        municipality_data = get_municipality_results(url, code, name)  # Získá data obce
        if municipality_data:  # Pokud data existují
            all_data.append(municipality_data)  # Přidá data do seznamu
        else:
            print(f"Error retrieving data for {name}")  # Vypíše chybu
    if all_data:  # Pokud máme nějaká data
        save_to(output_file, all_data, format)  # Uloží data do CSV souboru
        print(f"Results stored in '{output_file}.{format}'")  # Vypíše zprávu o uložení
    else:
        print("No data to process.")  # Vypíše zprávu o nedostatku dat

if __name__ == "__main__":
    main()  # Spustí hlavní funkci, pokud je skript spuštěn přímo
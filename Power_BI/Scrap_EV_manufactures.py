import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "https://m.arenaev.com/"

def make_absolute(url):
    if url.startswith("http"):
        return url
    else:
        return BASE_URL + url

def fetch_soup(url):
    url = make_absolute(url)
    print(f"Fetching URL: {url}")
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp.raise_for_status()
    except requests.exceptions.TooManyRedirects:
        print(f"Too many redirects on URL: {url}")
        return BeautifulSoup("", "html.parser")
    except Exception as e:
        print(f"Failed to fetch URL: {url} - {e}")
        return BeautifulSoup("", "html.parser")
    return BeautifulSoup(resp.content, "html.parser")

def scrap_makers():
    soup = fetch_soup(BASE_URL + "makers.php3")
    makers = []
    for a in soup.find_all("a", href=True):
        strong = a.find("strong")
        if strong:
            makers.append({
                "maker_name": strong.text.strip(),
                "maker_url": BASE_URL + a["href"]
            })
    return makers

def scrap_models(maker):
    soup = fetch_soup(maker["maker_url"])
    models = []
    for a in soup.find_all("a", {"data-model-id": True}):
        models.append({
            "maker_name": maker["maker_name"],
            "model_name": a["data-model-name"],
            "year": a["data-year"].strip(),
            "model_url": BASE_URL + a["href"]
        })
    return models

def scrap_versions(model):
    soup = fetch_soup(model["model_url"])
    versions = []
    select = soup.select_one("div.floating-drive-selector select")
    if select:
        for opt in select.find_all("option"):
            href = opt.get("value")
            if href:
                versions.append({
                    **model,
                    "version_name": opt.text.strip(),
                    "version_url": BASE_URL + href
                })
    else:
        # Pro případ, že žádné volby nejsou – použij model_url s prázdnou verzí
        versions.append({
            **model,
            "version_name": "",
            "version_url": model["model_url"]
        })
    return versions

def scrap_specs(ver):
    soup = fetch_soup(ver["version_url"])
    data = {k: ver[k] for k in ["maker_name","model_name","year","version_name","version_url"]}
    for table in soup.find_all("table"):
        th = table.find("th")
        section = th.text.strip() if th else "Unknown"
        for row in table.find_all("tr"):
            ttl = row.find("td", class_="ttl")
            nfo = row.find("td", class_="nfo")
            if ttl and nfo:
                key = f"{section}.{ttl.text.strip()}"
                data[key] = nfo.text.strip()
    return data

def main():
    results = []
    makers = scrap_makers()
    print(f"💡 Nalezeno výrobců: {len(makers)}")
    for m in makers:
        print(f"Scrapuji výrobce: {m['maker_name']}")
        models = scrap_models(m)
        for mod in models:
            print(f" Model: {mod['model_name']} ({mod['year']})")
            versions = scrap_versions(mod)
            for ver in versions:
                print(f"   🔧 Verze: {ver['version_name']}")
                spec = scrap_specs(ver)
                results.append(spec)
                time.sleep(1)  # respektuj server
        time.sleep(1)

    df = pd.DataFrame(results)
    df.to_csv("arenaev_full_scrape.csv", index=False, encoding="utf-8-sig")
    print("✅ Hotovo! Data uložena do arenaev_full_scrape.csv")

if __name__ == "__main__":
    main()

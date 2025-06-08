#################///////////////   1  /////////////////////###########################################
#Tento skript analyzuje všechny CSV soubory v dané složce
# Zkontroluje, zda mají všechny stejnou strukturu sloupců
# Vytiskne rozdíly (chybějící a přebytečné sloupce)
# Pomůže ti rychle najít problémové soubory, které by mohly způsobit potíže při spojování dat.
#################/////////////////////////////////////###########################################

# import pandas as pd
# import glob
# import os

# # Složka s CSV soubory
# cesta = r"C:\Users\mlaut\Documents\Git\Engeto_project\Power_BI\Sources\openchargemap_country\repair_file"
# soubory = glob.glob(os.path.join(cesta, "*.csv"))

# sloupce_dict = {}

# # Načíst každý soubor a uložit sloupce
# for soubor in soubory:
#     try:
#         df = pd.read_csv(soubor, encoding='utf-8')  # nebo cp1250 podle potřeby
#         sloupce = df.columns.str.strip().tolist()  # očistí mezery
#         sloupce_dict[os.path.basename(soubor)] = sloupce
#     except Exception as e:
#         print(f"Chyba při načítání {soubor}: {e}")

# # Vypsat všechny sloupce ve všech souborech
# print("\nNázvy sloupců v jednotlivých CSV:")
# for soubor, sloupce in sloupce_dict.items():
#     print(f"\n{soubor}:")
#     for sloupec in sloupce:
#         print(f"  - {sloupec}")

# # Porovnání struktur
# referencni_soubor = list(sloupce_dict.keys())[0]
# referencni_sloupce = sloupce_dict[referencni_soubor]

# # Najdeme soubory s odlišnou strukturou
# odlisne_soubory = []
# for soubor, sloupce in sloupce_dict.items():
#     if set(sloupce) != set(referencni_sloupce):
#         odlisne_soubory.append(soubor)

# # Výsledek
# if odlisne_soubory:
#     print("\nPozor! Některé soubory mají jinou strukturu sloupců:")
#     for soubor in odlisne_soubory:
#         print(f"  - {soubor}")
# else:
#     print("\nVšechny soubory mají stejnou strukturu sloupců.")

# print("\nDetailní rozdíly:")
# for soubor, sloupce in sloupce_dict.items():
#     missing = set(referencni_sloupce) - set(sloupce)
#     extra = set(sloupce) - set(referencni_sloupce)
#     if missing or extra:
#         print(f"\n{soubor}:")
#         if missing:
#             print(f"  - Chybí sloupce: {sorted(missing)}")
#         if extra:
#             print(f"  - Přebytečné sloupce: {sorted(extra)}")



#################///////////////// 2   ///////////////////###########################################
# Pro každý CSV:
# Načte soubor (pd.read_csv(soubor))
# Vyčistí názvy sloupců (odebere bílé znaky)
# Uloží seznam sloupců do slovníku sloupce_dict pod jménem souboru
# Když dojde k chybě při čtení, vypíše se na konzoli.
#################/////////////////////////////////////###########################################


# import pandas as pd
# import glob
# import os

# # Složka s CSV soubory
# cesta = r"C:\Users\mlaut\Documents\Git\Engeto_project\Power_BI\Sources\openchargemap_country"
# soubory = glob.glob(os.path.join(cesta, "*.csv"))

# sloupce_dict = {}

# # Načteme všechny názvy sloupců
# for soubor in soubory:
#     try:
#         df = pd.read_csv(soubor, encoding='utf-8')  # nebo cp1250
#         sloupce = df.columns.str.strip().tolist()
#         sloupce_dict[os.path.basename(soubor)] = sloupce
#     except Exception as e:
#         print(f"Chyba při načítání {soubor}: {e}")

# # Najdeme průnik všech sloupců
# spolecne_sloupce = set.intersection(*(set(sloupce) for sloupce in sloupce_dict.values()))
# print(f"\nSpolečné sloupce ve všech CSV: {sorted(spolecne_sloupce)}")

# # Načteme CSV jen s těmito sloupci a spojíme
# dfs = []
# for soubor in soubory:
#     try:
#         df = pd.read_csv(soubor, encoding='utf-8')  # nebo cp1250
#         df = df.loc[:, df.columns.str.strip().isin(spolecne_sloupce)]
#         dfs.append(df)
#     except Exception as e:
#         print(f"Chyba při načítání {soubor}: {e}")

# # Spojíme a uložíme
# final_df = pd.concat(dfs, ignore_index=True)
# final_df.to_csv(r"C:\Users\mlaut\Documents\Git\Engeto_project\Power_BI\Sources\openchargemap_country\merged.csv", index=False)

# print("\nHotovo! Data byla úspěšně sloučena s použitím pouze společných sloupců.")




#################//////////////////  3  /////////////////###########################################
# Načte všechny CSV a zjistí, které sloupce jsou v každém CSV (průnik sloupců)
# Odstraní sloupce, které nejsou ve všech souborech (přebytečné)
# Uloží nové CSV se sjednocenou strukturou, takže každý soubor má stejnou množinu sloupců
#################/////////////////////////////////////###########################################


# import os
# import pandas as pd

# # složka s původními CSV
# input_folder = r"C:\Users\mlaut\Documents\Git\Engeto_project\Power_BI\Sources\openchargemap_country"
# # složka kam uložíš upravené CSV (vytvoř ji, pokud neexistuje)
# output_folder = r"C:\Users\mlaut\Documents\Git\Engeto_project\Power_BI\Sources\openchargemap_country\repair_file"
# os.makedirs(output_folder, exist_ok=True)

# # 1. Načti všechny sloupce z CSV
# all_columns = []
# files = []

# for filename in os.listdir(input_folder):
#     if filename.endswith(".csv"):
#         path = os.path.join(input_folder, filename)
#         df = pd.read_csv(path)
#         all_columns.append(set(df.columns))
#         files.append(filename)

# # 2. Najdi průnik sloupců, které jsou ve všech souborech (společné sloupce)
# common_columns = set.intersection(*all_columns)

# print("Společné sloupce:", common_columns)

# # 3. Projdi všechny soubory, ponech jen společné sloupce a ulož nové CSV
# for filename in files:
#     path = os.path.join(input_folder, filename)
#     df = pd.read_csv(path)
    
#     # ponech jen společné sloupce
#     df_clean = df.loc[:, df.columns.isin(common_columns)]
    
#     # ulož upravený CSV do výstupní složky
#     out_path = os.path.join(output_folder, filename)
#     df_clean.to_csv(out_path, index=False)

# print("Hotovo! Upravené soubory jsou v:", output_folder)

#################//////////////////  4  /////////////////###########################################
# Seřadí soubory podle názvu (pokud chceš, můžeme změnit na jiné třídění).
# Zachová původní název souboru (např. openchargemap_AD).
# Přidá k němu číslo v hranatých závorkách ([1], [2], …).
# Zachová příponu .csv.
#################/////////////////////////////////////###########################################

import os
import glob

# cesta ke složce s CSV soubory
cesta = r"C:\Users\mlaut\Documents\Git\Engeto_project\Power_BI\Sources\openchargemap_country"

# načteme všechny CSV soubory (setřídíme podle názvu)
soubory = sorted(glob.glob(os.path.join(cesta, "*.csv")))

# projdeme soubory a přejmenujeme je
for idx, soubor in enumerate(soubory, start=1):
    nazev = os.path.basename(soubor)
    nazev_bez_pripony, pripona = os.path.splitext(nazev)
    nove_jmeno = f"{nazev_bez_pripony}[{idx}]{pripona}"
    nova_cesta = os.path.join(cesta, nove_jmeno)
    os.rename(soubor, nova_cesta)
    print(f"Přejmenováno: {nazev} -> {nove_jmeno}")

print("Hotovo! 🎉")

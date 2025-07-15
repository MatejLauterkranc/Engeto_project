# EVolution Insights Car: Globální Analýza Elektromobility

---

## Autor
**Matěj Lauterkranc**

---

## Popis Projektu
Vítejte v projektu **_EVolution Insights Car_**, komplexní Power BI analýze zaměřené na **globální vývoj a dopady elektromobility**. Cílem tohoto projektu je poskytnout detailní a ucelený pohled na trh s elektrickými vozidly (EV), srovnat jej s tradičními vozy se spalovacími motory (ICE) a nabídnout uživatelům interaktivní nástroj pro informovaná rozhodnutí. Prozkoumáme vše od infrastruktury a tržních trendů až po ekonomické a environmentální náklady vlastnictví vozidla.

---
## Oficiální Zadání Projektu a Cíle
Tento projekt vznikl v rámci druhého projektu Datové Akademie, který se zaměřuje na vizualizaci dat. Navazuje na první projekt, kde byly připraveny datové podklady a zodpovězeny výzkumné otázky.

**Cíl zadání:** Vizualizovat zvolený dataset s důrazem na zajímavé ukazatele a vhodnou interaktivitu pro čtenáře.

**Kritéria zadání:**
* **Rozsah:** 2-5 stránek
* **Vizuály:** Použití minimálně 5 různých typů vizuálů
* **Filtrování:** Primárně pomocí průřezů/slicerů
* **Interaktivní prvky:** Využití prvků jako jsou záložky, navigace po stranách, odkazy na webové stránky
* **Propojení dat:** Propojení několika (2+) datových tabulek (přes vazby v Power BI nebo Power Query)
* **Hierarchie:** Použití vytvořené hierarchie o alespoň dvou úrovních (nepovinné)
* **Míry a sloupce:** Vytvoření alespoň 1 measure (metrika/míra) a 1 kalkulovaného sloupce/tabulky
* **Grafická úprava:** Vizuální úprava použitých vizuálů, zvolení správných typů vizuálů a vizuálně přívětivý výsledný report

---

## Zadání Projektu
Jako reakce na rostoucí zájem o elektromobilitu a potřebu komplexních dat pro strategické rozhodování, byl definován tento projekt. Jeho účelem je agregovat a vizualizovat klíčové informace o EV sektoru a umožnit srovnání s ICE vozidly, aby bylo možné posoudit skutečné náklady a dopady vlastnictví obou typů vozidel. Projekt slouží jako datový podklad pro potenciální investory, regulační orgány i individuální spotřebitele, kteří hledají přehled o budoucím směřování automobilového průmyslu.

## Hlavní Cíle Projektu
* **Poskytnout ucelený přehled** o stavu a vývoji elektromobility ve světě.
* **Analyzovat klíčové faktory** ovlivňující adopci EV, včetně infrastruktury, nabídky modelů a prodejních trendů.
* **Nabídnout podrobné srovnání** nákladů na vlastnictví a environmentálních dopadů EV vs. ICE vozidel.
* **Vybavit uživatele interaktivním nástrojem** pro simulaci nákladů na vlastnictví vozidla na základě vlastních preferencí (délka používání, roční nájezd, země).

---

## Klíčové sekce a jejich přínos

Projekt je strukturován do několika interaktivních záložek (stránek) v Power BI, z nichž každá se zaměřuje na specifickou oblast analýzy:

### 1. EV Charge Map (Připravenost infrastruktury)
Tato záložka vizualizuje **globální připravenost zemí na elektromobilitu** prostřednictvím **počtu vybudovaných nabíjecích stanic pro EV**. Uživatel může dynamicky filtrovat země a sledovat data na mapě a v kartografickém zobrazení. Interaktivní prstencový graf navíc umožňuje detailní porovnání infrastruktury mezi dvěma vybranými zeměmi.
* **Datové poznámky:** Data o nabíjecích stanicích byla získána primárně metodou **web scrapingu** (Python skript `Scrap_API_Oper_pass_geo.py`). Toto řešení bylo zvoleno po zjištění extrémně vysokých nákladů na komerční databáze a omezeních při získávání dat přes API (limit cca 80 000 záznamů). Proces scrapingu byl technicky velmi náročný a časově náročný (cca 3 týdny), jelikož vyžadoval iterativní procházení mapy po definovaných krocích a kontrolu dostupnosti dat. I přes vynaložené úsilí se podařilo získat data pro necelých **450 000 nabíjecích stanic**, nicméně ne všechny státy jsou v datech kompletně pokryty. Autor si je vědom těchto dílčích omezení, avšak získaný datový vzorek je i tak vysoce vypovídající pro účely této analýzy.

### 2. EV Manufacturers & Models (Tržní nabídka EV)
Zde získáte komplexní přehled o **aktuální nabídce elektromobilů na trhu**. Uživatelé zde mohou prohledávat a filtrovat **výrobce EV aut, konkrétní modely, jejich verze a roky vydání**. Na základě výběru se dynamicky zobrazí klíčové parametry vozidla, jako je minimální a maximální cena, kapacita baterie, dojezd a spotřeba. Dále jsou k dispozici doplňující informace o automobilkách, včetně jejich vlastníků či zakladatelů a logotypů, a detailní přehledová tabulka parametrů.
* **Datové poznámky:** Data o výrobcích, modelech a parametrech EV vozidel byla získána metodou **web scrapingu** pomocí vlastního Python skriptu `Scrap_API_Auto_data.py`.

### 3. EV Sales Share (Prodejní trendy EV)
Tato sekce se zaměřuje na **vývoj prodejů elektromobilů v čase a v rámci jednotlivých států světa**. Zahrnuje také zajímavé informace o **specifickém označování EV automobilů (registrační značky)** v různých zemích, přičemž je pozoruhodné, že i v rámci Evropské unie se značení liší. Prodejní data jsou vizualizována pomocí sloupcových a spojnicových grafů.
* **Datové poznámky:** Prodejní data byla získána z veřejně dostupných open-source zdrojů evropských vládních institucí.

### 4. Compare EV vs. ICE (Makro srovnání technologií)
Tento slide nabízí **široké srovnání mezi elektromobily a vozy se spalovacími motory** napříč různými dimenzemi. Analyzujeme zde:
* **Pořizovací náklady:** Průměrné ceny EV a ICE automobilů.
* **Dotační politiku:** Jak jednotlivé státy podporují nákup EV a jaké benefity nabízejí (pro ICE vozidla dotace nejsou zohledněny).
* **Provozní náklady:** Srovnání cen paliv (elektřiny vs. benzínu/nafty) v různých zemích.
* **Servis a údržba:** Odhadované výdaje na údržbu a servis po dobu vlastnictví vozu.
* **Výkon a uživatelský komfort:** Pohled na průměrnou spotřebu, dojezd a dobu tankování/nabíjení.
* **Environmentální dopady:** Komplexní propočty ekologické stopy automobilu (od výroby, přes provoz, až po konec životnosti), zahrnující propočítané metriky pro obě kategorie vozidel.

### 5. Compare EV vs. ICE\_2 (Detailní srovnání konkrétních modelů)
Tato záložka navazuje na předchozí srovnání, ale umožňuje uživateli provést **detailní analýzu dvou konkrétních, reálných modelů vozidel (jednoho EV a jednoho ICE)** dle vlastního výběru. Uživatel si dále zvolí **předpokládanou délku používání automobilu** (v letech) a **roční nájezd kilometrů**. Následně vybere **zemi nákupu**, což ovlivní aplikovatelnou dotační politiku a průměrné ceny elektrické energie či pohonných hmot v dané zemi. Zohledněny jsou i servisní náklady po celou dobu používání vozu.

V závěru jsou prezentovány čtyři klíčové DAX míry (metriky):

* **`Result EV`**
    * Představuje **celkové náklady na vlastnictví elektromobilu**. Kumuluje počáteční nákupní cenu EV, od které se odečtou dotace a roční benefity, a k níž se přičtou celkové servisní náklady a celkové náklady na elektrickou energii za celé období vlastnictví. Jde o komplexní odhad toho, kolik uživatel celkem zaplatí za vlastnictví a provoz elektromobilu po celou zvolenou dobu.

* **`Result ICE`**
    * Představuje **celkové náklady na vlastnictví vozu se spalovacím motorem (benzín/nafta)**. Kumuluje počáteční nákupní cenu ICE, k níž se přičtou celkové servisní náklady a celkové náklady na pohonné hmoty za celé období vlastnictví. Jde o komplexní odhad toho, kolik uživatel celkem zaplatí za vlastnictví a provoz vozu se spalovacím motorem po celou zvolenou dobu.

* **`Result EV (Náklady bez Pořizovací Ceny)`**
    * Tato míra zobrazuje **pouze kumulované provozní a servisní náklady elektromobilu** za celou dobu používání, kterou si uživatel vybere. Efektivně odečítá počáteční pořizovací cenu vozidla od celkových nákladů, což umožňuje vidět čisté výdaje na jeho provoz a údržbu, které se kumulují během zvoleného období.

* **`Result ICE (Náklady bez Pořizovací Ceny)`**
    * Podobně jako u EV, tato míra uvádí **pouze kumulované provozní a servisní náklady vozu se spalovacím motorem** za celou dobu používání. Odečtením počáteční pořizovací ceny vozidla od celkových nákladů získáte pohled na čisté výdaje na provoz a údržbu ICE vozidla během zvolené doby.

---

## Datové zdroje
Data použitá v projektu pochází z kombinace **web scrapingu** (s využitím vlastních Python skriptů) a **otevřených datových zdrojů** (např. evropských vládních institucí). Vzhledem k technickým a licenčním omezením bylo získání některých dat (zejména nabíjecích stanic) velmi náročné a vedlo k dílčím nekompletnostem v pokrytí států. Přesto je získaný datový vzorek dostatečně reprezentativní pro prezentované analýzy a srovnání.

---

## Replikace Projektu
Pro plnou funkčnost projektu je nezbytné mít k dispozici všechny datové zdroje a správně nastavené prostředí.

1.  **Zajištění datových zdrojů:**
    * Pro data získávaná scrapingem je nutné mít spuštěny a dokončeny Python skripty `Scrap_API_Oper_pass_geo.py` a `Scrap_API_Auto_data.py`. Tyto skripty vyexportují potřebná data ve formátu CSV/Excel, která poté naimportujete do Power BI.
    * Data z otevřených zdrojů (prodeje EV, ekonomické ukazatele) je třeba stáhnout a naimportovat do Power BI.

2.  **Nastavení Power BI:**
    * Otevřete soubor `.pbix` projektu v Power BI Desktopu.
    * Ujistěte se, že jsou všechny datové zdroje správně připojeny a cesty k souborům jsou aktuální. V případě potřeby aktualizujte připojení dat v Power BI.
    * Zkontrolujte a ověřte **vztahy mezi tabulkami** v zobrazení "Model" (Model View), zejména pro správné filtrování dat dle zemí.
    * Ověřte funkčnost všech definovaných DAX měr.

---

## Kontakt
Máte otázky, podněty nebo byste se chtěli o projektu dozvědět více? Neváhejte mě kontaktovat!
* **LinkedIn:** [Matěj Lauterkranc](https://www.linkedin.com/in/mat%C4%9Bj-lauterkranc-8a9b7a228/)
* **E-mail:** m.lauterkranc@gmail.com

---

**Vysvětlivky:**
* **ICE:** Internal Combustion Engine (Vůz se spalovacím motorem)
* **EV:** Electric Vehicle (Elektromobil)
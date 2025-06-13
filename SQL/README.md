# Projekt SQL: Dostupnost potravin v ČR

## Autor
Matěj Lauterkranc

## Popis projektu
Tento projekt analyzuje dostupnost základních potravin (primárně mléka a chleba, ale i dalších kategorií) v České republice z pohledu průměrných mezd a cen v několikaletém období. Cílem je odpovědět na definované výzkumné otázky týkající se životní úrovně a dostupnosti potravin pro širokou veřejnost. Dále se zkoumá vztah mezi HDP a dalšími ekonomickými ukazateli vybraných evropských zemí a vývojem cen a mezd v ČR.

## Zadání projektu (rekapitulace)

Na analytickém oddělení nezávislé společnosti, která se zabývá životní úrovní občanů, bylo dohodnuto, že se pokusíme odpovědět na pár definovaných výzkumných otázek, které adresují dostupnost základních potravin široké veřejnosti. Kolegové již vydefinovali základní otázky, na které se pokusí odpovědět a poskytnout tuto informaci tiskovému oddělení. Toto oddělení bude výsledky prezentovat na následující konferenci zaměřené na tuto oblast.

Pro tento úkol je potřeba připravit robustní datové podklady, ve kterých bude možné vidět porovnání dostupnosti potravin na základě průměrných příjmů za určité časové období.

Jako dodatečný materiál je požadována tabulka s HDP, GINI koeficientem a populací dalších evropských států ve stejném období, jako primární přehled pro ČR.

Výstupem projektu mají být dvě tabulky v databázi:
1.  `t_matej_lauterkranc_project_sql_primary_final`: Data mezd a cen potravin za Českou republiku sjednocených na totožné porovnatelné období. Tato tabulka je rozšířena o detaily potřebné pro zodpovězení všech výzkumných otázek (např. mzdy dle odvětví, ceny všech kategorií potravin).
2.  `t_matej_lauterkranc_project_sql_secondary_final`: Dodatečná data o HDP, GINI a populaci dalších evropských státech.

Dále je potřeba připravit sadu SQL dotazů, které z těchto dvou nově vytvořených tabulek získají datový podklad k odpovězení na vytyčené výzkumné otázky.


## Datové zdroje

Projekt využívá data z veřejně dostupné databáze Engeto Akademie (nebo jejích zrcadlených online verzí). Konkrétně se jedná o následující tabulky:

**Primární tabulky:**

- `czechia_payroll` – Informace o mzdách v různých odvětvích za několikaleté období. Datová sada pochází z Portálu otevřených dat ČR.
- `czechia_payroll_calculation` – Číselník kalkulací v tabulce mezd.
- `czechia_payroll_industry_branch` – Číselník odvětví v tabulce mezd.
- `czechia_payroll_unit` – Číselník jednotek hodnot v tabulce mezd.
- `czechia_payroll_value_type` – Číselník typů hodnot v tabulce mezd.
- `czechia_price` – Informace o cenách vybraných potravin za několikaleté období. Datová sada pochází z Portálu otevřených dat ČR.
- `czechia_price_category` – Číselník kategorií potravin, které se vyskytují v našem přehledu.

**Číselníky sdílených informací o ČR:**

- `czechia_region` – Číselník krajů České republiky dle normy CZ-NUTS 2.
- `czechia_district` – Číselník okresů České republiky dle normy LAU.

**Dodatečné tabulky:**

- `countries` - Všemožné informace o zemích na světě, například hlavní město, měna, národní jídlo nebo průměrná výška populace.
- `economies` - HDP, GINI, daňová zátěž, atd. pro daný stát a rok.

**Poznámka:** Je nutné mít přístup k těmto datům – bez nich projekt nebude fungovat. Pokud databázi nemáte, je třeba si ji stáhnout z oficiálního vzdělávacího rozhraní Engeto Akademie (viz jejich studijní portál).

## Výstupní tabulky

### `t_matej_lauterkranc_project_sql_primary_final`
Tato tabulka je komplexním zdrojem dat pro analýzu v ČR. Obsahuje:
-   `year`: Rok
-   `industry_branch_name`: Název odvětví (pro detailní analýzu mezd)
-   `avg_wage_per_industry`: Průměrná mzda v daném odvětví za daný rok
-   `overall_avg_wage`: Celková průměrná mzda v ČR za daný rok
-   `price_category_name`: Název kategorie potraviny
-   `avg_price_per_category`: Průměrná cena pro danou kategorii potravin za daný rok
-   `avg_price_milk`: Průměrná cena mléka
-   `avg_price_bread`: Průměrná cena chleba
-   `milk_liters`: Kolik litrů mléka si lze koupit za průměrnou mzdu
-   `bread_kg`: Kolik kg chleba si lze koupit za průměrnou mzdu

### `t_matej_lauterkranc_project_sql_secondary_final`
Obsahuje ekonomické ukazatele pro vybrané evropské státy:
-   `country`: Název země ('Czech Republic', 'Germany', 'Austria', 'Poland', 'Slovakia', 'Hungary')
-   `year`: Rok
-   `gdp_per_capita`: HDP na obyvatele
-   `gini_index`: GINI koeficient
-   `population`: Populace

## Výzkumné otázky a jejich řešení

Všechny následující otázky jsou zodpovězeny **výhradně na základě dat z tabulek `t_matej_lauterkranc_project_sql_primary_final` a `t_matej_lauterkranc_project_sql_secondary_final`**.

1.  **Rostou v průběhu let mzdy ve všech odvětvích, nebo v některých klesají?**
    -   Řešeno dotazem na `t_matej_lauterkranc_project_sql_primary_final`, seskupením dat podle odvětví a roku pro sledování trendů `avg_wage_per_industry`.

2.  **Kolik je možné si koupit litrů mléka a kilogramů chleba za první a poslední srovnatelné období v dostupných datech cen a mezd?**
    -   Řešeno dotazem na `t_matej_lauterkranc_project_sql_primary_final`, výběrem dat pro minimální a maximální rok a využitím sloupců `milk_liters` a `bread_kg`.

3.  **Která kategorie potravin zdražuje nejpomaleji (je u ní nejnižší percentuální meziroční nárůst)?**
    -   Řešeno dotazem na `t_matej_lauterkranc_project_sql_primary_final`, výpočtem meziročních procentuálních změn cen pro jednotlivé kategorie potravin (`avg_price_per_category`) a následným průměrováním a seřazením.

4.  **Existuje rok, ve kterém byl meziroční nárůst cen potravin výrazně vyšší než růst mezd (větší než 10 %)?**
    -   Řešeno dotazem na `t_matej_lauterkranc_project_sql_primary_final`, porovnáním meziročního růstu celkové průměrné mzdy (`overall_avg_wage`) a cen mléka a chleba (`avg_price_milk`, `avg_price_bread`).

5.  **Má výška HDP vliv na změny ve mzdách a cenách potravin? Neboli, pokud HDP vzroste výrazněji v jednom roce, projeví se to na cenách potravin či mzdách ve stejném nebo následujícím roce výraznějším růstem?**
    -   Řešeno spojením `t_matej_lauterkranc_project_sql_primary_final` a `t_matej_lauterkranc_project_sql_secondary_final` pro Českou republiku a výpočtem korelace mezi HDP (`gdp_per_capita`) a `overall_avg_wage`, `avg_price_milk`, `avg_price_bread` pro stejný rok a pro následující rok (s použitím `LEAD` funkce).

## Poznámky k datům
-   V datech se vyskytují chybějící hodnoty (`NULL`), které jsou v primárních `CREATE TABLE` dotazech ošetřeny pomocí `IS NOT NULL` v `WHERE` klauzuli nebo `COALESCE` a `NULLIF` pro bezpečné dělení nulou.
-   Roky, které neměly dostatečná data v obou primárních zdrojích (mzdy i ceny), byly při tvorbě finální primární tabulky zohledněny pro sjednocené období.

## Replikace projektu
1.  Ujistěte se, že máte přístup k databázi Engeto Academy nebo k SQL souboru s databází, a že jsou nahrány všechny zdrojové tabulky.
2.  Spusťte kompletní SQL skript (`projekt_sql.sql`) v preferovaném databázovém prostředí (např. PostgreSQL).
3.  Skript nejprve smaže existující finální tabulky (pokud existují) a poté je znovu vytvoří s aktuálními daty.
4.  Následují dotazy pro zobrazení prvních řádků finálních tabulek.
5.  Nakonec jsou v skriptu definovány a spuštěny SQL dotazy, které získávají data potřebná k zodpovězení všech pěti výzkumných otázek.

## Kontakt
Máte otázky? Kontaktujte mě na [LinkedIn](https://www.linkedin.com/in/mat%C4%9Bj-lauterkranc-8a9b7a228/) nebo přes e-mail: m.lauterkranc@gmail.com
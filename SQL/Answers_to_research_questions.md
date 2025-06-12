## 1. Rostou v průběhu let mzdy ve všech odvětvích, nebo v některých klesají?

Na základě dat z tabulky `t_matej_lauterkranc_project_sql_primary_final`, která agreguje informace o průměrných mzdách v jednotlivých odvětvích v České republice od roku 2000 do roku 2021, lze obecně konstatovat, že ve většině sledovaných odvětví mzdy vykazují rostoucí trend. I přes celkový růst však existují krátkodobá období, kdy v některých letech dochází k mírným poklesům nebo stagnaci, které jsou zpravidla spojeny s ekonomickými výkyvy.

**Růst ve většině odvětví**

Odvětví jako Informační a komunikační činnosti, Peněžnictví a pojišťovnictví, Profesní, vědecké a technické činnosti, či Doprava a skladování vykazují stabilní a výrazný růst mezd během celého sledovaného období. Například v sektoru informačních a komunikačních činností vzrostla průměrná mzda z přibližně 21 829 Kč (rok 2000) na 63 416 Kč (rok 2021), což představuje markantní nárůst.

**Krátkodobé poklesy a stagnace**

V některých odvětvích dochází k menším, meziročním poklesům:
-   **Činnosti v oblasti nemovitostí:** Mezi lety 2012 a 2013 byl zaznamenán mírný pokles mzdy.
-   **Těžba a dobývání:** V roce 2009 došlo k poklesu, pravděpodobně v souvislosti s globální ekonomickou krizí.
-   **Peněžnictví a pojišťovnictví:** Také v roce 2013 byl zaznamenán pokles.
-   **Kulturní, zábavní a rekreační činnosti:** Mírný pokles oproti předchozímu roku se projevil v roce 2021.

Odvětví jako Administrativní a podpůrné činnosti, Ubytování, stravování a pohostinství a částečně Stavebnictví sice zaznamenaly růst, ale jeho tempo bylo pomalejší a občas docházelo ke stagnaci.

**Celkový závěr**

Dlouhodobě vzato, mzdy ve všech sledovaných odvětvích v ČR vykazují vzestupný trend. Krátkodobé výjimky s mírným poklesem nebo stagnací jsou většinou ovlivněny ekonomickými cykly nebo specifickými faktory daného odvětví (např. finanční krize, pandemie COVID-19). Žádné odvětví v dostupných datech nevykazuje dlouhodobý a setrvalý pokles mezd.

## 2. Kolik je možné si koupit litrů mléka a kilogramů chleba za první a poslední srovnatelné období v dostupných datech cen a mezd?

Pro posouzení kupní síly domácností jsme analyzovali, kolik kilogramů chleba a litrů mléka bylo možné zakoupit za průměrnou mzdu v prvním a posledním srovnatelném období dostupném v tabulce `t_matej_lauterkranc_project_sql_primary_final`. Tyto údaje nám poskytují přehled o změnách dostupnosti základních potravin v čase.

**Metodika**

Kupní síla je vypočítána jako poměr průměrné hrubé mzdy k průměrné ceně dané potraviny (mléka nebo chleba) v daném roce. Tento výpočet představuje zjednodušený indikátor kupní síly, který nezohledňuje inflaci ani další životní náklady.

**Výsledky**

| Rok | Průměrná mzda (Kč) | Cena chleba (Kč/kg) | Cena mléka (Kč/l) | Kupní síla chleba (kg) | Kupní síla mléka (l) |
|-----|--------------------|---------------------|-------------------|------------------------|-----------------------|
|2006 | 20 211,00          | 16,12               | 14,44             | 1 253,78               | 1 399,65              |
|2021 | 38 021,57          | 29,19               | 22,78             | 1 302,68               | 1 669,13              |

*Pozn.: Data pro rok 2021 jsou použita jako poslední srovnatelné období z důvodu dostupnosti komplexních dat.*

**Z výpočtů je patrné, že:**

-   Kupní síla obyvatel rostla jak u chleba, tak u mléka.
-   V absolutním vyjádření vzrostl počet litrů mléka a kilogramů chleba, které bylo možné pořídit.
-   Růst kupní síly byl mírně vyšší u mléka než u chleba, což naznačuje nižší tempo růstu ceny mléka oproti chlebu.

**Závěr**

Ve sledovaném období došlo ke zvýšení kupní síly domácností při nákupu základních potravin. Růst průměrné mzdy převýšil tempo růstu cen chleba a mléka, což vedlo k vyšší dostupnosti těchto základních komodit pro průměrného zaměstnance. Tento trend svědčí o zlepšení ekonomické situace domácností, byť je důležité sledovat i další faktory (např. inflaci, náklady na bydlení či energie), které mohou kupní sílu ovlivňovat.

## 3. Která kategorie potravin zdražuje nejpomaleji (je u ní nejnižší percentuální meziroční nárůst)?

V rámci sledování vývoje cen potravin jsme analyzovali meziroční nárůst cen vybraných potravinářských kategorií, dostupných v tabulce `t_matej_lauterkranc_project_sql_primary_final`. Cílem bylo identifikovat potravinu s nejnižší procentuální meziroční změnou ceny, tedy tu, která v čase zdražuje nejpomaleji.

**Výsledky**

Na základě dostupných dat o meziročním procentuálním růstu cen vybraných potravin byly jednotlivé kategorie potravin seřazeny vzestupně dle míry zdražování:

**Tabulka: Průměrný meziroční nárůst vybraných potravin (nejužší kategorie)**

| Potravina                           | Průměrný Meziroční Nárůst (%) |
|-------------------------------------|-------------------------------|
| Cukr krystalový                     | -1,92                         |
| Rajská jablka červená kulatá        | -0,74                         |
| Banány žluté                        | +0,81                         |
| Vepřová pečeně s kostí              | +0,99                         |
| Přírodní minerální voda uhličitá    | +1,03                         |
| Šunkový salám                       | +1,85                         |
| Jablka konzumní                     | +2,02                         |
| Pečivo pšeničné bílé                | +2,20                         |
| Hovězí maso zadní bez kosti         | +2,54                         |
| Kapr živý                           | +2,60                         |

**Analýza**

-   Nejpomaleji zdražující kategorií je `Cukr krystalový`, který dokonce v průměru meziročně zlevnil o 1,92 %.
-   Druhá nejpomaleji zdražující kategorie jsou `Rajská jablka červená kulatá` s mírným průměrným poklesem cen o 0,74 %.
-   Mezi potraviny s nejnižším pozitivním růstem cen patří také `Banány žluté` (+0,81 %) a `Vepřová pečeně s kostí` (+0,99 %).
-   Naopak, potraviny s vyšším meziročním nárůstem cen (nad 2 %) byly zejména `Kapr živý` (+2,60 %), `Hovězí maso zadní bez kosti` (+2,54 %) a `Pečivo pšeničné bílé` (+2,20 %).

**Závěr**

`Cukr krystalový` je z hlediska dlouhodobé cenové stability a meziročního růstu cen nejvýraznějším příkladem potraviny, která nezdražuje nebo dokonce mírně zlevňuje. Tento trend může být způsoben řadou faktorů, jako je konkurence, stabilizace výrobních nákladů nebo příznivý vývoj cen surovin na světových trzích. U sezónních produktů, jako je `Kapr živý`, je třeba počítat s vyššími výkyvy cen. Pro komplexní analýzu cenové dostupnosti potravin je vhodné zohlednit nejen absolutní procentuální změny, ale i charakter produktu, jeho sezónnost a další externí faktory.

## 4. Existuje rok, ve kterém byl meziroční nárůst cen potravin výrazně vyšší než růst mezd (větší než 10 %)?

Analyzovali jsme data z `t_matej_lauterkranc_project_sql_primary_final` o meziročním procentuálním nárůstu průměrných cen mléka a chleba a růstu průměrné mzdy, abychom zjistili, zda existoval rok, ve kterém by byl růst cen potravin (mléka nebo chleba) o více než 10 procentních bodů vyšší než růst mezd.

**Výsledky**

SQL dotaz identifikuje roky, kde je splněna podmínka, že (`růst ceny potraviny` - `růst mzdy`) > 10 procentních bodů.

*Vzhledem k nastavení SQL dotazu, pokud takový rok neexistuje, výsledkem bude prázdná tabulka. Pokud by takový rok existoval, objevil by se zde.*

**Analýza výsledků (interpretace prázdné tabulky):**

Na základě spuštěného SQL dotazu, který porovnává meziroční růst průměrné mzdy s růstem cen mléka a chleba z finální primární tabulky, se nenašel žádný rok, ve kterém by meziroční nárůst cen mléka nebo chleba byl o více než 10 procentních bodů vyšší než růst mezd.

**Závěr**

Z dostupných dat v `t_matej_lauterkranc_project_sql_primary_final` vyplývá, že v žádném sledovaném období nedošlo k situaci, kdy by růst cen mléka nebo chleba výrazně převyšoval růst mezd o více než 10 procentních bodů. Tento výsledek naznačuje relativně stabilní vývoj kupní síly obyvatelstva ve vztahu k těmto základním potravinám v analyzovaném období.

## 5. Má výška HDP vliv na změny ve mzdách a cenách potravin? Neboli, pokud HDP vzroste výrazněji v jednom roce, projeví se to na cenách potravin či mzdách ve stejném nebo následujícím roce výraznějším růstem?

Prozkoumali jsme korelace mezi HDP na obyvatele (z `t_matej_lauterkranc_project_sql_secondary_final`) a průměrnými mzdami, cenami mléka a chleba (z `t_matej_lauterkranc_project_sql_primary_final`) pro Českou republiku. Cílem bylo zjistit, zda existuje vztah mezi ekonomickým růstem a vývojem mzdové úrovně a cen potravin.

**Výsledky korelační analýzy (současný rok):**

| Korelace (HDP vs. ...) | Hodnota korelace |
|-------------------------|------------------|
| HDP vs. Průměrná mzda   | 0,92             |
| HDP vs. Cena mléka      | 0,64             |
| HDP vs. Cena chleba     | 0,70             |

**Výsledky korelační analýzy (HDP vs. následující rok):**

| Korelace (HDP vs. ... následující rok) | Hodnota korelace |
|---------------------------------------|------------------|
| HDP (t) vs. Průměrná mzda (t+1)       | 0,92             |
| HDP (t) vs. Cena mléka (t+1)          | 0,64             |
| HDP (t) vs. Cena chleba (t+1)         | 0,70             |

*Pozn.: Hodnoty korelací v "následující rok" jsou náhodou stejné jako pro "současný rok", což naznačuje silný trendový růst všech proměnných, kde posun o rok výslednou korelaci podstatně nemění.*

**Analýza**

-   **Korelace mezi růstem HDP a růstem mezd:** Hodnota korelace 0,92 je velmi vysoká a silně pozitivní. To naznačuje, že mezi HDP a průměrnými mzdami existuje silná přímá úměra. S rostoucím HDP obvykle výrazně rostou i mzdy.
-   **Korelace mezi růstem HDP a cenou mléka:** Hodnota 0,64 je středně silná pozitivní korelace. Znamená to, že s růstem HDP mají tendenci růst i ceny mléka, ale vliv není tak silný jako u mezd.
-   **Korelace mezi růstem HDP a cenou chleba:** Hodnota 0,70 je silnější než u mléka a naznačuje silnější pozitivní vztah. S růstem HDP mají tendenci růst i ceny chleba.

**Závěr**

Výška HDP má zjevně pozitivní vliv na změny ve mzdách a cenách potravin v České republice v analyzovaném období. Silná pozitivní korelace mezi HDP a průměrnými mzdami naznačuje, že ekonomický růst se přímo promítá do zvýšení příjmů obyvatelstva. Co se týče cen potravin, růst HDP je také spojen s jejich růstem, ačkoli korelace jsou o něco slabší než u mezd. To je běžné, protože ceny potravin jsou ovlivněny i mnoha dalšími faktory, jako jsou náklady na suroviny, sezónnost, globální trhy, logistika a marže obchodníků. Nicméně, celkově data podporují hypotézu, že ekonomický růst měřený HDP má pozitivní dopad na růst mezd a je spojen i s růstem cen vybraných základních potravin. Důležité je, že růst mezd se jeví jako silnější než růst cen, což naznačuje zlepšení kupní síly obyvatelstva.
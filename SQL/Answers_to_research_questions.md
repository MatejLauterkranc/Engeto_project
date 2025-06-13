## 1. Rostou v průběhu let mzdy ve všech odvětvích, nebo v některých klesají?

Na základě dat z tabulky `t_matej_lauterkranc_project_sql_primary_final`, která agreguje informace o průměrných mzdách v jednotlivých odvětvích v České republice od roku 2006 do roku 2018, lze obecně konstatovat, že ve většině sledovaných odvětví mzdy vykazují rostoucí trend. I přes celkový růst však existují krátkodobá období, kdy v některých letech dochází k mírným poklesům nebo stagnaci, které jsou zpravidla spojeny s ekonomickými výkyvy.

**Růst ve většině odvětví**

Odvětví jako Informační a komunikační činnosti, Peněžnictví a pojišťovnictví, Profesní, vědecké a technické činnosti, či Doprava a skladování vykazují stabilní a výrazný růst mezd během celého sledovaného období. Například v sektoru informačních a komunikačních činností vzrostla průměrná mzda z přibližně 35 367 Kč (rok 2006) na 56 101 Kč (rok 2018), což představuje markantní nárůst.

**Krátkodobé poklesy a stagnace**

V některých odvětvích dochází k menším, meziročním poklesům:

-   **Činnosti v oblasti nemovitostí:** Mezi lety 2012 (21 995 Kč) a 2013 (21 622 Kč) byl zaznamenán mírný pokles mzdy.
-   **Těžba a dobývání:** V roce 2009 došlo k poklesu (29 254 Kč v roce 2008 na 28 160 Kč v roce 2009), pravděpodobně v souvislosti s globální ekonomickou krizí. Další poklesy byly i v letech 2013 a 2016.
-   **Peněžnictví a pojišťovnictví:** Také v roce 2013 byl zaznamenán poměrně výrazný pokles (z 50 253 Kč v roce 2012 na 45 775 Kč v roce 2013).
-   **Kulturní, zábavní a rekreační činnosti:** Mírné poklesy byly zaznamenány například mezi lety 2010 a 2011, a 2012 a 2013.
-   **Veřejná správa a obrana; povinné sociální zabezpečení:** Mzdy mírně klesaly mezi lety 2009 a 2011.
Odvětví jako Administrativní a podpůrné činnosti, Ubytování, stravování a pohostinství a částečně Stavebnictví sice zaznamenaly růst, ale jeho tempo bylo pomalejší a občas docházelo ke stagnaci nebo drobným poklesům.

**Celkový závěr**

Dlouhodobě vzato, mzdy ve všech sledovaných odvětvích v ČR vykazují vzestupný trend. Krátkodobé výjimky s mírným poklesem nebo stagnací jsou většinou ovlivněny ekonomickými cykly nebo specifickými faktory daného odvětví. Žádné odvětví v dostupných datech (2006-2018) nevykazuje dlouhodobý a setrvalý pokles mezd.

---
## 2. Kolik je možné si koupit litrů mléka a kilogramů chleba za první a poslední srovnatelné období v dostupných datech cen a mezd?

Pro posouzení kupní síly domácností jsme analyzovali, kolik kilogramů chleba a litrů mléka bylo možné zakoupit za průměrnou mzdu v prvním (2006) a posledním (2018) srovnatelném období dostupném v tabulce `t_matej_lauterkranc_project_sql_primary_final`. Tyto údaje nám poskytují přehled o změnách dostupnosti základních potravin v čase.

**Metodika**

Kupní síla je vypočítána jako poměr průměrné hrubé mzdy k průměrné ceně dané potraviny (mléka nebo chleba) v daném roce. Tento výpočet představuje zjednodušený indikátor kupní síly, který nezohledňuje inflaci ani další životní náklady.

**Výsledky**

| Rok | Průměrná mzda (Kč) | Cena chleba (Kč/kg) | Cena mléka (Kč/l) | Kupní síla chleba (kg) | Kupní síla mléka (l) |
|-----|--------------------|---------------------|-------------------|------------------------|----------------------|
|2006 | 20 677,04          | 16,12               | 14,44             | 1 282,41               | 1 432,14             |
|2018 | 32 485,09          | 24,24               | 19,82             | 1 340,23               | 1 639,21             |


**Z výpočtů je patrné, že:**

-   **Kupní síla obyvatel obecně rostla** jak u chleba, tak u mléka. Průměrná mzda v roce 2018 umožňuje zakoupit více litrů mléka i kilogramů chleba než v roce 2006.
-   **Nárůst kupní síly byl výraznější u mléka.** Zatímco počet litrů mléka, které si průměrný člověk mohl koupit, vzrostl z 1 432,14 l na 1 639,21 l (nárůst o 207,07 l) což představuje 12,63 %, počet kilogramů chleba vzrostl z 1 282,41 kg na 1 340,23 kg (nárůst o 57,82 kg), což představuje 4,31 %. Tento rozdíl naznačuje, že cena mléka rostla pomaleji ve srovnání s průměrnou mzdou a cenou chleba.

**Závěr**

Ve sledovaném období (2006-2018) došlo ke zvýšení kupní síly domácností při nákupu základních potravin, konkrétně chleba a mléka. Růst průměrné mzdy převýšil tempo růstu cen obou komodit, což vedlo k vyšší dostupnosti těchto základních položek pro průměrného zaměstnance. Tento trend svědčí o zlepšení ekonomické situace domácností z hlediska dostupnosti potravin, byť je důležité sledovat i další faktory (např. inflaci, náklady na bydlení či energie), které mohou celkovou kupní sílu ovlivňovat.

---
## 3. Která kategorie potravin zdražuje nejpomaleji (je u ní nejnižší percentuální meziroční nárůst)?

V rámci sledování vývoje cen potravin jsme analyzovali meziroční nárůst cen vybraných potravinářských kategorií, dostupných v tabulce `t_matej_lauterkranc_project_sql_primary_final`. Cílem bylo identifikovat potravinu s nejnižším procentuálním meziročním změnou ceny, tedy tu, která v čase zdražuje nejpomaleji.


**Výsledky**

Na základě dostupných dat o meziročním procentuálním růstu cen vybraných potravin byly jednotlivé kategorie potravin seřazeny vzestupně dle míry zdražování:

**Tabulka: Průměrný meziroční nárůst vybraných potravin (nejužší kategorie)**

| Potravina                                | Průměrný Meziroční Nárůst (%) |
|------------------------------------------|-------------------------------|
| Cukr krystalový                          | -1,92                         |
| Rajská jablka červená kulatá             | -0,74                         |
| Banány žluté                             | +0,81                         |
| Vepřová pečeně s kostí                   | +0,99                         |
| Přírodní minerální voda uhličitá         | +1,02                         |
| Šunkový salám                            | +1,86                         |
| Jablka konzumní                          | +2,01                         |
| Pečivo pšeničné bílé                     | +2,20                         |
| Hovězí maso zadní bez kosti              | +2,54                         |
| Kapr živý                                | +2,60                         |


**Analýza**

-   Nejpomaleji zdražující kategorií je **`Cukr krystalový`**, který dokonce v průměru meziročně zlevnil o 1,92 %.
-   Druhá nejpomaleji zdražující kategorie jsou **`Rajská jablka červená kulatá`** s mírným průměrným poklesem cen o 0,74 %.
-   Mezi potraviny s nejnižším pozitivním růstem cen patří také **`Banány žluté`** (+0,81 %) a **`Vepřová pečeně s kostí`** (+0,99 %).
-   Naopak, potraviny s vyšším meziročním nárůstem cen (nad 2 %) byly zejména **`Kapr živý`** (+2,60 %), **`Hovězí maso zadní bez kosti`** (+2,54 %) a **`Pečivo pšeničné bílé`** (+2,20 %).

**Závěr**

**`Cukr krystalový`** je z hlediska dlouhodobé cenové stability a meziročního růstu cen nejvýraznějším příkladem potraviny, která nezdražuje nebo dokonce mírně zlevňuje. Tento trend může být způsoben řadou faktorů, jako je konkurence, stabilizace výrobních nákladů nebo příznivý vývoj cen surovin na světových trzích. U sezónních produktů, jako je **`Kapr živý`**, je třeba počítat s vyššími výkyvy cen. Pro komplexní analýzu cenové dostupnosti potravin je vhodné zohlednit nejen absolutní procentuální změny, ale i charakter produktu, jeho sezónnost a další externí faktory.

---
## 4. Existuje rok, ve kterém byl meziroční nárůst cen potravin výrazně vyšší než růst mezd (větší než 10 %)?

Analyzovali jsme data z `t_matej_lauterkranc_project_sql_primary_final` o meziročním procentuálním nárůstu průměrných cen mléka a chleba a růstu průměrné mzdy, abychom zjistili, zda existoval rok, ve kterém by byl růst cen potravin (mléka nebo chleba) o více než 10 procentních bodů vyšší než růst mezd.


**Výsledky**

SQL dotaz identifikoval následující roky, kde je splněna podmínka, že rozdíl mezi meziročním růstem ceny potraviny a růstem mzdy je větší než 10 procentních bodů:

| Rok  | Růst mezd (%) | Růst ceny mléka (%) | Růst ceny chleba (%) | Rozdíl (mléko - mzda) (%) | Rozdíl (chléb - mzda) (%) |
|------|---------------|---------------------|----------------------|---------------------------|---------------------------|
| 2007 | 6,86          | 8,00                | 16,89                | 1,14                      | **10,03** |
| 2008 | 7,87          | 15,00               | 21,41                | 7,13                      | **13,54** |
| 2011 | 2,31          | 10,05               | 17,61                | 7,74                      | **15,30** |


**Analýza výsledků:**

Z výše uvedené tabulky je patrné, že se našly roky, ve kterých byl meziroční nárůst cen chleba výrazně vyšší než růst průměrných mezd o více než 10 procentních bodů. Konkrétně se jedná o:

* **Rok 2007:** Růst ceny chleba převýšil růst mezd o **10,03 procentních bodů**.
* **Rok 2008:** Růst ceny chleba převýšil růst mezd o **13,54 procentních bodů**. V tomto roce došlo k výraznému zdražení chleba i mléka.
* **Rok 2011:** Růst ceny chleba převýšil růst mezd o **15,30 procentních bodů**, což představuje největší zaznamenaný rozdíl.

V žádném ze sledovaných let se však nenašla situace, kdy by cena **mléka** rostla o více než 10 procentních bodů rychleji než mzdy. To naznačuje, že i když ceny potravin mohou překonávat růst mezd, intenzita se liší napříč komoditami.


**Závěr**

Na rozdíl od původního předpokladu **existují roky (konkrétně 2007, 2008 a 2011), ve kterých meziroční nárůst cen chleba výrazně převýšil růst průměrných mezd o více než 10 procentních bodů.** To má přímý dopad na kupní sílu obyvatelstva a dostupnost této základní potraviny. V těchto letech se průměrný spotřebitel mohl potýkat s relativně rychlejším zdražováním chleba oproti svému příjmu. Tato zjištění jsou klíčová pro pochopení dynamiky cen a mezd v České republice a jejich dopadu na životní úroveň.

---
## 5. Má výška HDP vliv na změny ve mzdách a cenách potravin? Neboli, pokud HDP vzroste výrazněji v jednom roce, projeví se to na cenách potravin či mzdách ve stejném nebo následujícím roce výraznějším růstem?

Prozkoumali jsme korelace mezi HDP na obyvatele (z `t_matej_lauterkranc_project_sql_secondary_final`) a průměrnými mzdami, cenami mléka a chleba (z `t_matej_lauterkranc_project_sql_primary_final`) pro Českou republiku. Cílem bylo zjistit, zda existuje vztah mezi ekonomickým růstem a vývojem mzdové úrovně a cen potravin.



**Výsledky korelační analýzy (současný rok):**

Tato analýza zkoumá vztah mezi HDP a mzdami/cenami potravin ve stejném roce.

| Korelace (HDP vs. ...) | Hodnota korelace |
|-------------------------|------------------|
| HDP vs. Průměrná mzda   | 0,92             |
| HDP vs. Cena mléka      | 0,64             |
| HDP vs. Cena chleba     | 0,70             |



**Výsledky korelační analýzy (HDP vs. následující rok):**

Tato analýza zkoumá, zda růst HDP v jednom roce ovlivňuje mzdy a ceny potravin v roce následujícím.

| Korelace (HDP (t) vs. ... (t+1)) | Hodnota korelace |
|-----------------------------------|------------------|
| HDP (t) vs. Průměrná mzda (t+1)   | 0,81             |
| HDP (t) vs. Cena mléka (t+1)      | 0,52             |
| HDP (t) vs. Cena chleba (t+1)     | 0,47             |



**Analýza**

* **Korelace mezi HDP a průměrnými mzdami:**
    * **Současný rok (0,92):** Velmi vysoká a silně pozitivní korelace naznačuje, že mezi HDP a průměrnými mzdami existuje silná přímá úměra. S rostoucím HDP ve stejném roce obvykle výrazně rostou i mzdy.
    * **Následující rok (0,81):** I zde je korelace silná a pozitivní, byť mírně nižší než pro stejný rok. To znamená, že růst HDP v daném roce má stále silný, i když o něco menší, pozitivní vliv na růst mezd v roce následujícím. Mzdy tedy reagují na ekonomický růst jak okamžitě, tak s určitým zpožděním.

* **Korelace mezi HDP a cenou mléka:**
    * **Současný rok (0,64):** Středně silná pozitivní korelace. S růstem HDP mají tendenci růst i ceny mléka, ale vliv není tak silný jako u mezd.
    * **Následující rok (0,52):** Korelace je pozitivní, ale značně slabší než pro stejný rok a také slabší než u mezd. To naznačuje, že vliv HDP na cenu mléka v následujícím roce je méně výrazný.

* **Korelace mezi HDP a cenou chleba:**
    * **Současný rok (0,70):** Silnější pozitivní korelace než u mléka. S růstem HDP mají tendenci růst i ceny chleba ve stejném roce.
    * **Následující rok (0,47):** Korelace je pozitivní, ale poměrně slabá a podstatně nižší než pro stejný rok. To naznačuje, že HDP má spíše okamžitý vliv na cenu chleba než zpožděný dopad v následujícím roce.



**Závěr**

Výška HDP má zjevně **silný pozitivní vliv na změny ve mzdách a cenách potravin v České republice** v analyzovaném období. Nejsilnější korelace je pozorována mezi **HDP a průměrnými mzdami**, a to jak ve stejném roce (0,92), tak s menším zpožděním v roce následujícím (0,81). To jasně ukazuje, že ekonomický růst se přímo a významně promítá do zvýšení příjmů obyvatelstva.

Co se týče cen základních potravin, HDP je také spojeno s jejich růstem, nicméně korelace jsou slabší než u mezd, zejména s ročním zpožděním (mléko 0,52, chléb 0,47). To je běžné, protože ceny potravin jsou ovlivněny i mnoha dalšími faktory, jako jsou náklady na suroviny, sezónnost, globální trhy, logistika a marže obchodníků, které mohou utlumit nebo zpozdit přímý dopad HDP.

Celkově data podporují hypotézu, že ekonomický růst měřený HDP má pozitivní dopad na růst mezd a je spojen i s růstem cen vybraných základních potravin. Důležité je, že **vliv HDP na mzdy se jeví jako silnější a trvalejší než jeho vliv na ceny chleba a mléka**, což celkově naznačuje **zlepšení kupní síly obyvatelstva v kontextu ekonomického růstu**.
# Projekt SQL: Dostupnost potravin v ?R

## Autor
Matěj Lauterkranc

## Popis projektu
Tento projekt analyzuje dostupnost základních potravin (mléko, chléb) v České republice z pohledu průměrných mezd a cen, a to v několikaletém období. Dále se zkoumá vztah mezi HDP a ekonomickými ukazateli a vývojem cen a mezd.

## Datov� zdroje

Projekt využívá data z veřejně dostupné databáze Engeto Akademie (nebo jejích zrcadlených online verzí). Konkrétně se jedná o následující tabulky:

- `czechia_payroll`
- `czechia_payroll_calculation`
- `czechia_payroll_industry_branch`
- `czechia_payroll_unit`
- `czechia_payroll_value_type`
- `czechia_price`
- `czechia_price_category`
- `economies` mezinárodní ekonomická data (pravděpodobně z World Bank)

Tyto tabulky jsou součástí:
- buď veřejné SQL databáze zpřístupněné online v rámci kurzů Engeto,Add commentMore actions
- nebo je možné si stáhnout databázi ve formátu `.sql` z oficiálních materiálů kurzu a nahrát ji do vlastního databázového systému (např. PostgreSQL).

***Poznámka:** Je nutné mít přístup k těmto datům – bez nich projekt nebude fungovat. Pokud databázi nemáte, je třeba si ji stáhnout z oficiálního vzdělávacího rozhraní Engeto Akademie (viz jejich GitHub nebo studijní portál).

## Výstupní tabulky

### `t_matej_lauterkranc_project_sql_primary_final`
Obsahuje:Add commentMore actions
- Rok
- Průměrná mzda
- Průměrná cena mléka a chleba
- Kolik litrů mléka a kg chleba si lze koupit za mzdu

### `t_matej_lauterkranc_project_sql_secondary_final`
Obsahuje:
- Země (6 evropských států)
- Rok
- HDP na obyvatele
- GINI index
- Populace

## Výzkumné otázky a jak byly řešeny
1. **Vývoj mezd v jednotlivých odvětvích** – pomocí `GROUP BY` na odvětví a rok.
2. **Kupní síla na začátku a konci období** – porovnání prvního a posledního roku z primární tabulky.
3. **Nejpomalejší růst cen potravin** – výpočet průměrného meziročního procentuálního růstu u všech kategorií.
4. **Rok s výraznějším růstem cen než mezd (>10 %)** – porovnání meziročních růstů v jednotlivých letech.
5. **Vliv HDP na mzdy a ceny** – korelace mezi HDP a cenami/mzdami ve stejném a následujícím roce.

## Poznámky k datům
- V datech se vyskytují chybějící hodnoty, které byly ošetřeny pomocí `COALESCE` a `NULLIF`.
- Roky, které neměly data v obou zdrojích (mzdy i ceny), byly vynechány.

## Replikace projektu
1. Spusť SQL skript v databázovém prostředí.
2. Ověř si, že existují výše zmíněné zdrojové tabulky.
3. Výsledné tabulky `t_*_final` budou vytvořeny v databázi.


## Kontakt
Máte otázky? Kontaktujte mě na [LinkedIn](https://www.linkedin.com/in/mat%C4%9Bj-lauterkranc-8a9b7a228/) nebo přes e-mail: m.lauterkranc@gmail.com  
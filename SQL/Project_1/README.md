# Projekt SQL: Dostupnost potravin v ?R

## Autor
Mat?j Lauterkranc

## Popis projektu
Tento projekt analyzuje dostupnost základních potravin (mléko, chléb) v ?eské republice z pohledu pr?m?rných mezd a cen, a to v n?kolikaletém období. Dále se zkoumá vztah mezi HDP a ekonomickými ukazateli a vývojem cen a mezd.

## Datové zdroje

Projekt využívá data z ve?ejn? dostupné databáze Engeto Akademie (nebo jejích zrcadlených online verzí). Konkrétn? se jedná o následující tabulky:

- `czechia_payroll`
- `czechia_payroll_calculation`
- `czechia_payroll_industry_branch`
- `czechia_payroll_unit`
- `czechia_payroll_value_type`
- `czechia_price`
- `czechia_price_category`
- `economies` – mezinárodní ekonomická data (pravd?podobn? z World Bank)

Tyto tabulky jsou sou?ástí:
- bu? ve?ejné SQL databáze zp?ístupn?né online v rámci kurz? Engeto,
- nebo je možné si stáhnout databázi ve formátu `.sql` z oficiálních materiál? kurzu a nahrát ji do vlastního databázového systému (nap?. PostgreSQL).

**Poznámka:** Je nutné mít p?ístup k t?mto dat?m – bez nich projekt nebude fungovat. Pokud databázi nemáte, je t?eba si ji stáhnout z oficiálního vzd?lávacího rozhraní Engeto Akademie (viz jejich GitHub nebo studijní portál).

## Výstupní tabulky
### `t_matej_lauterkranc_project_sql_primary_final`
Obsahuje:
- Rok
- Pr?m?rná mzda
- Pr?m?rná cena mléka a chleba
- Kolik litr? mléka a kg chleba si lze koupit za mzdu

### `t_matej_lauterkranc_project_sql_secondary_final`
Obsahuje:
- Zem? (6 evropských stát?)
- Rok
- HDP na obyvatele
- GINI index
- Populace

## Výzkumné otázky a jak byly ?ešeny
1. **Vývoj mezd v jednotlivých odv?tvích** – pomocí `GROUP BY` na odv?tví a rok.
2. **Kupní síla na za?átku a konci období** – porovnání prvního a posledního roku z primární tabulky.
3. **Nejpomalejší r?st cen potravin** – výpo?et pr?m?rného meziro?ního procentuálního r?stu u všech kategorií.
4. **Rok s výrazn?jším r?stem cen než mezd (>10?%)** – porovnání meziro?ních r?st? v jednotlivých letech.
5. **Vliv HDP na mzdy a ceny** – korelace mezi HDP a cenami/mzdami ve stejném a následujícím roce.

## Poznámky k dat?m
- V datech se vyskytují chyb?jící hodnoty, které byly ošet?eny pomocí `COALESCE` a `NULLIF`.
- Roky, které nem?ly data v obou zdrojích (mzdy i ceny), byly vynechány.

## Replikace projektu
1. Spus? SQL skript v databázovém prost?edí.
2. Ov?? si, že existují výše zmín?né zdrojové tabulky.
3. Výsledné tabulky `t_*_final` budou vytvo?eny v databázi.



## Kontakt
Máte otázky? Kontaktujte m? na [LinkedIn](https://www.linkedin.com/in/mat%C4%9Bj-lauterkranc-8a9b7a228/) nebo p?es e-mail: m.lauterkranc@gmail.com  
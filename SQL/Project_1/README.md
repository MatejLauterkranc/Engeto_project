# Projekt SQL: Dostupnost potravin v ?R

## Autor
Matěj Lauterkranc

## Popis projektu
Tento projekt analyzuje dostupnost z�kladn�ch potravin (ml�ko, chl�b) v ?esk� republice z pohledu pr?m?rn�ch mezd a cen, a to v n?kolikalet�m obdob�. D�le se zkoum� vztah mezi HDP a ekonomick�mi ukazateli a v�vojem cen a mezd.

## Datov� zdroje

Projekt vyu��v� data z ve?ejn? dostupn� datab�ze Engeto Akademie (nebo jej�ch zrcadlen�ch online verz�). Konkr�tn? se jedn� o n�sleduj�c� tabulky:

- `czechia_payroll`
- `czechia_payroll_calculation`
- `czechia_payroll_industry_branch`
- `czechia_payroll_unit`
- `czechia_payroll_value_type`
- `czechia_price`
- `czechia_price_category`
- `economies` � mezin�rodn� ekonomick� data (pravd?podobn? z World Bank)

Tyto tabulky jsou sou?�st�:
- bu? ve?ejn� SQL datab�ze zp?�stupn?n� online v r�mci kurz? Engeto,
- nebo je mo�n� si st�hnout datab�zi ve form�tu `.sql` z ofici�ln�ch materi�l? kurzu a nahr�t ji do vlastn�ho datab�zov�ho syst�mu (nap?. PostgreSQL).

**Pozn�mka:** Je nutn� m�t p?�stup k t?mto dat?m � bez nich projekt nebude fungovat. Pokud datab�zi nem�te, je t?eba si ji st�hnout z ofici�ln�ho vzd?l�vac�ho rozhran� Engeto Akademie (viz jejich GitHub nebo studijn� port�l).

## V�stupn� tabulky
### `t_matej_lauterkranc_project_sql_primary_final`
Obsahuje:
- Rok
- Pr?m?rn� mzda
- Pr?m?rn� cena ml�ka a chleba
- Kolik litr? ml�ka a kg chleba si lze koupit za mzdu

### `t_matej_lauterkranc_project_sql_secondary_final`
Obsahuje:
- Zem? (6 evropsk�ch st�t?)
- Rok
- HDP na obyvatele
- GINI index
- Populace

## V�zkumn� ot�zky a jak byly ?e�eny
1. **V�voj mezd v jednotliv�ch odv?tv�ch** � pomoc� `GROUP BY` na odv?tv� a rok.
2. **Kupn� s�la na za?�tku a konci obdob�** � porovn�n� prvn�ho a posledn�ho roku z prim�rn� tabulky.
3. **Nejpomalej�� r?st cen potravin** � v�po?et pr?m?rn�ho meziro?n�ho procentu�ln�ho r?stu u v�ech kategori�.
4. **Rok s v�razn?j��m r?stem cen ne� mezd (>10?%)** � porovn�n� meziro?n�ch r?st? v jednotliv�ch letech.
5. **Vliv HDP na mzdy a ceny** � korelace mezi HDP a cenami/mzdami ve stejn�m a n�sleduj�c�m roce.

## Pozn�mky k dat?m
- V datech se vyskytuj� chyb?j�c� hodnoty, kter� byly o�et?eny pomoc� `COALESCE` a `NULLIF`.
- Roky, kter� nem?ly data v obou zdroj�ch (mzdy i ceny), byly vynech�ny.

## Replikace projektu
1. Spus? SQL skript v datab�zov�m prost?ed�.
2. Ov?? si, �e existuj� v��e zm�n?n� zdrojov� tabulky.
3. V�sledn� tabulky `t_*_final` budou vytvo?eny v datab�zi.



## Kontakt
M�te ot�zky? Kontaktujte m? na [LinkedIn](https://www.linkedin.com/in/mat%C4%9Bj-lauterkranc-8a9b7a228/) nebo p?es e-mail: m.lauterkranc@gmail.com  
-- ================================================
-- PROJECT: SQL analysis of food accessibility in CZ
-- AUTHOR: Matěj Lauterkranc
-- ================================================

-- Drop existing tables if they exist to ensure a clean run
DROP TABLE IF EXISTS t_matej_lauterkranc_project_sql_primary_final;
DROP TABLE IF EXISTS t_matej_lauterkranc_project_sql_secondary_final;

-- ================================================
-- Create PRIMARY final table: detailed wage, food prices and food affordability
-- This table is designed to answer all primary research questions.
-- ================================================
CREATE TABLE t_matej_lauterkranc_project_sql_primary_final AS
WITH
    wage_data AS (
        SELECT
            cp.payroll_year AS "year",
            cpib.name AS "industry_branch_name",
            ROUND(AVG(cp.value)::numeric, 2) AS "avg_wage_per_industry"
        FROM
            czechia_payroll cp
        JOIN
            czechia_payroll_value_type cpvt ON cp.value_type_code = cpvt.code
        JOIN
            czechia_payroll_industry_branch cpib ON cp.industry_branch_code = cpib.code
        WHERE
            cpvt.name = 'Průměrná hrubá mzda na zaměstnance' AND cp.value IS NOT NULL
        GROUP BY
            cp.payroll_year, cpib.name
    ),
    overall_avg_wage_data AS (
        SELECT
            payroll_year AS "year",
            ROUND(AVG(value)::numeric, 2) AS "overall_avg_wage"
        FROM
            czechia_payroll
        JOIN
            czechia_payroll_value_type ON czechia_payroll.value_type_code = czechia_payroll_value_type.code
        WHERE
            czechia_payroll_value_type.name = 'Průměrná hrubá mzda na zaměstnance' AND value IS NOT NULL
        GROUP BY
            payroll_year
    ),
    price_data AS (
        SELECT
            EXTRACT(YEAR FROM cp.date_from) AS "year",
            cpc.name AS "price_category_name",
            ROUND(AVG(cp.value)::numeric, 2) AS "avg_price_per_category"
        FROM
            czechia_price cp
        JOIN
            czechia_price_category cpc ON cp.category_code = cpc.code
        WHERE
            cp.value IS NOT NULL
        GROUP BY
            EXTRACT(YEAR FROM cp.date_from), cpc.name
    ),
    milk_bread_prices AS (
        SELECT
            EXTRACT(YEAR FROM cp.date_from) AS "year",
            AVG(CASE WHEN cpc.name ILIKE '%Mléko polotučné pasterované%' THEN cp.value END) AS "avg_price_milk",
            AVG(CASE WHEN cpc.name ILIKE '%Chléb konzumní kmínový%' THEN cp.value END) AS "avg_price_bread"
        FROM
            czechia_price cp
        JOIN
            czechia_price_category cpc ON cp.category_code = cpc.code
        WHERE
            cp.value IS NOT NULL
        GROUP BY
            EXTRACT(YEAR FROM cp.date_from)
    )
SELECT
    wd."year",
    wd.industry_branch_name,
    wd.avg_wage_per_industry,
    oawd.overall_avg_wage,
    pd.price_category_name,
    pd.avg_price_per_category,
    mbp.avg_price_milk,
    mbp.avg_price_bread,
    ROUND(COALESCE(oawd.overall_avg_wage / NULLIF(mbp.avg_price_milk, 0), 0)::numeric, 2) AS "milk_liters",
    ROUND(COALESCE(oawd.overall_avg_wage / NULLIF(mbp.avg_price_bread, 0), 0)::numeric, 2) AS "bread_kg"
FROM
    wage_data wd
LEFT JOIN
    overall_avg_wage_data oawd ON wd.year = oawd.year
LEFT JOIN
    price_data pd ON wd.year = pd.year
LEFT JOIN
    milk_bread_prices mbp ON wd.year = mbp.year
WHERE
    wd.year IN (SELECT DISTINCT "year" FROM overall_avg_wage_data)
    AND wd.year IN (SELECT DISTINCT "year" FROM milk_bread_prices)
ORDER BY
    wd."year", wd.industry_branch_name, pd.price_category_name;

-- ================================================
-- Create SECONDARY final table: economic indicators of selected countries
-- ================================================
CREATE TABLE t_matej_lauterkranc_project_sql_secondary_final AS
SELECT
    country,
    year,
    ROUND(gdp::numeric, 2) AS gdp_per_capita,
    ROUND(gini::numeric, 2) AS gini_index,
    ROUND(population) AS population
FROM
    economies
WHERE
    country IN ('Czech Republic', 'Germany', 'Austria', 'Poland', 'Slovakia', 'Hungary')
    AND year BETWEEN 2006 AND 2022
ORDER BY
    country, year;

-- ================================================
-- Show MAIN and SECONDARY table
-- ================================================

-- MAIN (first few rows to see structure, full table might be too big)
SELECT *
FROM t_matej_lauterkranc_project_sql_primary_final
LIMIT 100;

-- SECONDARY
SELECT *
FROM t_matej_lauterkranc_project_sql_secondary_final;

-- ================================================
-- Question 1: Wage trends across industries over the years
-- (Using t_matej_lauterkranc_project_sql_primary_final)
-- ================================================
SELECT
    industry_branch_name AS industry,
    "year",
    avg_wage_per_industry AS avg_wage
FROM
    t_matej_lauterkranc_project_sql_primary_final
WHERE
    industry_branch_name IS NOT NULL
GROUP BY
    industry_branch_name,
    "year",
    avg_wage_per_industry
ORDER BY
    industry_branch_name,
    "year";

-- ================================================
-- Question 2: Food affordability in first and last year
-- (Using t_matej_lauterkranc_project_sql_primary_final)
-- ================================================
SELECT
    "year",
    overall_avg_wage,
    avg_price_milk,
    avg_price_bread,
    milk_liters,
    bread_kg
FROM
    t_matej_lauterkranc_project_sql_primary_final
WHERE
    "year" IN (
        (SELECT MIN("year") FROM t_matej_lauterkranc_project_sql_primary_final),
        (SELECT MAX("year") FROM t_matej_lauterkranc_project_sql_primary_final)
    )
GROUP BY
    "year",
    overall_avg_wage,
    avg_price_milk,
    avg_price_bread,
    milk_liters,
    bread_kg
ORDER BY
    "year";

-- ================================================
-- Question 3: Slowest price growth among food categories
-- (Using t_matej_lauterkranc_project_sql_primary_final)
-- ================================================
WITH
    yearly_avg_prices AS (
        SELECT
            price_category_name AS category,
            "year",
            avg_price_per_category AS avg_price
        FROM
            t_matej_lauterkranc_project_sql_primary_final
        WHERE
            price_category_name IS NOT NULL
        GROUP BY
            price_category_name,
            "year",
            avg_price_per_category
    ),
    price_changes AS (
        SELECT
            category,
            "year",
            avg_price,
            LAG(avg_price) OVER (PARTITION BY category ORDER BY "year") AS prev_price
        FROM
            yearly_avg_prices
    ),
    growth_rates AS (
        SELECT
            category,
            "year",
            ROUND(100.0 * ((avg_price - prev_price) / prev_price)::numeric, 2) AS growth_pct
        FROM
            price_changes
        WHERE
            prev_price IS NOT NULL AND prev_price != 0
    ),
    avg_growth AS (
        SELECT
            category,
            ROUND(AVG(growth_pct)::numeric, 2) AS avg_yearly_growth_pct
        FROM
            growth_rates
        GROUP BY
            category
    )
SELECT
    *
FROM
    avg_growth
ORDER BY
    avg_yearly_growth_pct ASC
LIMIT 10;

-- ================================================
-- Question 4: Year where price growth exceeds wage growth by >10%
-- (Using t_matej_lauterkranc_project_sql_primary_final)
-- ================================================
WITH
    yearly_averages AS (
        SELECT DISTINCT
            "year",
            overall_avg_wage AS avg_wage,
            avg_price_milk AS avg_milk_price,
            avg_price_bread AS avg_bread_price
        FROM
            t_matej_lauterkranc_project_sql_primary_final
        WHERE
            overall_avg_wage IS NOT NULL
            AND avg_price_milk IS NOT NULL
            AND avg_price_bread IS NOT NULL
    ),
    changes AS (
        SELECT
            "year",
            avg_wage,
            avg_milk_price,
            avg_bread_price,
            LAG(avg_wage) OVER (ORDER BY "year") AS prev_wage,
            LAG(avg_milk_price) OVER (ORDER BY "year") AS prev_milk,
            LAG(avg_bread_price) OVER (ORDER BY "year") AS prev_bread
        FROM
            yearly_averages
    )
SELECT
    "year",
    ROUND(100 * ((avg_wage - prev_wage) / NULLIF(prev_wage, 0))::numeric, 2) AS wage_growth_pct,
    ROUND(100 * ((avg_milk_price - prev_milk) / NULLIF(prev_milk, 0))::numeric, 2) AS milk_growth_pct,
    ROUND(100 * ((avg_bread_price - prev_bread) / NULLIF(prev_bread, 0))::numeric, 2) AS bread_growth_pct,
    (ROUND(100 * ((avg_milk_price - prev_milk) / NULLIF(prev_milk, 0))::numeric, 2) - ROUND(100 * ((avg_wage - prev_wage) / NULLIF(prev_wage, 0))::numeric, 2)) AS milk_price_wage_diff_pct,
    (ROUND(100 * ((avg_bread_price - prev_bread) / NULLIF(prev_bread, 0))::numeric, 2) - ROUND(100 * ((avg_wage - prev_wage) / NULLIF(prev_wage, 0))::numeric, 2)) AS bread_price_wage_diff_pct
FROM
    changes
WHERE
    prev_wage IS NOT NULL
    AND prev_milk IS NOT NULL
    AND prev_bread IS NOT NULL
    AND (
        ((avg_milk_price - prev_milk) / NULLIF(prev_milk, 0) * 100) > ((avg_wage - prev_wage) / NULLIF(prev_wage, 0) * 100) + 10
        OR
        ((avg_bread_price - prev_bread) / NULLIF(prev_bread, 0) * 100) > ((avg_wage - prev_wage) / NULLIF(prev_wage, 0) * 100) + 10
    )
ORDER BY
    "year";

-- ================================================
-- Question 5: Correlation between GDP and prices/wages
-- (Using t_matej_lauterkranc_project_sql_primary_final and t_matej_lauterkranc_project_sql_secondary_final)
-- ================================================
WITH
    joined_data AS (
        SELECT DISTINCT
            spf."year",
            ssf.gdp_per_capita,
            spf.overall_avg_wage,
            spf.avg_price_milk,
            spf.avg_price_bread
        FROM
            t_matej_lauterkranc_project_sql_primary_final spf
        JOIN
            t_matej_lauterkranc_project_sql_secondary_final ssf ON spf."year" = ssf.year
        WHERE
            ssf.country = 'Czech Republic'
            AND spf.overall_avg_wage IS NOT NULL
            AND spf.avg_price_milk IS NOT NULL
            AND spf.avg_price_bread IS NOT NULL
            AND ssf.gdp_per_capita IS NOT NULL
    )
SELECT
    CORR(gdp_per_capita, overall_avg_wage) AS corr_gdp_wage,
    CORR(gdp_per_capita, avg_price_milk) AS corr_gdp_milk,
    CORR(gdp_per_capita, avg_price_bread) AS corr_gdp_bread
FROM
    joined_data;

-- ================================================
-- Optional (for Question 5): GDP effect one year ahead
-- (Using t_matej_lauterkranc_project_sql_primary_final and t_matej_lauterkranc_project_sql_secondary_final)
-- ================================================

WITH
    joined_data AS (
        SELECT DISTINCT
            spf."year",
            ssf.gdp_per_capita,
            spf.overall_avg_wage,
            spf.avg_price_milk,
            spf.avg_price_bread
        FROM
            t_matej_lauterkranc_project_sql_primary_final spf
        JOIN
            t_matej_lauterkranc_project_sql_secondary_final ssf ON spf."year" = ssf.year
        WHERE
            ssf.country = 'Czech Republic'
            AND spf.overall_avg_wage IS NOT NULL
            AND spf.avg_price_milk IS NOT NULL
            AND spf.avg_price_bread IS NOT NULL
            AND ssf.gdp_per_capita IS NOT NULL
    ),
    -- New CTE to calculate next_year_gdp
    data_with_next_gdp AS (
        SELECT
            "year",
            overall_avg_wage,
            avg_price_milk,
            avg_price_bread,
            LEAD(gdp_per_capita) OVER (ORDER BY "year") AS next_year_gdp -- LEAD is now in a separate CTE
        FROM
            joined_data
    )
SELECT
    CORR(next_year_gdp, overall_avg_wage) AS corr_next_gdp_wage,
    CORR(next_year_gdp, avg_price_milk) AS corr_next_gdp_milk,
    CORR(next_year_gdp, avg_price_bread) AS corr_next_gdp_bread
FROM
    data_with_next_gdp
WHERE
    next_year_gdp IS NOT NULL; -- Filter out NULL values from LEAD, as there's no "next_year_gdp" for the last year
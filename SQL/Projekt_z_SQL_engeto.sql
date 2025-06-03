-- ================================================
-- PROJECT: SQL analysis of food accessibility in CZ
-- AUTHOR: Matěj Lauterkranc
-- ================================================

-- Preview basic structure of payroll data
SELECT * 
FROM czechia_payroll;

-- Preview price data and category details
SELECT * FROM czechia_price;
SELECT * FROM czechia_price_category;

-- Preview all value types to filter correct wage indicator
SELECT DISTINCT name 
FROM czechia_payroll_value_type;

-- Find years with wage data but missing price data
SELECT DISTINCT payroll_year
FROM czechia_payroll p
JOIN czechia_payroll_value_type vt ON p.value_type_code = vt.code
WHERE vt.name = 'Průměrná hrubá mzda na zaměstnance'
  AND payroll_year NOT IN (
    SELECT DISTINCT EXTRACT(YEAR FROM date_from)
    FROM czechia_price
  );

-- Find years with price data but missing wage data
SELECT DISTINCT EXTRACT(YEAR FROM date_from)
FROM czechia_price
WHERE EXTRACT(YEAR FROM date_from) NOT IN (
  SELECT DISTINCT payroll_year
  FROM czechia_payroll p
  JOIN czechia_payroll_value_type vt ON p.value_type_code = vt.code
  WHERE vt.name = 'Průměrná hrubá mzda na zaměstnance'
);

-- Calculate yearly average prices for milk and bread
SELECT 
  EXTRACT(YEAR FROM p.date_from) AS year,
  AVG(CASE WHEN pc.name ILIKE '%Mléko polotučné pasterované%' THEN p.value END) AS avg_price_milk,
  AVG(CASE WHEN pc.name ILIKE '%Chléb konzumní kmínový%' THEN p.value END) AS avg_price_bread
FROM czechia_price p
JOIN czechia_price_category pc ON p.category_code = pc.code
WHERE p.value IS NOT NULL
GROUP BY EXTRACT(YEAR FROM p.date_from)
ORDER BY year;

-- ================================================
-- Create PRIMARY final table: avg wage, food prices and food affordability
-- ================================================
CREATE TABLE t_matej_lauterkranc_project_sql_primary_final AS
WITH
wages AS (
  SELECT 
    payroll_year AS year,
    AVG(p.value) AS avg_wage
  FROM czechia_payroll p
  JOIN czechia_payroll_value_type vt ON p.value_type_code = vt.code
  WHERE vt.name = 'Průměrná hrubá mzda na zaměstnance'
    AND p.value IS NOT NULL
  GROUP BY payroll_year
),
prices AS (
  SELECT 
    EXTRACT(YEAR FROM p.date_from) AS year,
    AVG(CASE WHEN pc.name ILIKE '%Mléko polotučné pasterované%' THEN p.value END) AS avg_price_milk,
    AVG(CASE WHEN pc.name ILIKE '%Chléb konzumní kmínový%' THEN p.value END) AS avg_price_bread
  FROM czechia_price p
  JOIN czechia_price_category pc ON p.category_code = pc.code
  WHERE p.value IS NOT NULL
  GROUP BY EXTRACT(YEAR FROM p.date_from)
)
SELECT 
  w.year,
  w.avg_wage,
  p.avg_price_milk,
  p.avg_price_bread,
  ROUND(COALESCE(w.avg_wage / NULLIF(p.avg_price_milk, 0), 0)::numeric, 2) AS milk_liters,
  ROUND(COALESCE(w.avg_wage / NULLIF(p.avg_price_bread, 0), 0)::numeric, 2) AS bread_kg
FROM wages w
JOIN prices p ON w.year = p.year
ORDER BY w.year;

-- ================================================
-- Create SECONDARY final table: economic indicators of selected countries
-- ================================================
CREATE TABLE t_matej_lauterkranc_project_sql_secondary_final AS
SELECT 
    country,
    year,
    ROUND((gdp)::numeric, 2) AS gdp_per_capita,
    ROUND((gini)::numeric, 2) AS gini_index,
    ROUND(population) AS population
FROM economies
WHERE country IN ('Czech Republic', 'Germany', 'Austria', 'Poland', 'Slovakia', 'Hungary')
  AND year BETWEEN 2006 AND 2022
ORDER BY country, year;

-- ================================================
-- Show MAIN and SECONDARY table 
-- ================================================

-- MAIN
SELECT * 
FROM t_matej_lauterkranc_project_sql_primary_final;

-- SECONDARY
SELECT * 
FROM t_matej_lauterkranc_project_sql_secondary_final;

-- ================================================
-- Question 1: Wage trends across industries over the years
-- ================================================
SELECT 
  ib.name AS industry,
  p.payroll_year AS year,
  ROUND(AVG(p.value)::numeric, 2) AS avg_wage
FROM czechia_payroll p
JOIN czechia_payroll_value_type vt ON p.value_type_code = vt.code
JOIN czechia_payroll_industry_branch ib ON p.industry_branch_code = ib.code
WHERE vt.name = 'Průměrná hrubá mzda na zaměstnance'
  AND p.value IS NOT NULL
GROUP BY ib.name, p.payroll_year
ORDER BY ib.name, p.payroll_year;

-- ================================================
-- Question 2: Food affordability in first and last year
-- ================================================
SELECT *
FROM t_matej_lauterkranc_project_sql_primary_final
WHERE year IN (
  (SELECT MIN(year) FROM t_matej_lauterkranc_project_sql_primary_final),
  (SELECT MAX(year) FROM t_matej_lauterkranc_project_sql_primary_final)
)
ORDER BY year;

-- ================================================
-- Question 3: Slowest price growth among food categories
-- ================================================
WITH yearly_avg_prices AS (
  SELECT 
    pc.name AS category,
    EXTRACT(YEAR FROM p.date_from) AS year,
    AVG(p.value) AS avg_price
  FROM czechia_price p
  JOIN czechia_price_category pc ON p.category_code = pc.code
  WHERE p.value IS NOT NULL
  GROUP BY pc.name, EXTRACT(YEAR FROM p.date_from)
),
price_changes AS (
  SELECT 
    category,
    year,
    avg_price,
    LAG(avg_price) OVER (PARTITION BY category ORDER BY year) AS prev_price
  FROM yearly_avg_prices
),
growth_rates AS (
  SELECT 
    category,
    year,
    ROUND(100.0 * ((avg_price - prev_price) / prev_price)::numeric, 2) AS growth_pct
  FROM price_changes
  WHERE prev_price IS NOT NULL
),
avg_growth AS (
  SELECT 
    category,
    ROUND(AVG(growth_pct)::numeric, 2) AS avg_yearly_growth_pct
  FROM growth_rates
  GROUP BY category
)
SELECT *
FROM avg_growth
ORDER BY avg_yearly_growth_pct ASC
LIMIT 10;

-- ================================================
-- Question 4: Year where price growth exceeds wage growth by >10%
-- ================================================
WITH changes AS (
  SELECT 
    year,
    avg_wage,
    avg_price_milk,
    avg_price_bread,
    LAG(avg_wage) OVER (ORDER BY year) AS prev_wage,
    LAG(avg_price_milk) OVER (ORDER BY year) AS prev_milk,
    LAG(avg_price_bread) OVER (ORDER BY year) AS prev_bread
  FROM t_matej_lauterkranc_project_sql_primary_final
)
SELECT 
  year,
  ROUND(100 * ((avg_wage - prev_wage) / prev_wage)::numeric, 2) AS wage_growth_pct,
  ROUND(100 * ((avg_price_milk - prev_milk) / prev_milk)::numeric, 2) AS milk_growth_pct,
  ROUND(100 * ((avg_price_bread - prev_bread) / prev_bread)::numeric, 2) AS bread_growth_pct
FROM changes
WHERE prev_wage IS NOT NULL
  AND (
    (avg_price_milk - prev_milk) / prev_milk > 0.10 
    OR (avg_price_bread - prev_bread) / prev_bread > 0.10
  );

-- ================================================
-- Question 5: Correlation between GDP and prices/wages
-- ================================================
WITH joined AS (
  SELECT 
    s.year,
    s.gdp_per_capita,
    p.avg_wage,
    p.avg_price_milk,
    p.avg_price_bread
  FROM t_matej_lauterkranc_project_sql_secondary_final s
  JOIN t_matej_lauterkranc_project_sql_primary_final p ON s.year = p.year
  WHERE s.country = 'Czech Republic'
)
SELECT 
  CORR(gdp_per_capita, avg_wage) AS corr_gdp_wage,
  CORR(gdp_per_capita, avg_price_milk) AS corr_gdp_milk,
  CORR(gdp_per_capita, avg_price_bread) AS corr_gdp_bread
FROM joined;

-- ================================================
-- Optional (for Question 5): GDP effect one year ahead
-- ================================================

WITH joined AS (
  SELECT 
    s.year,
    LEAD(s.gdp_per_capita) OVER (ORDER BY s.year) AS next_year_gdp,
    p.avg_wage,
    p.avg_price_milk,
    p.avg_price_bread
  FROM t_matej_lauterkranc_project_sql_secondary_final s
  JOIN t_matej_lauterkranc_project_sql_primary_final p ON s.year = p.year
  WHERE s.country = 'Czech Republic'
)
SELECT 
  CORR(next_year_gdp, avg_wage) AS corr_next_gdp_wage,
  CORR(next_year_gdp, avg_price_milk) AS corr_next_gdp_milk,
  CORR(next_year_gdp, avg_price_bread) AS corr_next_gdp_bread
FROM joined
WHERE next_year_gdp IS NOT NULL;

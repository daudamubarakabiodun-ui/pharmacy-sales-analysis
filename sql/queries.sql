-- Same analysis in SQL (load data/sales.csv into a table called sales)

-- 1. Monthly revenue and profit
SELECT strftime('%Y-%m', date) AS month,
       SUM(quantity * unit_price)               AS revenue,
       SUM(quantity * (unit_price - unit_cost)) AS profit
FROM sales
GROUP BY month ORDER BY month;

-- 2. Top 10 products by revenue
SELECT product, SUM(quantity * unit_price) AS revenue
FROM sales GROUP BY product ORDER BY revenue DESC LIMIT 10;

-- 3. ABC classification using cumulative revenue share
WITH r AS (
  SELECT product, SUM(quantity * unit_price) AS revenue FROM sales GROUP BY product
), c AS (
  SELECT product, revenue,
         SUM(revenue) OVER (ORDER BY revenue DESC) * 1.0 / SUM(revenue) OVER () AS cum_share
  FROM r
)
SELECT product, revenue, ROUND(cum_share, 3) AS cum_share,
       CASE WHEN cum_share <= 0.80 THEN 'A' WHEN cum_share <= 0.95 THEN 'B' ELSE 'C' END AS abc_class
FROM c ORDER BY revenue DESC;

-- 4. Margin by category
SELECT category,
       ROUND(SUM(quantity * (unit_price - unit_cost)) * 1.0 / SUM(quantity * unit_price), 3) AS margin
FROM sales GROUP BY category ORDER BY margin DESC;

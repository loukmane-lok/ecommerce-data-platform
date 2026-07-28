-- Customer repeat purchase rate
-- Business question: what % of customers are repeat buyers vs one-time buyers,
-- and how much revenue does each group represent?
-- Uses a CTE to first compute per-customer order counts, then classify.

WITH customer_orders AS (
    SELECT
        user_id,
        COUNT(*)         AS order_count,
        SUM(order_value) AS customer_revenue
    FROM ecommerce_db.orders_curated
    GROUP BY user_id
)
SELECT
    CASE WHEN order_count > 1 THEN 'repeat' ELSE 'one_time' END AS customer_type,
    COUNT(*)                AS customer_count,
    SUM(customer_revenue)   AS total_revenue,
    AVG(customer_revenue)   AS avg_revenue_per_customer
FROM customer_orders
GROUP BY CASE WHEN order_count > 1 THEN 'repeat' ELSE 'one_time' END
ORDER BY total_revenue DESC;
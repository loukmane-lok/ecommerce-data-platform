-- Top 10 products by revenue, last 7 days
-- Business question: which products generated the most revenue recently?
-- order_date is a partition key, so this filter prunes folders before scanning
-- (cheap), unlike filtering on a non-partition column like price or product_id.

SELECT
    product_id,
    SUM(order_value) AS total_revenue,
    COUNT(*)         AS order_count
FROM ecommerce_db.orders_curated
WHERE order_date >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY product_id
ORDER BY total_revenue DESC
LIMIT 10;
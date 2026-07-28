-- Daily revenue by product category
-- Business question: what is total revenue per category, per day?
-- Used to spot category-level trends and inform merchandising decisions.
-- Partition-aware: filters/groups on order_date and category (our partition keys),
-- so Athena skips non-matching partitions entirely instead of scanning all data.

SELECT
    order_date,
    category,
    COUNT(*)              AS order_count,
    SUM(order_value)       AS total_revenue,
    AVG(order_value)       AS avg_order_value
FROM ecommerce_db.orders_curated
GROUP BY order_date, category
ORDER BY order_date DESC, total_revenue DESC;
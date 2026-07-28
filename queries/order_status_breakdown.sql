-- Order status breakdown
-- Business question: what % of orders are completed vs cancelled vs refunded?
-- Uses a window function (SUM() OVER ()) to get the grand total alongside
-- each row, so we can compute percentage without a second query or self-join.

SELECT
    status,
    COUNT(*) AS order_count,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS pct_of_total
FROM ecommerce_db.orders_curated
GROUP BY status
ORDER BY order_count DESC;

-- ============================================================
-- DATACO SUPPLY CHAIN ANALYTICS
-- Improved SQL Business Analysis
-- Database: MySQL 8.0+
-- ============================================================


-- ============================================================
-- 1. DATABASE SETUP
-- ============================================================

CREATE DATABASE IF NOT EXISTS dataco_supply_chain;

USE dataco_supply_chain;


-- ============================================================
-- 2. DATASET OVERVIEW
-- ============================================================

SELECT
    COUNT(*) AS Total_Order_Items,
    COUNT(DISTINCT `Order Id`) AS Total_Orders,
    COUNT(DISTINCT `Customer Id`) AS Unique_Customers,
    COUNT(DISTINCT `Product Card Id`) AS Unique_Products,
    COUNT(DISTINCT `Market`) AS Total_Markets
FROM `datacosupplychain_clean_sql`;


-- ============================================================
-- 3. DATA QUALITY VALIDATION
-- ============================================================

-- Check duplicate order-item IDs

SELECT
    `Order Item Id`,
    COUNT(*) AS Duplicate_Count
FROM `datacosupplychain_clean_sql`
GROUP BY `Order Item Id`
HAVING COUNT(*) > 1;


-- Check missing values in important columns

SELECT
    SUM(`Order Id` IS NULL) AS Missing_Order_ID,
    SUM(`Customer Id` IS NULL) AS Missing_Customer_ID,
    SUM(`Sales` IS NULL) AS Missing_Sales,
    SUM(`Order Item Total` IS NULL) AS Missing_Item_Total,
    SUM(`Order Profit Per Order` IS NULL) AS Missing_Profit
FROM `datacosupplychain_clean_sql`;


-- Check whether order-level attributes are consistent

SELECT
    `Order Id`,
    COUNT(DISTINCT `Customer Id`) AS Customer_Count,
    COUNT(DISTINCT `Shipping Mode`) AS Shipping_Mode_Count,
    COUNT(DISTINCT `Delivery Status`) AS Delivery_Status_Count,
    COUNT(DISTINCT `Late_delivery_risk`) AS Risk_Flag_Count
FROM `datacosupplychain_clean_sql`
GROUP BY `Order Id`
HAVING
    Customer_Count > 1
    OR Shipping_Mode_Count > 1
    OR Delivery_Status_Count > 1
    OR Risk_Flag_Count > 1;


-- ============================================================
-- 4. SHIPPING PERFORMANCE ANALYSIS
-- ============================================================

-- Aggregate to one record per order before calculating
-- order counts and delivery performance.

WITH order_level AS (
    SELECT
        `Order Id`,
        MAX(`Shipping Mode`) AS Shipping_Mode,
        MAX(`Delivery Status`) AS Delivery_Status,
        MAX(`Late_delivery_risk`) AS Late_Risk
    FROM `datacosupplychain_clean_sql`
    GROUP BY `Order Id`
)

SELECT
    Shipping_Mode,
    COUNT(*) AS Total_Orders,

    SUM(
        CASE
            WHEN Delivery_Status = 'Late delivery' THEN 1
            ELSE 0
        END
    ) AS Actual_Late_Orders,

    SUM(
        CASE
            WHEN Late_Risk = 1 THEN 1
            ELSE 0
        END
    ) AS Risk_Flagged_Orders,

    ROUND(
        100.0 * SUM(
            CASE
                WHEN Delivery_Status = 'Late delivery' THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS Late_Delivery_Percentage

FROM order_level
GROUP BY Shipping_Mode
ORDER BY Late_Delivery_Percentage DESC;


-- ============================================================
-- 5. MARKET PERFORMANCE ANALYSIS
-- ============================================================

SELECT
    `Market`,

    COUNT(DISTINCT `Order Id`) AS Total_Orders,

    ROUND(SUM(`Sales`), 2) AS Gross_Sales,

    ROUND(SUM(`Order Item Total`), 2) AS Discount_Adjusted_Sales,

    ROUND(SUM(`Order Profit Per Order`), 2) AS Total_Profit,

    ROUND(
        SUM(`Order Profit Per Order`)
        / NULLIF(SUM(`Order Item Total`), 0) * 100,
        2
    ) AS Profit_Margin_Percentage

FROM `datacosupplychain_clean_sql`
GROUP BY `Market`
ORDER BY Total_Profit DESC;


-- ============================================================
-- 6. CATEGORY PROFITABILITY ANALYSIS
-- ============================================================

SELECT
    `Category Name`,

    COUNT(*) AS Total_Order_Items,

    COUNT(DISTINCT `Order Id`) AS Total_Orders,

    ROUND(SUM(`Order Item Total`), 2) AS Discount_Adjusted_Sales,

    ROUND(SUM(`Order Profit Per Order`), 2) AS Total_Profit,

    ROUND(AVG(`Order Profit Per Order`), 2) AS Average_Item_Profit

FROM `datacosupplychain_clean_sql`
GROUP BY `Category Name`
HAVING SUM(`Order Profit Per Order`) < 0
ORDER BY Total_Profit ASC;


-- ============================================================
-- 7. TOP 10 CUSTOMERS BY DISCOUNT-ADJUSTED SALES
-- ============================================================

SELECT
    `Customer Id`,

    MAX(`Customer Fname`) AS Customer_First_Name,

    ROUND(SUM(`Order Item Total`), 2) AS Total_Discount_Adjusted_Sales,

    ROUND(SUM(`Order Profit Per Order`), 2) AS Total_Profit,

    COUNT(DISTINCT `Order Id`) AS Total_Orders

FROM `datacosupplychain_clean_sql`
GROUP BY `Customer Id`
ORDER BY Total_Discount_Adjusted_Sales DESC
LIMIT 10;


-- ============================================================
-- 8. MONTHLY PROFITABILITY ANALYSIS
-- ============================================================

SELECT
    YEAR(`order date (DateOrders)`) AS Order_Year,

    MONTH(`order date (DateOrders)`) AS Order_Month,

    COUNT(DISTINCT `Order Id`) AS Total_Orders,

    ROUND(SUM(`Sales`), 2) AS Gross_Sales,

    ROUND(SUM(`Order Item Total`), 2) AS Discount_Adjusted_Sales,

    ROUND(SUM(`Order Profit Per Order`), 2) AS Monthly_Profit

FROM `datacosupplychain_clean_sql`

GROUP BY
    YEAR(`order date (DateOrders)`),
    MONTH(`order date (DateOrders)`)

ORDER BY
    Order_Year,
    Order_Month;


-- ============================================================
-- 9. DELIVERY STATUS ANALYSIS
-- ============================================================

SELECT
    `Delivery Status`,

    COUNT(DISTINCT `Order Id`) AS Total_Orders,

    ROUND(
        COUNT(DISTINCT `Order Id`) * 100.0 /
        (
            SELECT COUNT(DISTINCT `Order Id`)
            FROM `datacosupplychain_clean_sql`
        ),
        2
    ) AS Order_Percentage

FROM `datacosupplychain_clean_sql`
GROUP BY `Delivery Status`
ORDER BY Total_Orders DESC;


-- ============================================================
-- 10. OVERALL BUSINESS PERFORMANCE
-- ============================================================

SELECT
    COUNT(DISTINCT `Order Id`) AS Total_Orders,

    COUNT(DISTINCT `Customer Id`) AS Unique_Customers,

    ROUND(SUM(`Sales`), 2) AS Gross_Sales,

    ROUND(SUM(`Order Item Discount`), 2) AS Total_Discount,

    ROUND(SUM(`Order Item Total`), 2) AS Discount_Adjusted_Sales,

    ROUND(SUM(`Order Profit Per Order`), 2) AS Total_Profit,

    ROUND(
        SUM(`Order Profit Per Order`)
        / NULLIF(SUM(`Order Item Total`), 0) * 100,
        2
    ) AS Overall_Profit_Margin

FROM `datacosupplychain_clean_sql`;


-- ============================================================
-- END OF SQL ANALYSIS
-- ============================================================

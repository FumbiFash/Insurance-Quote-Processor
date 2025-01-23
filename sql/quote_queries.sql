-- 1. Conversion rates by product type and age bracket
WITH age_brackets AS (
  SELECT quote_reference,
         product_type,
         CASE 
           WHEN customer_age < 25 THEN '18-24'
           WHEN customer_age BETWEEN 25 AND 34 THEN '25-34'
           WHEN customer_age BETWEEN 35 AND 44 THEN '35-44'
           WHEN customer_age BETWEEN 45 AND 54 THEN '45-54'
           ELSE '55+'
         END AS age_bracket,
         conversion_status
  FROM quotes
)
SELECT 
  product_type,
  age_bracket,
  COUNT(*) as total_quotes,
  SUM(CASE WHEN conversion_status = 'ACCEPTED' THEN 1 ELSE 0 END) as accepted_quotes,
  ROUND(100.0 * SUM(CASE WHEN conversion_status = 'ACCEPTED' THEN 1 ELSE 0 END) / COUNT(*), 2) as conversion_rate
FROM age_brackets
GROUP BY product_type, age_bracket
ORDER BY product_type, age_bracket;

-- 2. Find the top 3 postcodes by quote volume

SELECT 
  risk_postcode,
  COUNT(*) as quote_count
FROM quotes
GROUP BY risk_postcode
ORDER BY quote_count DESC
LIMIT 3;

-- 3. Average premium by product type and payment method 
SELECT 
  product_type,
  payment_type,
  ROUND(AVG(quote_premium), 2) as avg_premium,
  COUNT(*) as quote_count
FROM quotes
GROUP BY product_type, payment_type
ORDER BY product_type, payment_type;

-- 4. Potential fraud patterns
WITH duplicate_quotes AS (
  SELECT 
    risk_postcode,
    DATE(timestamp) as quote_date,
    COUNT(*) as daily_quotes
  FROM quotes
  GROUP BY risk_postcode, DATE(timestamp)
  HAVING COUNT(*) > 2
)
SELECT 
  risk_postcode,
  quote_date,
  daily_quotes
FROM duplicate_quotes
ORDER BY daily_quotes DESC, quote_date;

-- 5. Broker commission report

SELECT 
  product_type,
  COUNT(*) as total_quotes,
  ROUND(SUM(broker_commission), 2) as total_commission,
  ROUND(AVG(broker_commission), 2) as avg_commission,
  ROUND(MIN(broker_commission), 2) as min_commission,
  ROUND(MAX(broker_commission), 2) as max_commission
FROM quotes
GROUP BY product_type
ORDER BY total_commission DESC;
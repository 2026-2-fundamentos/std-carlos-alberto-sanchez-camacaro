CREATE MACRO money_text(s) AS regexp_replace(upper(s), '\s+|COP|\$', '', 'g');
CREATE MACRO compact_money(s) AS replace(rtrim(money_text(s), 'K'), ',', '');
CREATE MACRO money(s) AS
    TRY_CAST(
        CASE WHEN regexp_matches(compact_money(s), '\.[0-9]{2}$')
            THEN replace(left(compact_money(s), -3), '.', '') || right(compact_money(s), 3)
            ELSE replace(compact_money(s), '.', '') END AS DOUBLE
    ) * CASE WHEN ends_with(money_text(s), 'K') THEN 1000 ELSE 1 END;

WITH source AS (
    SELECT row_number() OVER () AS pos,
           trim("Supplier ID") AS supplier_id,
           regexp_replace(trim(supplier), '\s+', ' ', 'g') AS supplier,
           upper(trim(country)) AS country,
           lower(strip_accents(trim(city))) AS city,
           trim("Purchase Date") AS purchase_date,
           money(amount) AS amount,
           TRY_CAST(rtrim(trim(discount), '%') AS DOUBLE) AS rate,
           ends_with(trim(discount), '%') AS percent,
           replace(lower(trim(weight)), ',', '.') AS weight,
           TRY_CAST(trim(units) AS INTEGER) AS units,
           money("Unit Price") AS unit_price,
           lower(trim("Contact Email")) AS contact_email
    FROM raw_sales
), normalized AS (
    SELECT pos, supplier_id, supplier,
           CASE WHEN country IN ('CO', 'COL', 'COLOMBIA') THEN 'COL' ELSE country END AS country,
           CASE city WHEN 'bogota' THEN 'Bogotá' WHEN 'medellin' THEN 'Medellín'
                WHEN 'sopo' THEN 'Sopó' WHEN 'tenjo' THEN 'Tenjo' END AS city,
           CAST(CASE WHEN regexp_matches(purchase_date, '^[0-9]{2}-') THEN try_strptime(purchase_date, '%d-%m-%y') ELSE try_strptime(purchase_date, ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y',
                     '%m/%d/%Y', '%d.%m.%Y']) END AS DATE) AS purchase_date,
           amount, CASE WHEN percent OR rate > 1 THEN rate / 100 ELSE rate END AS discount,
           TRY_CAST(regexp_extract(weight, '^(-?[0-9]+(?:\.[0-9]+)?)\s*(kg|g|ton)?$', 1) AS DOUBLE)
               * CASE WHEN ends_with(weight, 'ton') THEN 1000
                      WHEN ends_with(weight, 'kg') THEN 1
                      WHEN ends_with(weight, 'g') THEN 0.001 ELSE 1 END AS weight,
           units, CASE WHEN unit_price >= 0 THEN unit_price END AS unit_price,
           nullif(contact_email, 'sin correo') AS contact_email
    FROM source
), valid_ranges AS (
    SELECT * REPLACE (
        CASE WHEN discount BETWEEN 0 AND 1 THEN discount END AS discount,
        CASE WHEN weight >= 0 THEN weight END AS weight
    )
    FROM normalized
)
SELECT * EXCLUDE (pos)
FROM valid_ranges
QUALIFY row_number() OVER (
    PARTITION BY supplier_id, lower(supplier), country, city, purchase_date,
                 amount, discount, weight, units, unit_price, contact_email
    ORDER BY pos
) = 1
ORDER BY pos;

WITH profiles AS (
    SELECT row_number() OVER () AS pos, loyalty_card_number, annual_spend,
           (TRY_CAST(age AS INTEGER) // 10) * 10 AS decade,
           CASE
               WHEN city IN ('Barranquilla', 'Cartagena') THEN 'Caribe'
               WHEN city = 'Cali' THEN 'Pacífica'
               WHEN city IN ('Bello', 'Bogotá', 'Bucaramanga', 'Envigado', 'Itagüí',
                             'Manizales', 'Medellín', 'Pereira', 'Rionegro') THEN 'Andina'
           END AS region,
           CASE
               WHEN occupation IN ('Comerciante', 'Técnico electricista')
                   THEN 'Comercio y oficios'
               WHEN occupation IN ('Docente', 'Enfermera', 'Médico')
                   THEN 'Salud y educación'
               WHEN occupation IN ('Abogada', 'Administradora', 'Analista financiera', 'Contadora')
                   THEN 'Servicios profesionales'
               WHEN occupation IN ('Arquitecta', 'Diseñadora gráfica', 'Ingeniero de sistemas')
                   THEN 'Tecnología y diseño'
           END AS occupation_group
    FROM raw_customers
)
SELECT CASE WHEN regexp_full_match(loyalty_card_number, '[0-9]{1,12}')
            THEN '********' || right(lpad(loyalty_card_number, 12, '0'), 4)
       END AS loyalty_card_number,
       annual_spend,
       'CUST-' || upper(right(CAST(uuid() AS VARCHAR), 12)) AS customer_id,
       CASE WHEN decade BETWEEN 20 AND 60
            THEN CAST(decade AS VARCHAR) || '-' || CAST(decade + 9 AS VARCHAR)
       END AS age_group,
       region, occupation_group
FROM profiles
ORDER BY pos;

WITH cards AS (
    SELECT
        id,
        set_id,
        category,
        regulation_mark
    FROM {{ ref('stg_cards') }}
),

eras AS (
    SELECT
        begin_date,
        -- The current era has no end date in the seed; COALESCE so that
        -- consumers can always use BETWEEN safely.
        COALESCE(end_date, DATE '9999-12-31') AS end_date,
        legal_marks,
        season
    FROM {{ ref('regulation_eras') }}
)

SELECT
    c.id AS card_id,
    c.set_id,
    c.regulation_mark,
    e.season,
    e.begin_date,
    e.end_date
FROM cards AS c
JOIN eras AS e
    ON c.regulation_mark = ANY(STRING_TO_ARRAY(e.legal_marks, ','))
    OR (c.regulation_mark IS NULL AND c.category = 'Energy')

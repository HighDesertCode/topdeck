WITH cards AS (
    SELECT
        c.id,
        c.set_id,
        c.category,
        c.regulation_mark,
        s.release_date
    FROM {{ ref('stg_cards') }} AS c
    JOIN {{ ref('stg_sets') }} AS s
        ON s.id = c.set_id
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
    -- A card is never legal before its set released, even when its mark
    -- already was. (Approximation: sets become tournament-legal ~2 weeks
    -- after release; we clamp to release date and accept the small gap.)
    GREATEST(e.begin_date, c.release_date) AS begin_date,
    e.end_date
FROM cards AS c
JOIN eras AS e
    ON c.regulation_mark = ANY(STRING_TO_ARRAY(e.legal_marks, ','))
    OR (c.regulation_mark IS NULL AND c.category = 'Energy')
WHERE
    GREATEST(e.begin_date, c.release_date) <= e.end_date

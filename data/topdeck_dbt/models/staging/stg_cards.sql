SELECT
    id,
    "localId" AS local_id,
    "setId" AS set_id,
    name,
    category,
    rarity,
    UPPER("regulationMark") AS regulation_mark,
    "tcgplayerProductId" AS tcgplayer_product_id
FROM
    {{ source('raw', 'cards') }}
WHERE
    "setId" IN (SELECT id FROM {{ ref('stg_sets') }})

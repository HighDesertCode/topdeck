SELECT
    id,
    name,
    "serieId" as series_id,
    logo,
    symbol,
    "releaseDate" AS release_date,
    "abbreviationOfficial" AS set_abbr,
    "cardCountTotal" AS card_count
FROM
    {{ source('raw', 'sets') }}
WHERE
    id NOT IN (
        'fut2020',
        'swsh4.5sv',
        'cel25',
        'cel25cc',
        'swsh9tg',
        'swsh10tg',
        'swsh11tg',
        'swsh12tg',
        'swsh12.5gg',
        'mfb'
    )
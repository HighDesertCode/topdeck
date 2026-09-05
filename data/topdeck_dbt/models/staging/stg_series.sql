SELECT
    id,
    name,
    logo,
    "releaseDate" AS release_date
FROM
    {{ source('raw', 'series') }}

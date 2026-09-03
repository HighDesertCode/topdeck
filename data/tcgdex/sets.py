import datetime
import time

import polars as pl
from pydantic import AliasPath, BaseModel, Field

from common.secrets_retriever import fetch_secret
from tcgdex.client import SERIES_IDS, fetch_json

SERIES_PATH = "/v2/en/series"
SETS_PATH = "/v2/en/sets"


class SetData(BaseModel):
    id: str
    name: str
    serieId: str = Field(validation_alias=AliasPath("serie", "id"))
    logo: str | None = None
    symbol: str | None = None
    releaseDate: datetime.date
    abbreviationOfficial: str | None = Field(
        default=None, validation_alias=AliasPath("abbreviation", "official")
    )
    cardCountOfficial: int = Field(validation_alias=AliasPath("cardCount", "official"))
    cardCountTotal: int = Field(validation_alias=AliasPath("cardCount", "total"))
    standardLegal: bool = Field(validation_alias=AliasPath("legal", "standard"))
    expandedLegal: bool = Field(validation_alias=AliasPath("legal", "expanded"))


def list_set_ids(series_id: str) -> list[str]:
    series = fetch_json(f"{SERIES_PATH}/{series_id}")

    return [s["id"] for s in series["sets"]]


def validate_data(path: str) -> dict:
    data = fetch_json(path)

    return SetData.model_validate(data).model_dump()


def create_table(data: list[dict]) -> pl.DataFrame:
    schema = {
        "id": pl.String,
        "name": pl.String,
        "serieId": pl.String,
        "logo": pl.String,
        "symbol": pl.String,
        "releaseDate": pl.Date,
        "abbreviationOfficial": pl.String,
        "cardCountOfficial": pl.Int64,
        "cardCountTotal": pl.Int64,
        "standardLegal": pl.Boolean,
        "expandedLegal": pl.Boolean,
    }

    return pl.DataFrame(data, schema=schema)


def upload_table(df: pl.DataFrame) -> None:
    db_conn = fetch_secret("topdeck-db-dsn")

    df.write_database(
        table_name="raw.sets",
        connection=db_conn,
        if_table_exists="replace",
        engine="adbc",
    )


def main() -> None:
    set_ids: list[str] = []

    for series_id in SERIES_IDS:
        set_ids.extend(list_set_ids(series_id))
        time.sleep(1)

    all_sets = []

    for i, set_id in enumerate(set_ids, start=1):
        all_sets.append(validate_data(f"{SETS_PATH}/{set_id}"))
        print(f"[{i}/{len(set_ids)}] fetched {set_id}")
        time.sleep(1)

    df = create_table(all_sets)

    upload_table(df)

    print(f"loaded {df.height} rows into raw.sets")


if __name__ == "__main__":
    main()

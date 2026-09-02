import datetime
import time

import polars as pl
from pydantic import BaseModel

from secrets_retriever import fetch_secret
from tcgdex.client import fetch_json

BASE_URL = "/v2/en/series"
SERIES_IDS = ("sv", "me")


class SeriesData(BaseModel):
    id: str
    logo: str | None = None
    name: str
    releaseDate: datetime.date


def validate_data(path: str) -> dict:
    payload = fetch_json(path)
              
    return SeriesData.model_validate(payload).model_dump()


def create_table(data: list[dict]) -> pl.DataFrame:
    schema = {
        "id": pl.String,
        "logo": pl.String,
        "name": pl.String,
        "releaseDate": pl.Date,
    }

    return pl.DataFrame(data, schema=schema)


def upload_table(df: pl.DataFrame) -> None:
    db_conn = fetch_secret("topdeck-db-dsn")

    df.write_database(
        table_name="raw.series",
        connection=db_conn,
        if_table_exists="replace",
    )


def main() -> None:
    all_series = []

    for i, series_id in enumerate(SERIES_IDS):
        if i > 0:
            time.sleep(1)
        all_series.append(validate_data(f"{BASE_URL}/{series_id}"))

    df = create_table(all_series)

    upload_table(df)

    print(f"loaded {df.height} rows into raw.series")


if __name__ == "__main__":
    main()
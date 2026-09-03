import json
import time

import polars as pl
import requests
from pydantic import AliasPath, BaseModel, Field, ValidationError, model_validator

from common.secrets_retriever import fetch_secret
from tcgdex.client import SERIES_IDS, fetch_json
from tcgdex.sets import SETS_PATH, list_set_ids

CARDS_PATH = "/v2/en/cards"
FETCH_DELAY = 0.25


class CardData(BaseModel):
    id: str
    localId: str
    name: str
    category: str
    rarity: str | None = None
    regulationMark: str | None = None
    setId: str = Field(validation_alias=AliasPath("set", "id"))
    tcgplayerProductId: int | None = None
    cardmarketIdProduct: int | None = Field(
        default=None, validation_alias=AliasPath("pricing", "cardmarket", "idProduct")
    )

    @model_validator(mode="before")
    @classmethod
    def _extract_tcgplayer_product_id(cls, data: dict) -> dict:
        # productId nests under a per-card variant key (holofoil, normal, ...),
        # so no fixed AliasPath can reach it.
        # `or {}` guards keys that exist with a null value, which .get()
        # defaults do not catch.
        variants = (data.get("pricing") or {}).get("tcgplayer") or {}

        for value in variants.values():
            if isinstance(value, dict) and "productId" in value:
                data["tcgplayerProductId"] = value["productId"]
                break

        return data


def table_exists(db_conn: str) -> bool:
    # ::text because ADBC cannot map the regclass type to Arrow.
    result = pl.read_database_uri(
        "SELECT to_regclass('raw.cards')::text AS cards_table", db_conn, engine="adbc"
    )

    return result["cards_table"][0] is not None


def fetch_loaded_set_ids(db_conn: str) -> set[str]:
    if not table_exists(db_conn):
        return set()

    loaded = pl.read_database_uri(
        'SELECT DISTINCT "setId" FROM raw.cards', db_conn, engine="adbc"
    )

    return set(loaded["setId"].to_list())


def validate_data(path: str) -> dict:
    data = fetch_json(path)

    row = CardData.model_validate(data).model_dump()
    row["payload"] = json.dumps(data)

    return row


def create_table(data: list[dict]) -> pl.DataFrame:
    schema = {
        "id": pl.String,
        "localId": pl.String,
        "name": pl.String,
        "category": pl.String,
        "rarity": pl.String,
        "regulationMark": pl.String,
        "setId": pl.String,
        "tcgplayerProductId": pl.Int64,
        "cardmarketIdProduct": pl.Int64,
        "payload": pl.String,
    }

    return pl.DataFrame(data, schema=schema)


def upload_table(df: pl.DataFrame, db_conn: str) -> None:
    # raw.cards is created by hand (see the Topdeck note's DDL): ADBC's
    # append mode cannot create tables, and explicit DDL gives it a PK.
    df.write_database(
        table_name="raw.cards",
        connection=db_conn,
        if_table_exists="append",
        engine="adbc",
    )


def main() -> None:
    db_conn = fetch_secret("topdeck-db-dsn")

    loaded = fetch_loaded_set_ids(db_conn)

    missing: list[str] = []

    for series_id in SERIES_IDS:
        missing.extend(s for s in list_set_ids(series_id) if s not in loaded)
        time.sleep(1)

    failures: list[tuple[str, str]] = []
    total = 0

    for i, set_id in enumerate(missing, start=1):
        set_detail = fetch_json(f"{SETS_PATH}/{set_id}")
        card_ids = [card["id"] for card in set_detail["cards"]]

        rows = []
        set_failures = []

        for card_id in card_ids:
            time.sleep(FETCH_DELAY)

            try:
                rows.append(validate_data(f"{CARDS_PATH}/{card_id}"))
            except (requests.RequestException, ValidationError) as e:
                set_failures.append((card_id, type(e).__name__))

        # Partial sets are never persisted: a setId present in raw.cards
        # means the set is complete, so a failed set retries in full on the
        # next run instead of leaving a permanent silent gap.
        if set_failures:
            failures.extend(set_failures)
            print(
                f"[{i}/{len(missing)}] {set_id}: {len(set_failures)} of "
                f"{len(card_ids)} failed — set skipped, retries next run"
            )
            continue

        if rows:
            upload_table(create_table(rows), db_conn)

        total += len(rows)
        print(f"[{i}/{len(missing)}] {set_id}: {len(rows)}/{len(card_ids)} cards loaded")

    print(f"({total}) cards loaded into raw.cards")

    if failures:
        print(f"{len(failures)} failures:")

        for card_id, error in failures:
            print(f"  - {card_id} ({error})")

        raise SystemExit(1)


if __name__ == "__main__":
    main()

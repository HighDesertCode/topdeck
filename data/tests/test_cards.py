import json
from pathlib import Path

import polars as pl
import pytest
from pydantic import ValidationError

from tcgdex.cards import CardData, create_table

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    with open(FIXTURES / name) as f:
        return json.load(f)


def validated_row(payload: dict) -> dict:
    row = CardData.model_validate(payload).model_dump()
    row["payload"] = json.dumps(payload)

    return row


@pytest.fixture
def charizard() -> dict:
    """Real /v2/en/cards/sv03.5-199 response, saved 2026-09-02."""
    return load_fixture("card_detail_sv03.5-199.json")


@pytest.fixture
def tg_card() -> dict:
    """Real /v2/en/cards/swsh9tg-TG01 response — non-numeric localId."""
    return load_fixture("card_detail_swsh9tg-TG01.json")


class TestCardData:
    def test_parses_real_payload(self, charizard):
        card = CardData.model_validate(charizard)

        assert card.id == "sv03.5-199"
        assert card.localId == "199"
        assert card.setId == "sv03.5"
        assert card.regulationMark == "G"
        assert card.tcgplayerProductId == 517045
        assert card.cardmarketIdProduct is not None

    def test_non_numeric_local_id_stays_string(self, tg_card):
        card = CardData.model_validate(tg_card)

        assert card.localId == "TG01"
        assert card.setId == "swsh9tg"

    def test_missing_pricing_defaults_product_ids_to_none(self, charizard):
        del charizard["pricing"]

        card = CardData.model_validate(charizard)

        assert card.tcgplayerProductId is None
        assert card.cardmarketIdProduct is None

    def test_missing_required_field_raises(self, charizard):
        del charizard["name"]

        with pytest.raises(ValidationError):
            CardData.model_validate(charizard)


class TestCreateTable:
    def test_one_row_per_card(self, charizard, tg_card):
        df = create_table([validated_row(charizard), validated_row(tg_card)])

        assert df.shape == (2, 10)
        assert df["id"].to_list() == ["sv03.5-199", "swsh9tg-TG01"]

    def test_column_types_match_schema(self, charizard):
        df = create_table([validated_row(charizard)])

        assert df.schema["tcgplayerProductId"] == pl.Int64
        assert df.schema["payload"] == pl.String

    def test_payload_round_trips(self, charizard):
        df = create_table([validated_row(charizard)])

        restored = json.loads(df["payload"][0])

        assert restored["attacks"] == charizard["attacks"]

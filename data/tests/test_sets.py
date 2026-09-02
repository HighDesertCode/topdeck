import datetime
import json
from pathlib import Path

import polars as pl
import pytest
from pydantic import ValidationError

from tcgdex.sets import SetData, create_table

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    with open(FIXTURES / name) as f:
        return json.load(f)


@pytest.fixture
def sv01_detail() -> dict:
    """Real /v2/en/sets/sv01 response, saved 2026-09-02 (includes full cards list)."""
    return load_fixture("set_detail_sv01.json")


@pytest.fixture
def sve_detail() -> dict:
    """Real /v2/en/sets/sve response — energy set with no 'logo' or 'symbol'."""
    return load_fixture("set_detail_sve.json")


class TestSetData:
    def test_parses_real_payload(self, sv01_detail):
        s = SetData.model_validate(sv01_detail)

        assert s.id == "sv01"
        assert s.serieId == "sv"
        assert s.abbreviationOfficial == "SVI"
        assert s.releaseDate == datetime.date(2023, 3, 31)
        assert s.cardCountOfficial == 198
        assert s.cardCountTotal == 258
        assert s.standardLegal is False
        assert s.expandedLegal is True

    def test_missing_logo_and_symbol_default_to_none(self, sve_detail):
        s = SetData.model_validate(sve_detail)

        assert s.logo is None
        assert s.symbol is None

    def test_missing_nested_field_raises(self, sv01_detail):
        del sv01_detail["cardCount"]

        with pytest.raises(ValidationError):
            SetData.model_validate(sv01_detail)

    def test_malformed_date_raises(self, sv01_detail):
        sv01_detail["releaseDate"] = "not-a-date"

        with pytest.raises(ValidationError):
            SetData.model_validate(sv01_detail)


class TestCreateTable:
    def test_one_row_per_set(self, sv01_detail, sve_detail):
        validated = [
            SetData.model_validate(d).model_dump() for d in (sv01_detail, sve_detail)
        ]

        df = create_table(validated)

        assert df.shape == (2, 11)
        assert df["id"].to_list() == ["sv01", "sve"]

    def test_column_types_match_schema(self, sv01_detail):
        validated = [SetData.model_validate(sv01_detail).model_dump()]

        df = create_table(validated)

        assert df.schema["releaseDate"] == pl.Date
        assert df.schema["cardCountOfficial"] == pl.Int64
        assert df.schema["standardLegal"] == pl.Boolean

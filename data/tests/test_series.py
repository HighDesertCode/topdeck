import datetime
import json
from pathlib import Path

import polars as pl
import pytest
import requests
import responses
from pydantic import ValidationError
from tcgdex.series import SeriesData, create_table, validate_data

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    with open(FIXTURES / name) as f:
        return json.load(f)


@pytest.fixture
def sv_detail() -> dict:
    """Real /v2/en/series/sv response, saved 2026-08-31."""
    return load_fixture("series_detail_sv.json")


@pytest.fixture
def misc_detail() -> dict:
    """Real /v2/en/series/misc response — has no 'logo' key."""
    return load_fixture("series_detail_misc.json")


class TestSeriesData:
    def test_parses_real_payload(self, sv_detail):
        series = SeriesData.model_validate(sv_detail)

        assert series.id == "sv"
        assert series.name == "Scarlet & Violet"
        assert series.releaseDate == datetime.date(2023, 3, 31)

    def test_release_date_is_parsed_to_date_type(self, sv_detail):
        series = SeriesData.model_validate(sv_detail)

        assert isinstance(series.releaseDate, datetime.date)

    def test_missing_logo_defaults_to_none(self, misc_detail):
        series = SeriesData.model_validate(misc_detail)

        assert series.logo is None

    def test_malformed_date_raises(self, sv_detail):
        sv_detail["releaseDate"] = "not-a-date"

        with pytest.raises(ValidationError):
            SeriesData.model_validate(sv_detail)

    def test_missing_required_field_raises(self, sv_detail):
        del sv_detail["name"]

        with pytest.raises(ValidationError):
            SeriesData.model_validate(sv_detail)


class TestCreateTable:
    def test_one_row_per_series(self, sv_detail, misc_detail):
        validated = [
            SeriesData.model_validate(d).model_dump() for d in (sv_detail, misc_detail)
        ]

        df = create_table(validated)

        assert df.shape == (2, 4)
        assert df["id"].to_list() == ["sv", "misc"]

    def test_column_types_match_schema(self, sv_detail):
        validated = [SeriesData.model_validate(sv_detail).model_dump()]

        df = create_table(validated)

        assert df.schema["releaseDate"] == pl.Date
        assert df.schema["id"] == pl.String

    def test_missing_logo_becomes_null(self, misc_detail):
        validated = [SeriesData.model_validate(misc_detail).model_dump()]

        df = create_table(validated)

        assert df["logo"][0] is None


class TestValidateData:
    PATH = "/v2/en/series/sv"
    URL = f"https://api.tcgdex.net{PATH}"

    @responses.activate
    def test_returns_validated_dict(self, sv_detail):
        responses.add(responses.GET, self.URL, json=sv_detail, status=200)

        result = validate_data(self.PATH)

        assert result["id"] == "sv"
        assert result["releaseDate"] == datetime.date(2023, 3, 31)

    @responses.activate
    def test_http_error_raises(self):
        responses.add(responses.GET, self.URL, status=500)

        with pytest.raises(requests.HTTPError):
            validate_data(self.PATH)

    @responses.activate
    def test_invalid_payload_raises(self):
        responses.add(responses.GET, self.URL, json={"id": "sv"}, status=200)

        with pytest.raises(ValidationError):
            validate_data(self.PATH)

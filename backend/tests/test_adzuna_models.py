"""Tests for the Adzuna pydantic models (no network: recorded fixture only)."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from jobmatch.ingest.adzuna import AdzunaJob, AdzunaResponse
from jobmatch.ingest.models import Source

FIXTURE = Path(__file__).parent / "fixtures" / "adzuna_sample.json"


@pytest.fixture
def response() -> AdzunaResponse:
    return AdzunaResponse.model_validate(
        json.loads(FIXTURE.read_text(encoding="utf-8"))
    )


def test_parses_top_level(response: AdzunaResponse) -> None:
    # ``count`` is the total across pages, so it can exceed the results on this page.
    assert response.count == 3
    assert response.mean == 210000
    assert len(response.results) == 2


def test_parses_nested_objects(response: AdzunaResponse) -> None:
    job = response.results[1]
    assert job.id == "5943106416"
    assert job.company.display_name == "Unemplojorempleo"
    assert job.location.area == ["México", "Sonora", "Hermosillo"]
    assert job.category.tag == "unknown"
    assert job.created == datetime(2026, 10, 26, 22, 35, 12, tzinfo=UTC)


def test_missing_coordinates_are_none(response: AdzunaResponse) -> None:
    job = response.results[0]
    assert job.latitude is None
    assert job.longitude is None
    assert job.contract_time is None


def test_salary_is_predicted_string_becomes_bool(response: AdzunaResponse) -> None:
    assert response.results[0].salary_is_predicted is False


def test_missing_required_field_raises() -> None:
    with pytest.raises(ValidationError):
        AdzunaJob.model_validate({"id": "1", "title": "No url"})


def test_to_posting_maps_fields(response: AdzunaResponse) -> None:
    posting = response.results[1].to_posting(country="mx")
    assert posting.source is Source.ADZUNA
    assert posting.source_id == "5943106416"
    assert posting.company == "Unemplojorempleo"
    assert posting.location == "Hermosillo, Sonora"
    assert posting.category is None  # "unknown" tag is not a real category
    assert posting.salary_min == 222000
    assert posting.salary_currency == "MXN"
    assert posting.published_at.tzinfo is not None


def test_to_posting_without_salary_has_no_currency(response: AdzunaResponse) -> None:
    job = response.results[0].model_copy(
        update={"salary_min": None, "salary_max": None}
    )
    assert job.to_posting(country="mx").salary_currency is None

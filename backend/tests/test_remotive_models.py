"""Tests for the Remotive pydantic models (no network: fixture only)."""

import json
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from jobmatch.ingest.models import Source
from jobmatch.ingest.remotive import RemotiveJob, RemotiveResponse

FIXTURE = Path(__file__).parent / "fixtures" / "remotive_sample.json"


@pytest.fixture
def response() -> RemotiveResponse:
    return RemotiveResponse.model_validate(
        json.loads(FIXTURE.read_text(encoding="utf-8"))
    )


def test_parses_top_level_aliases(response: RemotiveResponse) -> None:
    assert response.job_count == 2
    assert len(response.jobs) == 2


def test_parses_job_types(response: RemotiveResponse) -> None:
    job = response.jobs[0]
    assert job.id == 1001
    assert job.publication_date == datetime(2026, 11, 10, 10, 23, 26)
    assert job.salary == "$120k - $150k"


def test_empty_strings_become_none(response: RemotiveResponse) -> None:
    job = response.jobs[1]
    assert job.job_type is None
    assert job.salary is None
    assert job.company_logo is None


def test_unknown_fields_are_ignored(response: RemotiveResponse) -> None:
    assert not hasattr(response.jobs[1], "some_new_field")


def test_missing_required_field_raises() -> None:
    with pytest.raises(ValidationError):
        RemotiveJob.model_validate({"id": 1, "title": "No url"})


def test_to_posting_maps_fields(response: RemotiveResponse) -> None:
    posting = response.jobs[0].to_posting()
    assert posting.source is Source.REMOTIVE
    assert posting.source_id == "1001"
    assert posting.title == "Senior Data Scientist"
    assert posting.company == "Example Analytics"
    assert posting.location == "Americas"
    assert posting.contract_type == "full_time"
    assert posting.salary_text == "$120k - $150k"
    assert str(posting.url).startswith("https://remotive.com/")
    # Naive Remotive dates are stored as UTC so they compare with Adzuna's.
    assert posting.published_at.tzinfo is not None

"""Source-agnostic job posting model: the shape every source is normalized into.

Each source (Remotive, Adzuna, ...) has its own raw pydantic models that mirror the
API response exactly. Those raw models expose ``to_posting()``, which maps them into
``JobPosting`` so the rest of the pipeline (dedupe, the ``jobs`` table, NLP) only ever
deals with one schema.
"""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator


class Source(StrEnum):
    REMOTIVE = "remotive"
    ADZUNA = "adzuna"


class JobPosting(BaseModel):
    """A job posting normalized across sources (one row of the ``jobs`` table)."""

    model_config = ConfigDict(frozen=True)

    source: Source
    source_id: str
    url: HttpUrl
    title: str
    company: str | None
    location: str | None
    description: str
    published_at: datetime
    category: str | None = None
    contract_type: str | None = None
    # Salary is kept as the source gives it; normalization (annual, USD/MXN) is Phase 2.
    # Remotive only has free text; Adzuna has numbers in the country's currency.
    salary_text: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    salary_is_predicted: bool = False

    @field_validator("published_at")
    @classmethod
    def assume_utc(cls, value: datetime) -> datetime:
        """Remotive dates are naive and Adzuna's are UTC ("Z"); make all of them aware.

        Mixing naive and aware datetimes raises TypeError when comparing or sorting.
        """
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

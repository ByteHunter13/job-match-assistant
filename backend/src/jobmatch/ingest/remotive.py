"""Remotive API models.

Docs: https://github.com/remotive-com/remote-jobs-api
Endpoint: GET https://remotive.com/api/remote-jobs?category=&search=&limit=

Usage rules from Remotive: at most ~4 requests per day (more than 2 per minute gets
blocked), jobs are delayed 24h, and every displayed job must link back to its Remotive
URL and name Remotive as the source.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from jobmatch.ingest.models import JobPosting, Source

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"


class RemotiveJob(BaseModel):
    """One item of ``jobs`` in the Remotive response, mirroring the API fields."""

    # Ignore unknown fields so a new API field doesn't break ingestion;
    # the full raw JSON is stored separately anyway.
    model_config = ConfigDict(extra="ignore")

    id: int
    url: HttpUrl
    title: str
    company_name: str
    company_logo: str | None = None
    category: str
    job_type: str | None = None
    publication_date: datetime
    candidate_required_location: str | None = None
    salary: str | None = None
    description: str

    @field_validator(
        "job_type",
        "salary",
        "company_logo",
        "candidate_required_location",
        mode="before",
    )
    @classmethod
    def empty_str_to_none(cls, value: object) -> object:
        """Remotive sends ``""`` for missing optional fields; store them as ``None``."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    def to_posting(self) -> JobPosting:
        return JobPosting(
            source=Source.REMOTIVE,
            source_id=str(self.id),
            url=self.url,
            title=self.title.strip(),
            company=self.company_name.strip() or None,
            location=self.candidate_required_location,
            description=self.description,
            published_at=self.publication_date,
            category=self.category,
            contract_type=self.job_type,
            salary_text=self.salary,
        )


class RemotiveResponse(BaseModel):
    """Top-level Remotive response: ``{"0-legal-notice", "job-count", "jobs"}``."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    legal_notice: str | None = Field(default=None, alias="0-legal-notice")
    job_count: int = Field(alias="job-count")
    jobs: list[RemotiveJob]

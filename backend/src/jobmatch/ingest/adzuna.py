"""Adzuna API models.

Docs: https://developer.adzuna.com/docs/search
Endpoint: GET https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
    ?app_id=...&app_key=...&results_per_page=...&what=...&content-type=application/json

Usage rules: the free tier allows 25 calls per minute (check the account dashboard for
the daily/monthly quota). Every displayed job must show "Adzuna" linked to its site,
and research use must cite "The Adzuna API" as the source.

Caveats seen in real responses:
- ``description`` is a truncated snippet (~500 chars ending in "…"), not the full text.
- ``latitude``/``longitude``, salaries and ``contract_type`` can be missing.
- Salaries come in the local currency of ``{country}`` and may be predicted by Adzuna
  (``salary_is_predicted == "1"``) rather than stated in the ad.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl

from jobmatch.ingest.models import JobPosting, Source

ADZUNA_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"

# Currency of the salaries returned for each Adzuna country code.
COUNTRY_CURRENCY: dict[str, str] = {
    "mx": "MXN",
    "us": "USD",
    "ca": "CAD",
    "gb": "GBP",
    "es": "EUR",
    "br": "BRL",
}


class AdzunaCompany(BaseModel):
    model_config = ConfigDict(extra="ignore")

    display_name: str | None = None


class AdzunaLocation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    display_name: str | None = None
    area: list[str] = []


class AdzunaCategory(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tag: str
    label: str


class AdzunaJob(BaseModel):
    """One item of ``results`` in the Adzuna response, mirroring the API fields."""

    model_config = ConfigDict(extra="ignore")

    id: str
    redirect_url: HttpUrl
    title: str
    description: str
    created: datetime
    company: AdzunaCompany
    location: AdzunaLocation
    category: AdzunaCategory
    latitude: float | None = None
    longitude: float | None = None
    contract_type: str | None = None  # "permanent" / "contract"
    contract_time: str | None = None  # "full_time" / "part_time"
    salary_min: float | None = None
    salary_max: float | None = None
    salary_is_predicted: bool = False  # API sends "0"/"1"; pydantic coerces to bool

    def to_posting(self, country: str) -> JobPosting:
        """Map to the common schema. ``country`` is the code used in the request."""
        category = None if self.category.tag == "unknown" else self.category.label
        has_salary = self.salary_min is not None or self.salary_max is not None
        return JobPosting(
            source=Source.ADZUNA,
            source_id=self.id,
            url=self.redirect_url,
            title=self.title.strip(),
            company=self.company.display_name,
            location=self.location.display_name,
            description=self.description,
            published_at=self.created,
            category=category,
            contract_type=self.contract_type,
            salary_min=self.salary_min,
            salary_max=self.salary_max,
            salary_currency=COUNTRY_CURRENCY.get(country) if has_salary else None,
            salary_is_predicted=self.salary_is_predicted,
        )


class AdzunaResponse(BaseModel):
    """Top-level Adzuna response: ``{"count", "mean", "results", "__CLASS__"}``."""

    model_config = ConfigDict(extra="ignore")

    count: int  # total matches across ALL pages, not len(results)
    mean: float | None = None  # mean salary of the matches
    results: list[AdzunaJob]

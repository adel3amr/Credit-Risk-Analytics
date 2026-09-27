from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .contracts import check_features, INDUSTRIES


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Borrower(Strict):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    industry: str
    observed_at: date
    collateral_type: Literal["Cash", "Mortgage", "Other", "Unsecured"]
    features: dict[str, float]

    @field_validator("industry")
    @classmethod
    def industry_valid(cls, v):
        if v not in INDUSTRIES:
            raise ValueError("Unsupported industry")
        return v

    @field_validator("features")
    @classmethod
    def features_valid(cls, v):
        return check_features(v)


class Facility(Strict):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    borrower_id: str
    observed_at: date
    product: Literal[
        "Term Loan", "OVD", "Import LC", "Performance Guarantee", "Financial Guarantee"
    ]
    drawn: float = Field(ge=0)
    limit: float = Field(ge=0)
    face: float = Field(ge=0)
    remaining_months: float = Field(ge=0)
    collateral_type: Literal["Cash", "Mortgage", "Other", "Unsecured"]
    collateral_coverage: float = Field(ge=0)
    guarantee_coverage: float = Field(ge=0, le=1)
    lien_rank: Literal["First", "Second", "Unsecured"]

    @model_validator(mode="after")
    def consistency(self):
        if self.collateral_type == "Unsecured" and (
            self.collateral_coverage != 0 or self.lien_rank != "Unsecured"
        ):
            raise ValueError("Unsecured facility has inconsistent security fields")
        if self.product in ("Term Loan", "OVD") and self.face != 0:
            raise ValueError("Direct facility cannot have trade face amount")
        if self.product not in ("Term Loan", "OVD") and (
            self.drawn != 0 or self.limit != 0
        ):
            raise ValueError("Trade facility must use face amount only")
        return self


class DatasetInput(Strict):
    name: str = Field(min_length=1, max_length=120)
    effective_date: date
    source: str = Field(min_length=1, max_length=200)
    borrowers: list[Borrower] = Field(min_length=1, max_length=15000)
    facilities: list[Facility] = Field(max_length=50000)

    @model_validator(mode="after")
    def links(self):
        ids = [b.id for b in self.borrowers]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate borrower")
        fids = [f.id for f in self.facilities]
        if len(fids) != len(set(fids)):
            raise ValueError("Duplicate facility")
        known = set(ids)
        for f in self.facilities:
            if f.borrower_id not in known:
                raise ValueError("Orphan facility")
        for entity in [*self.borrowers, *self.facilities]:
            if entity.observed_at > self.effective_date:
                raise ValueError("Future information prohibited")
        return self


class RunInput(Strict):
    dataset_id: str
    request_key: str = Field(min_length=8, max_length=100)
    purpose: Literal["reference", "bank"] = "reference"


class OverrideInput(Strict):
    run_id: str
    facility_id: str
    proposed_ecl: float = Field(ge=0)
    reason: str = Field(min_length=20, max_length=2000)


class ApprovalInput(Strict):
    decision: Literal["APPROVED", "REJECTED"]


class FindingInput(Strict):
    component: str = Field(min_length=1, max_length=100)
    severity: Literal["Critical", "High", "Moderate", "Low"]
    description: str = Field(min_length=10, max_length=3000)
    evidence: dict
    owner: str = Field(min_length=1, max_length=100)


class FindingEventInput(Strict):
    status: Literal["OPEN", "IN_REMEDIATION", "RETEST", "CLOSED"]
    note: str = Field(min_length=20, max_length=3000)


class Outcome(Strict):
    facility_id: str
    realized_lgd: float = Field(ge=0, le=1)
    resolved_at: date


class OutcomesInput(Strict):
    outcomes: list[Outcome] = Field(min_length=1, max_length=50000)


class CopilotInput(Strict):
    question: str = Field(min_length=3, max_length=1000)
    use_case: Literal["borrower", "portfolio", "model_risk", "credit_review"]
    run_id: str | None = Field(default=None, max_length=100)
    borrower_id: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def required_scope(self):
        if self.use_case in ("borrower", "credit_review") and (
            not self.run_id or not self.borrower_id
        ):
            raise ValueError("Borrower use cases require run_id and borrower_id")
        if self.use_case == "portfolio" and not self.run_id:
            raise ValueError("Portfolio use case requires run_id")
        return self

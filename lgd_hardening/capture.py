"""Prediction-time recovery evidence contract; no proxy is derived implicitly."""
from datetime import date
from pydantic import BaseModel,ConfigDict,Field,model_validator


class RecoveryEvidence(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    facility_id:str=Field(min_length=1)
    reporting_date:date
    recorded_at:date
    effective_date:date
    source_record_id:str=Field(min_length=1)
    source_system:str=Field(min_length=1)
    evidence_reference:str=Field(min_length=1)
    evidence_kind:str=Field(pattern='^(GUARANTEE|COLLATERAL)$')
    nominal_amount:float=Field(ge=0,allow_inf_nan=False)
    eligible_amount:float=Field(ge=0,allow_inf_nan=False)
    currency:str=Field(pattern='^[A-Z]{3}$')
    provider_or_asset_id:str=Field(min_length=1)
    enforceability_status:str=Field(pattern='^(CONFIRMED|UNCONFIRMED|INELIGIBLE)$')
    legal_review_reference:str|None=None
    valuation_or_financial_date:date
    valuation_or_financial_reference:str=Field(min_length=1)
    expiry_date:date|None=None
    derivation_version:str|None=None

    @model_validator(mode='after')
    def coherent(self):
        if max(self.recorded_at,self.effective_date,self.valuation_or_financial_date)>self.reporting_date:
            raise ValueError('Evidence unavailable at prediction time')
        if self.eligible_amount>self.nominal_amount:
            raise ValueError('Eligible amount exceeds nominal coverage')
        if self.enforceability_status!='CONFIRMED' and self.eligible_amount>0:
            raise ValueError('Unconfirmed legal support cannot be treated as eligible')
        if self.enforceability_status=='CONFIRMED' and not (self.legal_review_reference or '').strip():
            raise ValueError('Confirmed enforceability requires legal evidence')
        if self.expiry_date and self.expiry_date<self.reporting_date and self.eligible_amount>0:
            raise ValueError('Expired protection cannot be treated as eligible')
        return self


def require_validated_derivation(records,approved_versions):
    """A complete record alone never authorizes a numeric LGD quality feature."""
    if not records:raise ValueError('Recovery evidence capture missing')
    for r in records:
        if not r.derivation_version or r.derivation_version not in approved_versions:
            raise ValueError('Recovery-feature derivation has not been independently validated')
    return True

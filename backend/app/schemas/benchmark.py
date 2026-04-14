import uuid
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class BenchmarkCreate(BaseModel):
    grade_level: int
    subject_id: uuid.UUID
    tier1_min: float = Field(ge=0, le=100)
    tier2_min: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def validate_threshold_order(self):
        if self.tier1_min < self.tier2_min:
            raise ValueError("tier1_min must be greater than or equal to tier2_min")
        return self


class BenchmarkUpdate(BaseModel):
    tier1_min: Optional[float] = Field(default=None, ge=0, le=100)
    tier2_min: Optional[float] = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def validate_threshold_order(self):
        if self.tier1_min is not None and self.tier2_min is not None and self.tier1_min < self.tier2_min:
            raise ValueError("tier1_min must be greater than or equal to tier2_min")
        return self


class BenchmarkResponse(BaseModel):
    id: uuid.UUID
    grade_level: int
    subject_id: uuid.UUID
    tier1_min: float
    tier2_min: float
    model_config = {"from_attributes": True}

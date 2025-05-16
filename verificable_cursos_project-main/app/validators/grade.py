from typing import Optional

from pydantic import BaseModel, Field, validator


class GradeSchema(BaseModel):
    id: Optional[int] = Field(None, gt=0)
    student_id: int = Field(..., gt=0)
    evaluation_instance_id: int = Field(..., gt=0)
    grade: float = Field(..., ge=1.0, le=7.0)

    @validator("grade")
    def max_one_decimal(cls, v: float) -> float:
        if round(v, 1) != v:
            raise ValueError("La nota debe tener como máximo un decimal")
        return v

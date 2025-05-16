from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.validators.constants_evaluation_instance import (
    IsOptionalType,
    NameType,
    WeightTypeType,
    WeightValueType,
)
from db import DatabaseConnection


class EvaluationInstanceSchema(BaseModel):
    id: Optional[int] = Field(None)
    evaluation_id: int = Field(..., description="ID de la evaluación padre", gt=0)
    name: NameType
    weight_type: WeightTypeType
    weight: WeightValueType
    is_optional: IsOptionalType = False

    @field_validator("evaluation_id", mode="after")
    def evaluation_exists(cls, v):
        db = DatabaseConnection()
        cur = db.connect()
        cur.execute("SELECT 1 FROM evaluation WHERE id = %s", (v,))
        exists = cur.fetchone()
        cur.close()
        if not exists:
            raise ValueError(f"Evaluación {v} no encontrada")
        return v

    @model_validator(mode="after")
    def unique_name(cls, m):
        db = DatabaseConnection()
        cur = db.connect()
        if m.id is None:
            cur.execute(
                "SELECT 1 FROM evaluation_instance WHERE evaluation_id = %s AND name = %s",
                (m.evaluation_id, m.name),
            )
        else:
            cur.execute(
                "SELECT 1 FROM evaluation_instance WHERE evaluation_id = %s AND name = %s AND id <> %s",
                (m.evaluation_id, m.name, m.id),
            )
        dup = cur.fetchone()
        cur.close()
        if dup:
            raise ValueError(f"La instancia '{m.name}' ya existe para esta evaluación")
        return m

from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.validators.constants_section import (
    EvaluationSchemeType,
    SectionNumberType,
)
from db import DatabaseConnection


class SectionSchema(BaseModel):
    id: Optional[int] = Field(None)
    course_instance_id: int = Field(..., description="ID de la instancia de curso")
    section_number: SectionNumberType
    evaluation_scheme: EvaluationSchemeType = Field(
        ..., description="Tipo de evaluación: 'percentage' o 'weight'"
    )

    @field_validator("course_instance_id", mode="after")
    def instance_exists(cls, v):
        db = DatabaseConnection()
        cur = db.connect()
        cur.execute("SELECT 1 FROM course_instance WHERE id = %s", (v,))
        exists = cur.fetchone()
        cur.close()
        if not exists:
            raise ValueError(f"Instancia de curso {v} no encontrada")
        return v

    @model_validator(mode="after")
    def unique_section(cls, m):
        db = DatabaseConnection()
        cur = db.connect()
        if m.id is None:
            cur.execute(
                "SELECT 1 FROM section WHERE course_instance_id = %s AND section_number = %s",
                (m.course_instance_id, m.section_number),
            )
        else:
            cur.execute(
                "SELECT 1 FROM section WHERE course_instance_id = %s AND section_number = %s AND id <> %s",
                (m.course_instance_id, m.section_number, m.id),
            )
        dup = cur.fetchone()
        cur.close()
        if dup:
            raise ValueError(
                f"La sección '{m.section_number}' ya existe en esta instancia"
            )
        return m

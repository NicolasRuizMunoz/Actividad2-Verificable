from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.validators.constants_evaluation import (
    NameType,
    WeightValue,
)
from db import DatabaseConnection


class EvaluationSchema(BaseModel):
    id: Optional[int] = Field(None)
    course_instance_id: int = Field(..., description="ID de la instancia de curso")
    section_id: int = Field(..., description="ID de la sección")
    name: NameType
    weight: WeightValue

    @field_validator("section_id", mode="after")
    def section_exists(cls, v):
        db = DatabaseConnection()
        cur = db.connect()
        cur.execute("SELECT 1 FROM section WHERE id = %s", (v,))
        exists = cur.fetchone()
        cur.close()
        if not exists:
            raise ValueError(f"Sección {v} no encontrada")
        return v

    @field_validator("course_instance_id", mode="after")
    def instance_exists(cls, v):
        db = DatabaseConnection()
        cur = db.connect()
        cur.execute("SELECT 1 FROM course_instance WHERE id = %s", (v,))
        exists = cur.fetchone()
        cur.close()
        if not exists:
            raise ValueError(f"Instancia {v} no encontrada")
        return v

    @field_validator("name", mode="after")
    def unique_name_within_section(cls, v, info):
        """
        Verifica que no exista otra evaluación con el mismo nombre
        en esta sección, excluyendo la propia en caso de update.
        """
        eval_id = info.data.get("id")
        section_id = info.data["section_id"]

        db = DatabaseConnection()
        cur = db.connect()
        if eval_id is None:
            cur.execute(
                "SELECT 1 FROM evaluation WHERE section_id = %s AND name = %s",
                (section_id, v),
            )
        else:
            cur.execute(
                "SELECT 1 FROM evaluation WHERE section_id = %s AND name = %s AND id <> %s",
                (section_id, v, eval_id),
            )
        exists = cur.fetchone()
        cur.close()

        if exists:
            raise ValueError(f'El nombre "{v}" ya está en uso en esta sección.')
        return v

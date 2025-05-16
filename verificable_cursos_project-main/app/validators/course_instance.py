from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.validators.constants_course_instance import SemesterType, YearType
from db import DatabaseConnection


class CourseInstanceSchema(BaseModel):
    id: Optional[int] = Field(None)
    course_id: int = Field(..., description="ID del curso al que pertenece")
    semester: SemesterType = Field(..., description="Semestre: '01' o '02'")
    year: YearType = Field(..., description="Año de la instancia, p.ej. 2025")

    @field_validator("course_id", mode="after")
    def course_must_exist(cls, v):
        db = DatabaseConnection()
        cur = db.connect()
        cur.execute("SELECT 1 FROM course WHERE id = %s", (v,))
        exists = cur.fetchone()
        cur.close()
        if not exists:
            raise ValueError(f"No existe el curso con id={v}")
        return v

    @model_validator(mode="after")
    def unique_instance(cls, m):
        db = DatabaseConnection()
        cur = db.connect()
        if m.id is None:
            cur.execute(
                "SELECT 1 FROM course_instance WHERE course_id=%s AND semester=%s AND year=%s",
                (m.course_id, m.semester, m.year),
            )
        else:
            cur.execute(
                "SELECT 1 FROM course_instance WHERE course_id=%s AND semester=%s AND year=%s AND id<>%s",
                (m.course_id, m.semester, m.year, m.id),
            )
        dup = cur.fetchone()
        cur.close()
        if dup:
            raise ValueError(
                f"La instancia para curso {m.course_id} ({m.semester}/{m.year}) ya existe"
            )
        return m

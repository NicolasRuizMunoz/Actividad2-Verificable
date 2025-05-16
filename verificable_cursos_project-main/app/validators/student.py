# app/validators/student.py
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.validators.constants_student import (
    EmailType,
    MaxDate,
    MinDate,
    NameType,
)
from db import DatabaseConnection


class StudentSchema(BaseModel):
    id: Optional[int] = Field(None)
    nombre: NameType
    correo: EmailType
    anio_ingreso: date

    @field_validator("anio_ingreso", mode="before")
    def parse_year(cls, v):
        if isinstance(v, int):
            return date(v, 1, 1)
        if isinstance(v, str) and v.isdigit() and len(v) == 4:
            return date(int(v), 1, 1)
        return v

    @field_validator("anio_ingreso", mode="after")
    def check_fecha(cls, v: date):
        if v < MinDate or v > MaxDate:
            raise ValueError(
                f"La fecha debe estar entre {MinDate.isoformat()} y {MaxDate.isoformat()}"
            )
        return v

    @field_validator("correo", mode="after")
    def unique_correo(cls, v, info):
        student_id = info.data.get("id")
        db = DatabaseConnection()
        cur = db.connect()
        if student_id is None:
            cur.execute("SELECT 1 FROM student WHERE email = %s", (v,))
        else:
            cur.execute(
                "SELECT 1 FROM student WHERE email = %s AND id <> %s", (v, student_id)
            )
        exists = cur.fetchone()
        cur.close()
        if exists:
            raise ValueError(f'El correo "{v}" ya está en uso')
        return v

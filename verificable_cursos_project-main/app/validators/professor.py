from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.validators.constants_professor import EmailType, NameType
from db import DatabaseConnection


class ProfessorSchema(BaseModel):
    id: Optional[int] = Field(None)
    nombre: NameType
    correo: EmailType

    @field_validator("correo", mode="after")
    def unique_email(cls, v, info):
        prof_id = info.data.get("id")
        db = DatabaseConnection()
        cur = db.connect()
        if prof_id is None:
            cur.execute("SELECT 1 FROM professor WHERE email = %s", (v,))
        else:
            cur.execute(
                "SELECT 1 FROM professor WHERE email = %s AND id <> %s", (v, prof_id)
            )
        exists = cur.fetchone()
        cur.close()
        if exists:
            raise ValueError(f'El correo "{v}" ya está en uso')
        return v

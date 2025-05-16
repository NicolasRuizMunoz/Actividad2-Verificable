import json
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.validators.constants_course import (
    CourseCode,
    Credits,
    Description,
    RequisiteCode,
)
from db import DatabaseConnection


class CourseSchema(BaseModel):
    id: Optional[int] = Field(None)
    codigo: CourseCode
    descripcion: Description
    requisitos: List[RequisiteCode] = Field(default_factory=list)
    creditos: Credits

    @field_validator("requisitos", mode="before")
    def _parse_requisitos(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @field_validator("requisitos", mode="before")
    def ensure_requisites_is_list(cls, v):
        if isinstance(v, str):
            return [v]
        if not isinstance(v, list):
            raise TypeError("`requisitos` debe ser una lista de strings.")
        return v

    @field_validator("requisitos", mode="after")
    def requisitos_existentes(cls, v: List[str], info):
        if not v:
            return v
        db = DatabaseConnection()
        cur = db.connect()
        placeholders = ",".join(["%s"] * len(v))
        cur.execute(f"SELECT code FROM course WHERE code IN ({placeholders})", tuple(v))
        found = {row["code"] for row in cur.fetchall()}
        cur.close()
        missing = set(v) - found
        if missing:
            raise ValueError(f"No se encontraron pre-requisitos: {sorted(missing)}")
        return v

    @field_validator("codigo", mode="after")
    def unique_codigo(cls, v, info):
        course_id = info.data.get("id")
        db = DatabaseConnection()
        cur = db.connect()
        if course_id is None:
            cur.execute("SELECT 1 FROM course WHERE code = %s", (v,))
        else:
            cur.execute(
                "SELECT 1 FROM course WHERE code = %s AND id <> %s", (v, course_id)
            )
        exists = cur.fetchone()
        cur.close()
        if exists:
            raise ValueError(f'El código "{v}" ya está en uso')
        return v

    @model_validator(mode="after")
    def no_self_prerequisite(cls, m):
        if m.codigo in m.requisitos:
            raise ValueError("Un curso no puede ser prerrequisito de sí mismo")
        return m

    @model_validator(mode="after")
    def no_circular_prerequisites(cls, m):
        start = m.codigo
        db = DatabaseConnection()
        cur = db.connect()
        visited = set()
        stack = list(m.requisitos)
        while stack:
            code = stack.pop()
            if code == start:
                cur.close()
                raise ValueError(
                    f'El curso que seleccionó ya tiene prerequisitos en este curso."{start}"'
                )
            if code in visited:
                continue
            visited.add(code)
            cur.execute("SELECT requisites FROM course WHERE code = %s", (code,))
            row = cur.fetchone()
            if row and row.get("requisites"):
                try:
                    stack.extend(json.loads(row["requisites"]))
                except BaseException:
                    pass
        cur.close()
        return m

    @model_validator(mode="after")
    def no_sections_on_update(cls, m):
        if m.id is None:
            return m
        db = DatabaseConnection()
        cur = db.connect()
        cur.execute(
            """
            SELECT COUNT(*) AS cnt
              FROM section s
              JOIN course_instance ci ON s.course_instance_id = ci.id
             WHERE ci.course_id = %s
            """,
            (m.id,),
        )
        cnt = cur.fetchone().get("cnt", 0)
        cur.close()
        if cnt > 0:
            raise ValueError(
                f"No se puede modificar/eliminar curso {m.id}: tiene {cnt} sección(es) asociada(s)"
            )
        return m

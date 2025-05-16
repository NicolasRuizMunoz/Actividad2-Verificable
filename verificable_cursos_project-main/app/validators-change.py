from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Set, Tuple

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ValidationError,
    confloat,
)


class Course(BaseModel):
    id: int
    codigo: str = Field(max_length=255)
    descripcion: str = Field(max_length=255)
    requisitos: List[str]
    creditos: int


class Professor(BaseModel):
    id: int
    nombre: str = Field(max_length=255)
    correo: EmailStr


class Student(BaseModel):
    id: int
    nombre: str = Field(max_length=255)
    correo: EmailStr
    anio_ingreso: int = Field(ge=1990, le=date.today().year)


class CourseInstance(BaseModel):
    id: int
    curso_id: int
    semestre: str
    año: int


class Section(BaseModel):
    id: int
    instancia_curso: int
    profesor_id: int


class AlumnoSeccion(BaseModel):
    alumno_id: int
    seccion_id: int


class Nota(BaseModel):
    alumno_id: int
    evaluation_instance_id: int
    grade: confloat(ge=1.0, le=7.0)


class ValidationIssue(BaseModel):
    loc: str
    msg: str
    code: str = "value_error"


def validate_dataset(data: Dict[str, Any]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    def collect(model: Any, raw: Dict[str, Any], loc: str) -> None:
        try:
            model(**raw)
        except ValidationError as e:
            for err in e.errors():
                issues.append(
                    ValidationIssue(
                        loc=f"{loc}.{err['loc'][0]}",
                        msg=err["msg"],
                        code=err["type"],
                    )
                )

    for i, c in enumerate(data.get("cursos", [])):
        collect(Course, c, f"cursos[{i}]")
    for i, p in enumerate(data.get("profesores", [])):
        collect(Professor, p, f"profesores[{i}]")
    for i, s in enumerate(data.get("alumnos", [])):
        collect(Student, s, f"alumnos[{i}]")
    for i, ci in enumerate(data.get("instancias", [])):
        collect(CourseInstance, ci, f"instancias[{i}]")
    for i, sec in enumerate(data.get("secciones", [])):
        collect(Section, sec, f"secciones[{i}]")
    for i, asg in enumerate(data.get("alumnos_seccion", [])):
        collect(AlumnoSeccion, asg, f"alumnos_seccion[{i}]")
    for i, note in enumerate(data.get("notas", [])):
        collect(Nota, note, f"notas[{i}]")

    # Duplicate ID checks
    def check_duplicates(
        items: List[Dict[str, Any]],
        key: str,
        prefix: str,
    ) -> None:
        seen: Set[Any] = set()
        for item in items:
            val = item.get(key)
            if val in seen:
                issues.append(
                    ValidationIssue(
                        loc=f"{prefix}[id={val}]",
                        msg="id duplicado",
                        code="value_error.duplicate",
                    )
                )
            seen.add(val)

    check_duplicates(data.get("cursos", []), "id", "cursos")
    check_duplicates(data.get("profesores", []), "id", "profesores")
    check_duplicates(data.get("alumnos", []), "id", "alumnos")
    check_duplicates(data.get("instancias", []), "id", "instancias")
    check_duplicates(data.get("secciones", []), "id", "secciones")

    seen_pairs: Set[Tuple[int, int]] = set()
    for asg in data.get("alumnos_seccion", []):
        pair = (asg["alumno_id"], asg["seccion_id"])
        if pair in seen_pairs:
            issues.append(
                ValidationIssue(
                    loc=f"alumnos_seccion{pair}",
                    msg="inscripción duplicada",
                    code="value_error.duplicate",
                )
            )
        seen_pairs.add(pair)

    seen_notes: Set[Tuple[int, int, int]] = set()
    for note in data.get("notas", []):
        triple = (
            note["alumno_id"],
            note["evaluation_instance_id"],
            note["grade"],
        )
        if triple in seen_notes:
            issues.append(
                ValidationIssue(
                    loc=f"notas{triple}",
                    msg="nota duplicada",
                    code="value_error.duplicate",
                )
            )
        seen_notes.add(triple)

    curso_ids = {c["id"] for c in data.get("cursos", [])}
    profes_ids = {p["id"] for p in data.get("profesores", [])}
    alumnos_ids = {s["id"] for s in data.get("alumnos", [])}
    instancia_ids = {ci["id"] for ci in data.get("instancias", [])}
    seccion_ids = {sec["id"] for sec in data.get("secciones", [])}

    for ci in data.get("instancias", []):
        if ci["curso_id"] not in curso_ids:
            issues.append(
                ValidationIssue(
                    loc=f"instancias[id={ci['id']}].curso_id",
                    msg=f"curso_id {ci['curso_id']} no existe",
                    code="value_error",
                )
            )
    for sec in data.get("secciones", []):
        if sec["instancia_curso"] not in instancia_ids:
            issues.append(
                ValidationIssue(
                    loc=f"secciones[id={sec['id']}].instancia_curso",
                    msg=f"Instancia {sec['instancia_curso']} no existe",
                    code="value_error",
                )
            )
        if sec["profesor_id"] not in profes_ids:
            issues.append(
                ValidationIssue(
                    loc=f"secciones[id={sec['id']}].profesor_id",
                    msg=f"Profesor {sec['profesor_id']} no existe",
                    code="value_error",
                )
            )
        eval_data = sec.get("evaluacion", {})
        topicos = eval_data.get("combinacion_topicos", [])
        total_perc = sum(
            t.get("valor", 0)
            for t in topicos
            if eval_data.get("topicos", {}).get(str(t["id"]), {}).get("tipo")
            == "porcentaje"
        )
        if (
            any(
                eval_data.get("topicos", {}).get(str(t["id"]), {}).get("tipo")
                == "porcentaje"
                for t in topicos
            )
            and abs(total_perc - 100) > 1e-6
        ):
            issues.append(
                ValidationIssue(
                    loc=f"secciones[id={sec['id']}].evaluacion",
                    msg=f"Porcentaje total {total_perc}, debe sumar 100",
                    code="value_error",
                )
            )
    for asg in data.get("alumnos_seccion", []):
        if asg["alumno_id"] not in alumnos_ids:
            issues.append(
                ValidationIssue(
                    loc=f"alumnos_seccion alumno={asg['alumno_id']}",
                    msg=f"Alumno {asg['alumno_id']} no existe",
                    code="value_error",
                )
            )
        if asg["seccion_id"] not in seccion_ids:
            issues.append(
                ValidationIssue(
                    loc=f"alumnos_seccion seccion={asg['seccion_id']}",
                    msg=f"Sección {asg['seccion_id']} no existe",
                    code="value_error",
                )
            )

    eval_inst_ids = set()
    for sec in data.get("secciones", []):
        eval_data = sec["evaluacion"]
        for topic in eval_data["combinacion_topicos"]:
            t_id = topic["id"]
            tdata = eval_data["topicos"][str(t_id)]
            qty = tdata.get("cantidad", 0)
            if qty == 0:
                continue
            for idx in range(qty):
                eval_inst_ids.add(t_id * 100 + idx + 1)

    for note in data.get("notas", []):
        if note["alumno_id"] not in alumnos_ids:
            issues.append(
                ValidationIssue(
                    loc=f"notas alumno={note['alumno_id']}",
                    msg=f"Alumno {note['alumno_id']} no existe",
                    code="value_error",
                )
            )
        if note["evaluation_instance_id"] not in eval_inst_ids:
            issues.append(
                ValidationIssue(
                    loc=f"notas evaluation_instance={note['evaluation_instance_id']}",
                    msg=f"evaluation_instance_id {note['evaluation_instance_id']} no existe",
                    code="value_error",
                )
            )

    return issues

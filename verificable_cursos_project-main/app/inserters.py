from __future__ import annotations

import json
from datetime import date
from typing import Any, Dict, List, Tuple

import mysql.connector
from mysql.connector.cursor_cext import CMySQLCursor


def _safe_execute(
    cur: CMySQLCursor,
    query: str,
    params: Tuple[Any, ...],
) -> None:
    try:
        cur.execute(query, params)
    except mysql.connector.errors.IntegrityError:
        pass


def _semester_str(año: int, semestre: int) -> str:
    return f"{año}-{10 if semestre == 1 else 20}"


def insert_courses(cur: CMySQLCursor, cursos: List[Dict[str, Any]]) -> None:
    for c in cursos:
        _safe_execute(
            cur,
            "INSERT INTO course (id, code, description, requisites, credits) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                c["id"],
                c["codigo"],
                c["descripcion"],
                json.dumps(c["requisitos"]),
                c["creditos"],
            ),
        )


def insert_professors(
    cur: CMySQLCursor,
    profesores: List[Dict[str, Any]],
) -> None:
    for p in profesores:
        _safe_execute(
            cur,
            "INSERT INTO professor (id, name, email) VALUES (%s, %s, %s)",
            (p["id"], p["nombre"], p["correo"]),
        )


def insert_students(
    cur: CMySQLCursor,
    alumnos: List[Dict[str, Any]],
) -> None:
    for s in alumnos:
        _safe_execute(
            cur,
            "INSERT INTO student (id, name, email, enrollment_date) "
            "VALUES (%s, %s, %s, %s)",
            (s["id"], s["nombre"], s["correo"], date(s["anio_ingreso"], 1, 1)),
        )


def insert_course_instances(
    cur: CMySQLCursor,
    instancias: List[Dict[str, Any]],
) -> None:
    for ci in instancias:
        _safe_execute(
            cur,
            "INSERT INTO course_instance "
            "(id, course_id, semester, year, evaluation_scheme) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                ci["id"],
                ci["curso_id"],
                _semester_str(ci["año"], ci["semestre"]),
                ci["año"],
                "percentage",
            ),
        )


def _create_section(
    cur: CMySQLCursor,
    sec: Dict[str, Any],
) -> None:
    section_number = str(sec["id"]).zfill(4)
    _safe_execute(
        cur,
        "INSERT INTO section (id, course_instance_id, section_number) "
        "VALUES (%s, %s, %s)",
        (sec["id"], sec["instancia_curso"], section_number),
    )


def _assign_professor(
    cur: CMySQLCursor,
    sec: Dict[str, Any],
) -> None:
    """Crea la fila en professor_assignment (id == section_id)."""
    _safe_execute(
        cur,
        "INSERT INTO professor_assignment "
        "(id, professor_id, course_instance_id, section_id) "
        "VALUES (%s, %s, %s, %s)",
        (sec["id"], sec["profesor_id"], sec["instancia_curso"], sec["id"]),
    )


def _create_evaluation(
    cur: CMySQLCursor,
    topic: Dict[str, Any],
    sec: Dict[str, Any],
) -> int:
    """Inserta `evaluation` y devuelve el id (es el mismo del topic)."""
    topic_id = topic["id"]
    topic_data = sec["evaluacion"]["topicos"][str(topic_id)]
    is_percentage = topic_data["tipo"] == "porcentaje"
    weight_type = "percentage" if is_percentage else "weight"

    _safe_execute(
        cur,
        "INSERT INTO evaluation "
        "(id, course_instance_id, section_id, name, weight_type, weight) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (
            topic_id,
            sec["instancia_curso"],
            sec["id"],
            topic["nombre"],
            weight_type,
            topic["valor"],
        ),
    )
    return topic_id


def _create_evaluation_instance(
    cur: CMySQLCursor,
    topic: Dict[str, Any],
    topic_data: Dict[str, Any],
    idx: int,
) -> None:
    """Crea una fila en evaluation_instance."""
    is_percentage = topic_data["tipo"] == "porcentaje"
    weight_type = "percentage" if is_percentage else "weight"
    instance_id = topic["id"] * 100 + idx + 1
    _safe_execute(
        cur,
        "INSERT INTO evaluation_instance "
        "(id, evaluation_id, name, weight_type, weight, is_optional) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (
            instance_id,
            topic["id"],
            f"{topic['nombre']} #{idx+1}",
            weight_type,
            topic_data["valores"][idx],
            not topic_data["obligatorias"][idx],
        ),
    )


def insert_sections_and_evaluations(
    cur: CMySQLCursor,
    secciones: List[Dict[str, Any]],
) -> Dict[int, List[int]]:
    evals_by_section: Dict[int, List[int]] = {}

    for sec in secciones:
        _create_section(cur, sec)
        _assign_professor(cur, sec)

        eval_ids: List[int] = []
        eval_data = sec["evaluacion"]

        for topic in eval_data["combinacion_topicos"]:
            topic_id = _create_evaluation(cur, topic, sec)
            eval_ids.append(topic_id)

            tdata = eval_data["topicos"][str(topic_id)]
            if "cantidad" in tdata:
                for idx in range(tdata["cantidad"]):
                    _create_evaluation_instance(cur, topic, tdata, idx)

        evals_by_section[sec["id"]] = eval_ids

    return evals_by_section


def insert_student_assignments(
    cur: CMySQLCursor,
    alumnos_seccion: List[Dict[str, int]],
) -> None:
    for asg in alumnos_seccion:
        sec_id = asg["seccion_id"]
        student_id = asg["alumno_id"]
        inst_course_id = _course_instance_of_section(cur, sec_id)
        assignment_id = sec_id * 1000 + student_id
        _safe_execute(
            cur,
            """
            INSERT INTO student_assignment
            (id, student_id, course_instance_id, section_id)
            VALUES (%s, %s, %s, %s)
            """,
            (assignment_id, student_id, inst_course_id, sec_id),
        )


def insert_grades(cur: CMySQLCursor, notas: List[Dict[str, Any]]) -> None:
    for n in notas:
        _safe_execute(
            cur,
            """
            INSERT INTO grade
              (student_id, evaluation_instance_id, grade)
            VALUES (%s, %s, %s)
            """,
            (n["alumno_id"], n["evaluation_instance_id"], n["grade"]),
        )


def _course_instance_of_section(
    cur: CMySQLCursor,
    section_id: int,
) -> int | None:
    cur.execute(
        "SELECT course_instance_id FROM section WHERE id = %s",
        (section_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    if isinstance(row, dict):
        return row.get("course_instance_id")
    return row[0]


def insert_all(cur, data):
    insert_courses(cur, data["cursos"])
    insert_professors(cur, data["profesores"])
    insert_students(cur, data["alumnos"])
    insert_course_instances(cur, data["instancias"])
    insert_sections_and_evaluations(cur, data["secciones"])
    insert_student_assignments(cur, data["alumnos_seccion"])
    insert_grades(cur, data["notas"])

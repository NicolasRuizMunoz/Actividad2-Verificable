from functools import wraps

from flask import render_template, request
from pydantic import ValidationError

from services.courses_instances_manager import CourseInstanceManager
from services.courses_manager import CourseManager
from services.professor_manager import ProfessorManager
from services.section_manager import SectionManager
from services.student_manager import StudentManager

instance_mgr = CourseInstanceManager()
section_mgr = SectionManager()


def validate_with(schema, template, form_key="form", error_key="errors"):
    def translate_error(err):
        loc = err.get("loc") or []
        key = loc[0] if isinstance(loc, (list, tuple)) and loc else ""
        typ = err.get("type", "")
        raw = err.get("msg", "")
        labels = {
            "codigo": "Código",
            "descripcion": "Descripción",
            "requisitos": "Requisitos",
            "creditos": "Créditos",
            "nombre": "Nombre",
            "correo": "Correo",
            "anio_ingreso": "Fecha de Ingreso",
            "course_id": "Curso",
            "instance_id": "Instancia",
            "course_instance_id": "Instancia",
            "semester": "Semestre",
            "year": "Año",
            "evaluation_scheme": "Esquema de Evaluación",
            "section_id": "Sección",
            "section_number": "Número de sección",
            "name": "Nombre de evaluación",
            "weight_type": "Tipo de ponderación",
            "weight": "Peso",
            "is_optional": "Opcional",
            "evaluation_id": "Evaluación",
        }
        field = labels.get(key, key or "Error")
        if typ == "value_error.missing":
            return {"field": field, "msg": f"{field} es obligatorio."}
        if "pattern" in typ:
            return {"field": field, "msg": f"Formato de {field} inválido."}
        if "min_length" in typ:
            n = err.get("ctx", {}).get("limit_value")
            return {
                "field": field,
                "msg": f"{field} debe tener al menos {n} caracteres.",
            }
        if "max_length" in typ:
            n = err.get("ctx", {}).get("limit_value")
            return {
                "field": field,
                "msg": f"{field} debe tener como máximo {n} caracteres.",
            }
        if typ in ("type_error.integer", "value_error.any_int"):
            return {"field": field, "msg": f"{field} debe ser un número entero válido."}
        if typ == "value_error.number.not_ge":
            n = err.get("ctx", {}).get("limit_value")
            return {"field": field, "msg": f"{field} debe ser ≥ {n}."}
        if typ == "value_error.number.not_le":
            n = err.get("ctx", {}).get("limit_value")
            return {"field": field, "msg": f"{field} debe ser ≤ {n}."}
        return {"field": field, "msg": raw}

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if request.method != "POST":
                return fn(*args, **kwargs)

            raw = {
                k: v if len(v) > 1 else v[0]
                for k, v in request.form.to_dict(flat=False).items()
            }
            payload = {
                k: (v.strip() if isinstance(v, str) else v) for k, v in raw.items()
            }

            if "instance_ev_id" in kwargs:
                payload["id"] = kwargs["instance_ev_id"]
            elif "evaluation_id" in kwargs:
                payload["id"] = kwargs["evaluation_id"]
            elif "section_id" in kwargs:
                payload["id"] = kwargs["section_id"]
            elif "instance_id" in kwargs:
                payload["id"] = kwargs["instance_id"]
            elif "course_id" in kwargs:
                payload["id"] = kwargs["course_id"]
            elif "professor_id" in kwargs:
                payload["id"] = kwargs["professor_id"]
            elif "student_id" in kwargs:
                payload["id"] = kwargs["student_id"]

            if "course_id" in kwargs:
                payload["course_id"] = kwargs["course_id"]
            if "instance_id" in kwargs:
                payload["course_instance_id"] = kwargs["instance_id"]
            if "section_id" in kwargs:
                payload["section_id"] = kwargs["section_id"]
            if "professor_id" in kwargs:
                payload["professor_id"] = kwargs["professor_id"]
            if "student_id" in kwargs:
                payload["student_id"] = kwargs["student_id"]

            try:
                validated = schema(**payload)
            except ValidationError as ve:
                errs = [translate_error(e) for e in ve.errors()]
                ctx = {form_key: payload, error_key: errs}
                if "course_id" in kwargs:
                    ctx["course"] = CourseManager().get_course_by_id(
                        kwargs["course_id"]
                    )
                if "instance_id" in kwargs:
                    ci = CourseInstanceManager().get_course_instance_by_id(
                        kwargs["instance_id"]
                    )
                    ctx["instance"] = ci
                    ctx["course_instance"] = ci
                if "section_id" in kwargs:
                    ctx["section"] = section_mgr.get_section_by_id(kwargs["section_id"])
                    ctx["section_id"] = kwargs["section_id"]
                if "professor_id" in kwargs:
                    ctx["professor"] = ProfessorManager().get_professor_by_id(
                        kwargs["professor_id"]
                    )
                if "student_id" in kwargs:
                    ctx["student"] = StudentManager().get_student_by_id(
                        kwargs["student_id"]
                    )
                if "evaluation_id" in kwargs:
                    from services.evaluations_manager import EvaluationManager

                    ctx["evaluation"] = EvaluationManager().get_evaluation_by_id(
                        kwargs["evaluation_id"]
                    )
                return render_template(template, **ctx), 400

            return fn(validated=validated, *args, **kwargs)

        return wrapper

    return decorator
